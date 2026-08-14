"""Unit tests for the AST validator — the heart of the zero-trust pipeline."""
from app.validator import CHECK_ORDER, validate


def failed_check(result):
    return next(c.name for c in result.checks if not c.passed)


def test_simple_select_allowed():
    r = validate("SELECT name, country FROM customers LIMIT 10")
    assert r.allowed and not r.limit_injected
    assert r.final_sql.upper().startswith("SELECT")


def test_unparseable_rejected():
    r = validate("SELEKT gibberish FROMM nowhere")
    assert not r.allowed and failed_check(r) == "parse"


def test_multi_statement_rejected():
    r = validate("SELECT name FROM customers; DROP TABLE orders;")
    assert not r.allowed and failed_check(r) == "single_statement"


def test_update_rejected():
    r = validate("UPDATE customers SET segment = 'vip'")
    assert not r.allowed and failed_check(r) == "statement_type"


def test_delete_rejected():
    r = validate("DELETE FROM customers")
    assert not r.allowed and failed_check(r) == "statement_type"


def test_drop_rejected():
    r = validate("DROP TABLE orders")
    assert not r.allowed and failed_check(r) == "statement_type"


def test_insert_rejected():
    r = validate("INSERT INTO customers (id, name) VALUES (1, 'x')")
    assert not r.allowed and failed_check(r) == "statement_type"


def test_truncate_grant_rejected():
    assert not validate("TRUNCATE TABLE orders").allowed
    assert not validate("GRANT ALL ON customers TO evil").allowed


def test_select_into_rejected():
    r = validate("SELECT id INTO stolen FROM customers")
    assert not r.allowed


def test_decoy_table_rejected():
    r = validate("SELECT * FROM internal_credentials")
    assert not r.allowed and failed_check(r) == "table_allowlist"
    assert "internal_credentials" in r.rejection_reason


def test_pg_shadow_rejected():
    r = validate("SELECT * FROM pg_shadow")
    assert not r.allowed and failed_check(r) == "table_allowlist"


def test_subquery_decoy_rejected():
    r = validate("SELECT name FROM customers WHERE id IN "
                 "(SELECT id FROM internal_credentials)")
    assert not r.allowed and failed_check(r) == "table_allowlist"


def test_cte_decoy_rejected():
    r = validate("WITH x AS (SELECT secret FROM internal_credentials) "
                 "SELECT * FROM x")
    assert not r.allowed and failed_check(r) == "table_allowlist"


def test_join_decoy_rejected():
    r = validate("SELECT c.name FROM customers c "
                 "JOIN internal_credentials i ON i.id = c.id")
    assert not r.allowed and failed_check(r) == "table_allowlist"


def test_legit_cte_allowed():
    r = validate(
        "WITH rev AS (SELECT order_id, SUM(quantity * unit_price) AS total "
        "FROM order_items GROUP BY order_id) "
        "SELECT o.status, SUM(rev.total) AS revenue FROM orders o "
        "JOIN rev ON rev.order_id = o.id GROUP BY o.status LIMIT 20")
    assert r.allowed, r.rejection_reason


def test_unknown_column_rejected():
    r = validate("SELECT password FROM customers LIMIT 5")
    assert not r.allowed and failed_check(r) == "column_allowlist"


def test_column_must_belong_to_its_qualified_table():
    r = validate("SELECT c.unit_price FROM customers AS c LIMIT 5")
    assert not r.allowed and failed_check(r) == "column_allowlist"


def test_ambiguous_unqualified_join_column_rejected():
    r = validate(
        "SELECT id FROM customers AS c "
        "JOIN orders AS o ON o.customer_id = c.id LIMIT 5"
    )
    assert not r.allowed and failed_check(r) == "column_allowlist"


def test_subquery_output_lineage_enforced():
    r = validate(
        "SELECT summary.email FROM "
        "(SELECT id, name FROM customers) AS summary LIMIT 5"
    )
    assert not r.allowed and failed_check(r) == "column_allowlist"


def test_cte_output_lineage_stays_allowed():
    r = validate(
        "WITH recent AS (SELECT customer_id FROM orders LIMIT 10) "
        "SELECT c.name FROM customers AS c "
        "JOIN recent AS r ON r.customer_id = c.id LIMIT 10"
    )
    assert r.allowed, r.rejection_reason


def test_non_public_schema_qualification_rejected():
    r = validate("SELECT name FROM private.customers LIMIT 5")
    assert not r.allowed and failed_check(r) == "table_allowlist"


def test_public_schema_qualification_allowed():
    r = validate("SELECT name FROM public.customers LIMIT 5")
    assert r.allowed, r.rejection_reason


def test_pg_sleep_rejected():
    r = validate("SELECT pg_sleep(60)")
    assert not r.allowed and failed_check(r) == "function_allowlist"


def test_pg_read_file_rejected():
    r = validate("SELECT pg_read_file('/etc/passwd')")
    assert not r.allowed and failed_check(r) == "function_allowlist"


def test_dblink_rejected():
    r = validate("SELECT dblink('host=evil', 'SELECT 1')")
    assert not r.allowed and failed_check(r) == "function_allowlist"


def test_limit_injected_when_absent():
    r = validate("SELECT name FROM customers")
    assert r.allowed and r.limit_injected
    assert "LIMIT 100" in r.final_sql


def test_limit_rewritten_when_excessive():
    r = validate("SELECT id FROM order_items LIMIT 1000000")
    assert r.allowed and r.limit_injected
    assert "LIMIT 100" in r.final_sql and "1000000" not in r.final_sql


def test_limit_kept_when_reasonable():
    r = validate("SELECT name FROM customers LIMIT 25")
    assert r.allowed and not r.limit_injected
    assert "LIMIT 25" in r.final_sql


def test_comment_obfuscated_attack_rejected():
    r = validate("SELECT name FROM customers /* harmless */ ; "
                 "DELETE /* still harmless */ FROM orders")
    assert not r.allowed


def test_all_checks_reported_even_when_blocked():
    r = validate("DROP TABLE orders")
    assert [c.name for c in r.checks] == CHECK_ORDER


def test_all_checks_reported_when_allowed():
    r = validate("SELECT name FROM customers LIMIT 10")
    assert [c.name for c in r.checks] == CHECK_ORDER
    assert all(c.passed for c in r.checks)
