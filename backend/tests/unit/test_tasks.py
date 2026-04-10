import pytest

from src.models import Alert, StoredFile
from src.tasks import _extract_file_metadata, _scan_file_for_threats, _send_file_alert


class TestScanFileForThreats:
    """V-M-TASKS / scenario-1,2: scan detects suspicious extensions and marks clean files."""

    async def test_suspicious_extension_detected(self, session, make_stored_file):
        file = make_stored_file(
            file_id="scan-sus-1",
            original_name="malware.exe",
            processing_status="uploaded",
        )
        session.add(file)
        await session.flush()

        await _scan_file_for_threats(session, "scan-sus-1")
        await session.refresh(file)

        assert file.scan_status == "suspicious"
        assert "suspicious extension .exe" in file.scan_details
        assert file.requires_attention is True

    async def test_clean_file(self, session, make_stored_file):
        file = make_stored_file(
            file_id="scan-clean-1",
            original_name="document.pdf",
            mime_type="application/pdf",
            size=1000,
            processing_status="uploaded",
        )
        session.add(file)
        await session.flush()

        await _scan_file_for_threats(session, "scan-clean-1")
        await session.refresh(file)

        assert file.scan_status == "clean"
        assert file.requires_attention is False

    async def test_large_file_flagged(self, session, make_stored_file):
        file = make_stored_file(
            file_id="scan-large-1",
            original_name="huge.zip",
            size=11 * 1024 * 1024,  # 11 MB
            processing_status="uploaded",
        )
        session.add(file)
        await session.flush()

        await _scan_file_for_threats(session, "scan-large-1")
        await session.refresh(file)

        assert file.scan_status == "suspicious"
        assert "larger than 10 MB" in file.scan_details

    async def test_pdf_mime_mismatch(self, session, make_stored_file):
        file = make_stored_file(
            file_id="scan-mime-1",
            original_name="fake.pdf",
            mime_type="text/plain",
            processing_status="uploaded",
        )
        session.add(file)
        await session.flush()

        await _scan_file_for_threats(session, "scan-mime-1")
        await session.refresh(file)

        assert file.scan_status == "suspicious"
        assert "mime type" in file.scan_details

    async def test_skip_nonexistent_file(self, session):
        """V-M-TASKS / scenario-5: Tasks skip gracefully if file_id not found."""
        await _scan_file_for_threats(session, "nonexistent-id")
        # No exception raised


class TestExtractFileMetadata:
    """V-M-TASKS / scenario-3: extract_file_metadata populates metadata for text files."""

    async def test_text_file_metadata(self, session, make_stored_file, tmp_storage, monkeypatch):
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)
        monkeypatch.setattr("src.tasks.STORAGE_DIR", tmp_storage)

        file = make_stored_file(
            file_id="meta-text-1",
            mime_type="text/plain",
            stored_name="meta-text-1.txt",
        )
        session.add(file)
        await session.flush()

        # Create physical file
        (tmp_storage / "meta-text-1.txt").write_text("line1\nline2\nline3")

        await _extract_file_metadata(session, "meta-text-1")
        await session.refresh(file)

        assert file.metadata_json is not None
        assert file.metadata_json["line_count"] == 3
        assert file.processing_status == "processed"

    async def test_missing_file_marks_failed(self, session, make_stored_file, tmp_storage, monkeypatch):
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)
        monkeypatch.setattr("src.tasks.STORAGE_DIR", tmp_storage)

        file = make_stored_file(
            file_id="meta-missing-1",
            stored_name="nonexistent.txt",
        )
        session.add(file)
        await session.flush()

        await _extract_file_metadata(session, "meta-missing-1")
        await session.refresh(file)

        assert file.processing_status == "failed"


class TestSendFileAlert:
    """V-M-TASKS / scenario-4: send_file_alert creates appropriate alerts."""

    async def test_warning_for_suspicious_file(self, session, make_stored_file):
        file = make_stored_file(
            file_id="alert-sus-1",
            processing_status="processed",
            scan_status="suspicious",
            scan_details="suspicious extension .exe",
            requires_attention=True,
        )
        session.add(file)
        await session.flush()

        await _send_file_alert(session, "alert-sus-1")

        from sqlalchemy import select
        result = await session.execute(
            select(Alert).where(Alert.file_id == "alert-sus-1")
        )
        alert = result.scalar_one()
        assert alert.level == "warning"
        assert "attention" in alert.message.lower() or "requires" in alert.message.lower()

    async def test_info_for_clean_file(self, session, make_stored_file):
        file = make_stored_file(
            file_id="alert-clean-1",
            processing_status="processed",
            scan_status="clean",
            requires_attention=False,
        )
        session.add(file)
        await session.flush()

        await _send_file_alert(session, "alert-clean-1")

        from sqlalchemy import select
        result = await session.execute(
            select(Alert).where(Alert.file_id == "alert-clean-1")
        )
        alert = result.scalar_one()
        assert alert.level == "info"

    async def test_critical_for_failed_file(self, session, make_stored_file):
        file = make_stored_file(
            file_id="alert-fail-1",
            processing_status="failed",
        )
        session.add(file)
        await session.flush()

        await _send_file_alert(session, "alert-fail-1")

        from sqlalchemy import select
        result = await session.execute(
            select(Alert).where(Alert.file_id == "alert-fail-1")
        )
        alert = result.scalar_one()
        assert alert.level == "critical"
