from pathlib import Path

from mercado_analytics.ingestion.load import _batch_id


def test_batch_id_from_monthly_filename():
    assert _batch_id(Path("vendas_cartoes_2026_09.csv")) == "2026-09"
    assert _batch_id(Path("vendas_por_horario_2026-10.csv")) == "2026-10"
    assert _batch_id(Path("vendas_cartoes_2026_01_2026_03.csv")) == "2026-01_2026-03"


def test_monthly_audit_assets_exist():
    sql = Path("database/ddl/003_observability.sql").read_text(encoding="utf-8")
    ddl = Path("database/ddl/002_tables.sql").read_text(encoding="utf-8")
    dag = Path("airflow/dags/mercado_analytics_dag.py").read_text(encoding="utf-8")
    assert "audit.processed_files" in sql
    for field in ["source_file", "batch_id", "ingested_at"]:
        assert field in ddl
    assert "mercado_analytics_monthly" in dag
    assert "schedule=None" in dag


def test_file_hash_changes_when_content_changes(tmp_path):
    from mercado_analytics.ingestion.load import RawBatch

    path = tmp_path / "vendas_cartoes_2026_04.csv"
    path.write_text("a;b\n1;2\n", encoding="utf-8")
    first = RawBatch("cards", path, "2026-04").file_hash

    path.write_text("a;b\n1;3\n", encoding="utf-8")
    second = RawBatch("cards", path, "2026-04").file_hash

    assert len(first) == 64
    assert first != second


def test_reprocessing_assets_exist():
    sql = Path("database/ddl/003_observability.sql").read_text(encoding="utf-8")
    postgres = Path("src/mercado_analytics/database/postgres.py").read_text(encoding="utf-8")
    assert "file_hash" in sql
    assert "audit.processed_file_events" in sql
    assert "REPROCESSED" in sql
    assert "_delete_batch_from_warehouse" in postgres
    assert "Content change detected" in postgres
