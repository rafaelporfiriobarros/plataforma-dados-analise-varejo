from pathlib import Path

def test_star_schema_and_views_exist():
    root = Path(__file__).resolve().parents[1]
    ddl = (root / "database/ddl/002_tables.sql").read_text(encoding="utf-8")
    views = (root / "database/views/001_analytics_views.sql").read_text(encoding="utf-8")
    for obj in ["gold.dim_tempo", "gold.dim_mes", "gold.dim_pagamento", "gold.dim_bandeira", "gold.dim_horario", "gold.fato_pagamentos", "gold.fato_vendas_horario"]:
        assert obj in ddl
    for view in ["gold.vw_kpis", "gold.vw_vendas_por_hora", "gold.vw_meios_pagamento"]:
        assert view in views


def test_month_dimension_migration_and_builder():
    root = Path(__file__).resolve().parents[1]
    ddl = (root / "database/ddl/002_tables.sql").read_text(encoding="utf-8")
    migration = (root / "database/ddl/004_dim_mes_migration.sql").read_text(encoding="utf-8")
    builder = (root / "src/mercado_analytics/database/postgres.py").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS gold.dim_mes" in ddl
    assert "ADD COLUMN IF NOT EXISTS mes_key" in migration
    assert "UPDATE gold.fato_pagamentos SET mes_key" in migration
    assert "fk_fato_vendas_dim_mes" in migration
    assert "INSERT INTO gold.dim_mes" in builder
    assert "date_trunc('month',s.data_transacao)::date" in builder
