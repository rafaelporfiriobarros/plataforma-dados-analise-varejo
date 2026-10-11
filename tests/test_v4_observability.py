from pathlib import Path

def test_v4_assets_exist():
    assert Path("airflow/dags/mercado_analytics_dag.py").exists()
    assert Path("database/ddl/003_observability.sql").exists()

def test_audit_ddl():
    sql=Path("database/ddl/003_observability.sql").read_text(encoding="utf-8")
    assert "audit.pipeline_runs" in sql
    assert "audit.data_quality_results" in sql
