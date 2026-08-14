"""Zero-trust SQL validator: SQLGlot AST checks, allowlists, and LIMIT rewriting.

The LLM (or any caller) is treated as a hostile SQL generator. Nothing reaches
the database unless every check below passes. All checks are AST-based —
no regex-only decisions — so comment obfuscation and casing tricks do not help.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp
from sqlglot.errors import OptimizeError
from sqlglot.optimizer.qualify import qualify

from .allowlist import ALLOWED_TABLES, ALLOWED_FUNCTIONS, MAX_ROWS

CHECK_ORDER = [
    "parse", "single_statement", "statement_type", "table_allowlist",
    "column_allowlist", "function_allowlist", "row_limit",
]

FORBIDDEN_STATEMENTS = (
    exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Create,
    exp.TruncateTable, exp.Grant, exp.Revoke, exp.Copy, exp.Merge, exp.Set,
    exp.Command, exp.Use,
)


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


@dataclass
class ValidationResult:
    allowed: bool = True
    final_sql: str | None = None
    limit_injected: bool = False
    rejection_reason: str | None = None
    checks: list[Check] = field(default_factory=list)

    def to_payload(self) -> dict:
        return {
            "allowed": self.allowed,
            "checks": [c.__dict__ for c in self.checks],
            "rejection_reason": self.rejection_reason,
            "limit_injected": self.limit_injected,
        }


def _fail(result: ValidationResult, name: str, detail: str) -> ValidationResult:
    result.checks.append(Check(name, False, detail))
    result.allowed = False
    result.rejection_reason = f"{name}: {detail}"
    # Remaining checks are reported as skipped-fail-closed for transparency.
    idx = CHECK_ORDER.index(name)
    for later in CHECK_ORDER[idx + 1:]:
        result.checks.append(Check(later, False, "not evaluated — earlier check failed"))
    return result


def _passed(result: ValidationResult, name: str, detail: str) -> None:
    result.checks.append(Check(name, True, detail))


def _schema() -> dict[str, dict[str, str]]:
    """Return SQLGlot's schema shape without exposing runtime data or types."""
    return {
        table: {column: "UNKNOWN" for column in metadata["columns"]}
        for table, metadata in ALLOWED_TABLES.items()
    }


def _validate_column_lineage(tree: exp.Expression) -> str | None:
    """Resolve columns through tables, aliases, subqueries, and CTE scopes.

    A global column-name set is unsafe: ``customers.unit_price`` used to pass
    merely because ``unit_price`` exists on another table. SQLGlot's qualifier
    performs scope-aware provenance against the exact allowlisted schema and
    also rejects ambiguous unqualified columns.
    """
    try:
        qualify(
            tree.copy(),
            dialect="postgres",
            schema=_schema(),
            validate_qualify_columns=True,
            identify=False,
            quote_identifiers=False,
        )
    except OptimizeError as err:
        # Optimizer messages contain SQL identifiers only, but cap their size so
        # hostile generated SQL cannot create an oversized response or log row.
        return str(err)[:300]
    return None


def validate(sql: str) -> ValidationResult:
    """Run the full check pipeline over one SQL string."""
    result = ValidationResult()

    # 1. parse
    try:
        statements = sqlglot.parse(sql, dialect="postgres")
    except sqlglot.errors.ParseError as err:
        return _fail(result, "parse", f"unparseable SQL: {err}"[:300])
    statements = [s for s in statements if s is not None]
    if not statements:
        return _fail(result, "parse", "no SQL statement found")
    _passed(result, "parse", "SQL parsed with sqlglot dialect=postgres")

    # 2. exactly one statement
    if len(statements) != 1:
        return _fail(result, "single_statement",
                     f"{len(statements)} statements found; exactly 1 required")
    tree = statements[0]
    _passed(result, "single_statement", "exactly one statement")

    # 3. statement type: SELECT only, and no forbidden node anywhere in the AST
    if not isinstance(tree, (exp.Select, exp.Union)):
        return _fail(result, "statement_type",
                     f"top-level statement is {type(tree).__name__}, only SELECT allowed")
    for node in tree.walk():
        if isinstance(node, FORBIDDEN_STATEMENTS):
            return _fail(result, "statement_type",
                         f"forbidden {type(node).__name__} node inside the statement")
        if isinstance(node, exp.Into):
            return _fail(result, "statement_type", "SELECT ... INTO is not allowed")
    _passed(result, "statement_type", "read-only SELECT confirmed across the whole AST")

    # 4. table allowlist — every table in every scope (CTEs, subqueries, joins)
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    table_nodes = list(tree.find_all(exp.Table))
    tables = {t.name.lower() for t in table_nodes}
    unknown_tables = sorted(t for t in tables
                            if t not in ALLOWED_TABLES and t not in cte_names)
    unsafe_namespaces = sorted({
        t.sql(dialect="postgres") for t in table_nodes
        if t.name.lower() not in cte_names
        and (t.catalog or (t.db and t.db.lower() != "public"))
    })
    if unknown_tables:
        return _fail(result, "table_allowlist",
                     f"table(s) not in allowlist: {', '.join(unknown_tables)}")
    if unsafe_namespaces:
        return _fail(result, "table_allowlist",
                     "table namespace not allowed: " + ", ".join(unsafe_namespaces))
    _passed(result, "table_allowlist",
            f"tables referenced: {', '.join(sorted(tables)) or 'none'}")

    # 5. column allowlist — every reference must resolve in its own scope.
    lineage_error = _validate_column_lineage(tree)
    if lineage_error:
        return _fail(result, "column_allowlist",
                     f"column lineage could not be resolved: {lineage_error}")
    _passed(result, "column_allowlist",
            "all columns resolve through allowlisted table, alias, CTE, and subquery scopes")

    # 6. function allowlist — strict: any function whose canonical name is
    # outside the modest allowlist is rejected (fail closed).
    bad_funcs = sorted({
        _func_name(node) for node in tree.find_all(exp.Func)
        if _func_name(node) not in ALLOWED_FUNCTIONS
    })
    if bad_funcs:
        return _fail(result, "function_allowlist",
                     f"function(s) not allowed: {', '.join(bad_funcs)}")
    _passed(result, "function_allowlist", "all functions inside the modest allowlist")

    # 7. LIMIT enforcement by AST transformation
    injected = False
    limit_node = tree.args.get("limit")
    if limit_node is None:
        tree = tree.limit(MAX_ROWS)
        injected = True
        detail = f"no LIMIT present — LIMIT {MAX_ROWS} injected by AST rewrite"
    else:
        try:
            current = int(limit_node.expression.this)
        except (TypeError, ValueError, AttributeError):
            current = MAX_ROWS + 1
        if current > MAX_ROWS:
            tree.set("limit", exp.Limit(expression=exp.Literal.number(MAX_ROWS)))
            injected = True
            detail = f"LIMIT {current} exceeds {MAX_ROWS} — rewritten to {MAX_ROWS}"
        else:
            detail = f"LIMIT {current} within the {MAX_ROWS} cap"
    _passed(result, "row_limit", detail)
    result.limit_injected = injected
    result.final_sql = tree.sql(dialect="postgres")
    return result


def _func_name(node: exp.Func) -> str:
    if isinstance(node, exp.Anonymous):
        return (node.name or "").lower()
    return node.sql_name().lower()
