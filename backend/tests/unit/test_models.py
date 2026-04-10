from sqlalchemy import inspect

from src.models import Alert, Base, StoredFile


class TestStoredFileSchema:
    """V-M-MODELS / scenario-1: StoredFile has all required columns."""

    def test_table_name(self):
        assert StoredFile.__tablename__ == "files"

    def test_required_columns_exist(self):
        mapper = inspect(StoredFile)
        column_names = {c.key for c in mapper.column_attrs}
        expected = {
            "id", "title", "original_name", "stored_name", "mime_type",
            "size", "processing_status", "scan_status", "scan_details",
            "metadata_json", "requires_attention", "created_at", "updated_at",
        }
        assert expected.issubset(column_names)

    def test_primary_key_is_id(self):
        mapper = inspect(StoredFile)
        pk_cols = [c.name for c in mapper.mapper.primary_key]
        assert pk_cols == ["id"]


class TestAlertSchema:
    """V-M-MODELS / scenario-2: Alert FK references files.id."""

    def test_table_name(self):
        assert Alert.__tablename__ == "alerts"

    def test_file_id_foreign_key(self):
        mapper = inspect(Alert)
        file_id_col = mapper.columns["file_id"]
        fk_targets = [fk.target_fullname for fk in file_id_col.foreign_keys]
        assert "files.id" in fk_targets

    def test_autoincrement_id(self):
        mapper = inspect(Alert)
        id_col = mapper.columns["id"]
        assert id_col.autoincrement is not False


class TestCascadeDelete:
    """V-M-MODELS / scenario-3: Cascade delete on StoredFile removes related Alerts."""

    async def test_cascade_delete_removes_alerts(self, session, make_stored_file, make_alert):
        file = make_stored_file(file_id="cascade-test-1")
        session.add(file)
        await session.flush()

        alert1 = make_alert(file_id="cascade-test-1", level="info", message="Alert 1")
        alert2 = make_alert(file_id="cascade-test-1", level="warning", message="Alert 2")
        session.add_all([alert1, alert2])
        await session.flush()

        await session.delete(file)
        await session.flush()

        from sqlalchemy import select
        result = await session.execute(
            select(Alert).where(Alert.file_id == "cascade-test-1")
        )
        remaining = result.scalars().all()
        assert len(remaining) == 0, "Cascade delete should remove all related alerts"
