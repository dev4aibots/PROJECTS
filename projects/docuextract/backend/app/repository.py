"""Owner-scoped document repositories for local and live deployments."""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from copy import deepcopy
from threading import Lock
from typing import Any, Protocol
from uuid import UUID, uuid4


class DocumentRepository(Protocol):
    mode: str

    def open(self) -> None: ...
    def close(self) -> None: ...
    def readiness(self) -> dict[str, str | bool]: ...
    def create(
        self,
        filename: str,
        content_type: str,
        file_size: int,
        owner_id: UUID,
        storage_path: str,
        document_id: str | None = None,
    ) -> dict: ...
    def get(self, document_id: str, owner_id: UUID) -> dict | None: ...
    def claim_processing(self, document_id: str, owner_id: UUID) -> str: ...
    def update(self, document_id: str, owner_id: UUID, **values: Any) -> dict | None: ...
    def list(self, owner_id: UUID) -> list[dict]: ...
    def invoice_number_exists(
        self, invoice_number: str, owner_id: UUID, excluding_document_id: str
    ) -> bool: ...
    def delete(self, document_id: str, owner_id: UUID) -> bool: ...


class Repository:
    """Deterministic memory repository with the live concurrency contract."""

    mode = "memory"

    def __init__(self) -> None:
        self.docs: dict[str, dict] = {}
        self.lock = Lock()

    def open(self) -> None:
        return None

    def close(self) -> None:
        return None

    def readiness(self) -> dict[str, str | bool]:
        return {"ready": True, "repository": self.mode}

    def reset(self) -> None:
        with self.lock:
            self.docs.clear()

    def create(
        self,
        filename: str,
        content_type: str,
        file_size: int,
        owner_id: UUID,
        storage_path: str,
        document_id: str | None = None,
    ) -> dict:
        document_id = document_id or str(uuid4())
        value = {
            "id": document_id,
            "owner_id": str(owner_id),
            "filename": filename,
            "content_type": content_type,
            "file_size": file_size,
            "storage_path": storage_path,
            "status": "uploaded",
            "error": None,
            "processing_version": 0,
        }
        with self.lock:
            self.docs[document_id] = value
        return deepcopy(value)

    def get(self, document_id: str, owner_id: UUID) -> dict | None:
        with self.lock:
            value = self.docs.get(document_id)
            if not value or value["owner_id"] != str(owner_id):
                return None
            return deepcopy(value)

    def claim_processing(self, document_id: str, owner_id: UUID) -> str:
        with self.lock:
            value = self.docs.get(document_id)
            if not value or value["owner_id"] != str(owner_id):
                return "missing"
            if value["status"] == "processing":
                return "busy"
            if value["status"] in {"verified", "verification_failed"}:
                return "complete"
            value.update(
                status="processing",
                error=None,
                processing_version=value.get("processing_version", 0) + 1,
            )
            return "claimed"

    def update(self, document_id: str, owner_id: UUID, **values: Any) -> dict | None:
        with self.lock:
            current = self.docs.get(document_id)
            if not current or current["owner_id"] != str(owner_id):
                return None
            current.update(values)
            return deepcopy(current)

    def list(self, owner_id: UUID) -> list[dict]:
        with self.lock:
            values = list(reversed(self.docs.values()))
            return [
                self.public(value)
                for value in values
                if value["owner_id"] == str(owner_id)
            ]

    def invoice_number_exists(
        self,
        invoice_number: str,
        owner_id: UUID,
        excluding_document_id: str,
    ) -> bool:
        with self.lock:
            return any(
                value.get("invoice", {}).get("invoice_number") == invoice_number
                and value["owner_id"] == str(owner_id)
                and value["id"] != excluding_document_id
                for value in self.docs.values()
            )

    def delete(self, document_id: str, owner_id: UUID) -> bool:
        with self.lock:
            current = self.docs.get(document_id)
            if not current or current["owner_id"] != str(owner_id):
                return False
            del self.docs[document_id]
            return True

    @staticmethod
    def public(document: dict) -> dict:
        return public_document(document)


class PostgresRepository:
    """Durable repository using transaction-local identity and forced RLS."""

    mode = "postgres"

    def __init__(self, database_url: str, pool: Any | None = None) -> None:
        if not database_url:
            raise RuntimeError("DATABASE_URL is required when APP_MODE=live")
        self.database_url = database_url
        self.pool = pool
        self._owns_pool = pool is None

    def open(self) -> None:
        if self.pool is not None:
            return
        from psycopg_pool import ConnectionPool

        self.pool = ConnectionPool(
            conninfo=self.database_url,
            min_size=0,
            max_size=int(os.getenv("DATABASE_POOL_MAX_SIZE", "5")),
            timeout=float(os.getenv("DATABASE_POOL_TIMEOUT_SECONDS", "5")),
            open=True,
        )

    def close(self) -> None:
        if self._owns_pool and self.pool is not None:
            self.pool.close()
            self.pool = None

    @contextmanager
    def _session(self, owner_id: UUID):
        if self.pool is None:
            raise RuntimeError("Postgres repository pool is not open")
        with self.pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
            cur.execute("SET LOCAL ROLE docuextract_api")
            cur.execute(
                "SELECT set_config('app.current_user_id', %s, true)",
                (str(owner_id),),
            )
            yield cur

    def readiness(self) -> dict[str, str | bool]:
        if self.pool is None:
            return {"ready": False, "repository": self.mode}
        try:
            with self.pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """SELECT pg_has_role(current_user, 'docuextract_api', 'member'),
                              has_table_privilege('docuextract_api', 'documents', 'SELECT')"""
                )
                role_member, table_access = cur.fetchone()
            return {
                "ready": bool(role_member and table_access),
                "repository": self.mode,
            }
        except Exception:
            return {"ready": False, "repository": self.mode}

    @staticmethod
    def _row(row: tuple[Any, ...]) -> dict:
        result = row[8] if isinstance(row[8], dict) else json.loads(row[8] or "{}")
        return {
            "id": str(row[0]),
            "owner_id": str(row[1]),
            "filename": row[2],
            "content_type": row[3],
            "file_size": row[4],
            "storage_path": row[5],
            "status": row[6],
            "error": row[7],
            "processing_version": row[9],
            **result,
        }

    _SELECT = """SELECT id,owner_id,filename,content_type,file_size,storage_path,
        status,error,result,processing_version FROM documents"""

    def create(
        self,
        filename: str,
        content_type: str,
        file_size: int,
        owner_id: UUID,
        storage_path: str,
        document_id: str | None = None,
    ) -> dict:
        document_id = document_id or str(uuid4())
        with self._session(owner_id) as cur:
            cur.execute(
                """INSERT INTO documents
                   (id,owner_id,filename,content_type,file_size,storage_path,status)
                   VALUES(%s,%s,%s,%s,%s,%s,'uploaded')
                   RETURNING id,owner_id,filename,content_type,file_size,storage_path,
                     status,error,result,processing_version""",
                (
                    document_id,
                    owner_id,
                    filename,
                    content_type,
                    file_size,
                    storage_path,
                ),
            )
            return self._row(cur.fetchone())

    def get(self, document_id: str, owner_id: UUID) -> dict | None:
        with self._session(owner_id) as cur:
            cur.execute(self._SELECT + " WHERE id=%s", (document_id,))
            row = cur.fetchone()
            return self._row(row) if row else None

    def claim_processing(self, document_id: str, owner_id: UUID) -> str:
        with self._session(owner_id) as cur:
            cur.execute(
                """UPDATE documents SET status='processing',error=NULL,
                     processing_version=processing_version+1,updated_at=now()
                   WHERE id=%s AND status IN ('uploaded','failed_extraction')
                   RETURNING id""",
                (document_id,),
            )
            if cur.fetchone():
                return "claimed"
            cur.execute("SELECT status FROM documents WHERE id=%s", (document_id,))
            row = cur.fetchone()
            if not row:
                return "missing"
            if row[0] == "processing":
                return "busy"
            if row[0] in {"verified", "verification_failed"}:
                return "complete"
            return "busy"

    def update(self, document_id: str, owner_id: UUID, **values: Any) -> dict | None:
        allowed_columns = {"status", "error", "provider_model", "schema_version"}
        columns = {key: value for key, value in values.items() if key in allowed_columns}
        result = {key: value for key, value in values.items() if key not in allowed_columns}
        assignments = [f"{name}=%s" for name in columns]
        params = list(columns.values())
        if result:
            assignments.append("result=result || %s::jsonb")
            params.append(json.dumps(result, default=str))
        assignments.append("updated_at=now()")
        params.append(document_id)
        with self._session(owner_id) as cur:
            cur.execute(
                f"UPDATE documents SET {','.join(assignments)} WHERE id=%s "
                "RETURNING id,owner_id,filename,content_type,file_size,storage_path,"
                "status,error,result,processing_version",
                tuple(params),
            )
            row = cur.fetchone()
            if not row:
                return None
            if "invoice" in values and "verification" in values:
                self._replace_invoice(cur, document_id, values)
            return self._row(row)

    @staticmethod
    def _replace_invoice(cur: Any, document_id: str, values: dict[str, Any]) -> None:
        invoice = values["invoice"]
        verification = values["verification"]
        invoice_id = str(uuid4())
        cur.execute("DELETE FROM invoices WHERE document_id=%s", (document_id,))
        cur.execute(
            """INSERT INTO invoices
               (id,document_id,invoice_number,vendor_name,invoice_date,currency,
                subtotal,tax,total,raw_extraction)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""",
            (
                invoice_id,
                document_id,
                invoice["invoice_number"],
                invoice["vendor_name"],
                invoice["invoice_date"],
                invoice["currency"],
                invoice["subtotal"],
                invoice.get("tax"),
                invoice["total"],
                json.dumps(values.get("raw_extraction", invoice), default=str),
            ),
        )
        for position, item in enumerate(invoice["line_items"]):
            cur.execute(
                """INSERT INTO invoice_items
                   (id,invoice_id,position,description,quantity,unit_price,line_total)
                   VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                (
                    str(uuid4()),
                    invoice_id,
                    position,
                    item["description"],
                    item["quantity"],
                    item["unit_price"],
                    item["line_total"],
                ),
            )
        cur.execute(
            """INSERT INTO verification_results
               (id,invoice_id,status,checks,tolerance)
               VALUES(%s,%s,%s,%s::jsonb,%s)""",
            (
                str(uuid4()),
                invoice_id,
                verification["status"],
                json.dumps(verification["checks"], default=str),
                verification["tolerance"],
            ),
        )

    def list(self, owner_id: UUID) -> list[dict]:
        with self._session(owner_id) as cur:
            cur.execute(self._SELECT + " ORDER BY created_at DESC")
            return [public_document(self._row(row)) for row in cur.fetchall()]

    def invoice_number_exists(
        self,
        invoice_number: str,
        owner_id: UUID,
        excluding_document_id: str,
    ) -> bool:
        with self._session(owner_id) as cur:
            cur.execute(
                """SELECT EXISTS(
                     SELECT 1 FROM invoices i JOIN documents d ON d.id=i.document_id
                     WHERE i.invoice_number=%s AND d.id<>%s
                   )""",
                (invoice_number, excluding_document_id),
            )
            return bool(cur.fetchone()[0])

    def delete(self, document_id: str, owner_id: UUID) -> bool:
        with self._session(owner_id) as cur:
            cur.execute("DELETE FROM documents WHERE id=%s RETURNING id", (document_id,))
            return cur.fetchone() is not None

    @staticmethod
    def public(document: dict) -> dict:
        return public_document(document)


def public_document(document: dict) -> dict:
    return {
        key: value
        for key, value in deepcopy(document).items()
        if key not in {"owner_id", "storage_path", "processing_version"}
    }


def build_repository(mode: str | None = None) -> DocumentRepository:
    selected = (mode or os.getenv("APP_MODE", "local")).strip().lower()
    if selected == "local":
        return Repository()
    if selected == "live":
        repository = PostgresRepository(os.getenv("DATABASE_URL", ""))
        repository.open()
        return repository
    raise RuntimeError("APP_MODE must be local or live")
