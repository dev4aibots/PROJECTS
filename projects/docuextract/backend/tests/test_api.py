from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
from reportlab.pdfgen.canvas import Canvas

import app.main as main


def pdf_bytes(pages=1):
    output = BytesIO()
    canvas = Canvas(output)
    for page in range(pages):
        canvas.drawString(40, 700, f"Invoice page {page + 1}")
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def png_bytes():
    output = BytesIO()
    Image.new("RGB", (8, 8), "white").save(output, "PNG")
    return output.getvalue()


client = TestClient(main.app)
PDF = pdf_bytes()
PNG = png_bytes()
A = "00000000-0000-0000-0000-000000000001"
B = "00000000-0000-0000-0000-000000000002"


def headers(user=A):
    return {"X-Demo-User-Id": user}


def setup_function():
    main.repo.reset()
    if hasattr(main.storage, "reset"):
        main.storage.reset()


def upload(name="clean_invoice.pdf", data=PDF, ct="application/pdf", user=A):
    return client.post(
        "/api/documents/upload",
        headers=headers(user),
        files={"file": (name, data, ct)},
    )


def test_health_and_private_response_headers():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_clean_end_to_end():
    uploaded = upload()
    assert uploaded.status_code == 200
    result = client.post(
        f"/api/documents/{uploaded.json()['id']}/process", headers=headers()
    )
    assert result.json()["status"] == "verified"
    assert result.json()["verification"]["status"] == "VERIFIED"
    assert "owner_id" not in result.json()
    assert "storage_path" not in result.json()
    assert "data" not in result.json()
    repeated = client.post(
        f"/api/documents/{uploaded.json()['id']}/process", headers=headers()
    )
    assert repeated.status_code == 200
    assert repeated.json()["status"] == "verified"
    assert repeated.json()["invoice"]["invoice_number"] == "INV-2026-0042"


def test_broken_total_is_not_corrected():
    uploaded = upload("broken_total_invoice.pdf")
    result = client.post(
        f"/api/documents/{uploaded.json()['id']}/process", headers=headers()
    ).json()
    assert result["status"] == "verification_failed"
    assert result["invoice"]["total"] == "12800"
    assert any(not check["passed"] for check in result["verification"]["checks"])


def test_non_invoice_creates_no_invoice():
    uploaded = upload("cat.png", PNG, "image/png")
    result = client.post(
        f"/api/documents/{uploaded.json()['id']}/process", headers=headers()
    ).json()
    assert result["status"] == "failed_extraction"
    assert "invoice" not in result


def test_wrong_type_magic_and_oversize_are_blocked():
    assert upload("x.txt", b"hi", "text/plain").status_code == 400
    assert upload(data=b"not pdf").status_code == 400
    assert upload(data=b"%PDF" + b"x" * (8 * 1024 * 1024)).status_code == 400


def test_duplicate_flag_and_history_delete_are_owner_scoped():
    first = upload().json()
    client.post(f"/api/documents/{first['id']}/process", headers=headers())
    second = upload().json()
    result = client.post(
        f"/api/documents/{second['id']}/process", headers=headers()
    ).json()
    assert result["possible_duplicate"]
    assert len(client.get("/api/documents", headers=headers()).json()["documents"]) == 2
    assert client.get("/api/documents", headers=headers(B)).json()["documents"] == []
    assert client.delete(
        f"/api/documents/{second['id']}", headers=headers(B)
    ).status_code == 404
    assert client.delete(
        f"/api/documents/{second['id']}", headers=headers()
    ).json()["deleted"]


def test_cross_owner_detail_and_process_are_hidden():
    uploaded = upload(user=A).json()
    path = f"/api/documents/{uploaded['id']}"
    assert client.get(path, headers=headers(B)).status_code == 404
    assert client.post(path + "/process", headers=headers(B)).status_code == 404
    assert client.get(path, headers=headers(A)).status_code == 200


def test_invalid_local_identity_is_rejected():
    response = client.get("/api/documents", headers={"X-Demo-User-Id": "invalid"})
    assert response.status_code == 400
