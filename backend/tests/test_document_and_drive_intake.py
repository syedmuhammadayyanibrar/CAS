import pytest
import io
import zipfile
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.core.document_parser import DocumentParser


@pytest.mark.asyncio
async def test_document_parser_docx_and_text():
    # 1. Test DOCX standard openxml extraction
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>MASTER SERVICES AGREEMENT</w:t></w:r></w:p>
    <w:p><w:r><w:t>This Agreement is between Acme Corp ("Customer") and NovaCloud Inc ("Vendor").</w:t></w:r></w:p>
  </w:body>
</w:document>"""
        z.writestr("word/document.xml", xml)

    res = DocumentParser.extract_text_from_bytes("msa.docx", buf.getvalue())
    assert res["file_type"] == "docx"
    assert "MASTER SERVICES AGREEMENT" in res["content"]
    assert res["word_count"] > 5

    # 2. Test plain text extraction
    txt_bytes = b"CONFIDENTIALITY AGREEMENT\nBetween Alpha Inc and Beta LLC."
    res_txt = DocumentParser.extract_text_from_bytes("nda.txt", txt_bytes)
    assert res_txt["file_type"] == "text"
    assert "CONFIDENTIALITY AGREEMENT" in res_txt["content"]


@pytest.mark.asyncio
async def test_google_drive_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. List files
        r_files = await ac.get("/automations/google-drive/files")
        assert r_files.status_code == 200
        data_files = r_files.json()
        assert len(data_files) >= 4
        assert any("NovaCloud" in f["name"] for f in data_files)

        # 2. Import a file via Fastn workflow
        r_import = await ac.post(
            "/automations/google-drive/import",
            json={"document_id": "gdrive_novacloud_saas_2026", "auto_create_contract": False}
        )
        assert r_import.status_code == 200
        data_import = r_import.json()
        assert data_import["success"] is True
        assert data_import["fastn_workflow"] == "cas-contract-intake"
        assert "MASTER SAAS SERVICES AGREEMENT" in data_import["content"]
        assert data_import["word_count"] > 100


@pytest.mark.asyncio
async def test_upload_document_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("vendor_agreement.txt", b"VENDOR TERMS AND CONDITIONS\nPayment is due in 30 days.", "text/plain")}
        res = await ac.post("/contracts/upload-document", files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["filename"] == "vendor_agreement.txt"
        assert "VENDOR TERMS" in data["content"]
        assert data["word_count"] > 5
