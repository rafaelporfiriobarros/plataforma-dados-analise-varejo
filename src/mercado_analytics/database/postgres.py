import logging
from pathlib import Path
from uuid import uuid4

import pandas as pd
import psycopg
from psycopg import sql

from mercado_analytics.config import DB_CONFIG, ROOT_DIR
from mercado_analytics.observability import retry

logger = logging.getLogger(__name__)


@retry(attempts=5, delay=2)
def connect():
    return psycopg.connect(**DB_CONFIG)


def _execute_sql_dir(conn, folder: Path):
    for path in sorted(folder.glob("*.sql")):
        logger.info("Applying SQL: %s", path.name)
        conn.execute(path.read_text(encoding="utf-8"))


def initialize_database(conn):
    _execute_sql_dir(conn, ROOT_DIR / "database" / "ddl")


def _truncate(conn, table):
    schema, name = table.split(".")
    conn.execute(
        sql.SQL("TRUNCATE TABLE {}.{} RESTART IDENTITY CASCADE").format(
            sql.Identifier(schema), sql.Identifier(name)
        )
    )


def _insert_df(conn, table_name, df, conflict=False):
    if df.empty:
        return 0
    schema, name = table_name.split(".", 1)
    columns = list(df.columns)
    query = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({}){}").format(
        sql.Identifier(schema),
        sql.Identifier(name),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        sql.SQL(" ON CONFLICT DO NOTHING") if conflict else sql.SQL(""),
    )
    clean_df = df.astype(object).where(pd.notna(df), None)
    rows = list(clean_df.itertuples(index=False, name=None))
    before = None
    if conflict:
        before = conn.execute(
            sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier(schema), sql.Identifier(name)
            )
        ).fetchone()[0]
    with conn.cursor() as cur:
        cur.executemany(query, rows)
    if conflict:
        after = conn.execute(
            sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier(schema), sql.Identifier(name)
            )
        ).fetchone()[0]
        return after - before
    return len(rows)


def _audit_start(conn, run_id):
    conn.execute(
        "INSERT INTO audit.pipeline_runs(run_id,pipeline_name,status) VALUES (%s,'mercado_analytics_monthly','RUNNING')",
        (run_id,),
    )


def _audit_finish(conn, run_id, status, counts, error=None):
    conn.execute(
        """UPDATE audit.pipeline_runs SET finished_at=now(),status=%s,
        rows_bronze_cards=%s,rows_bronze_hourly=%s,rows_silver_cards=%s,
        rows_silver_hourly=%s,error_message=%s WHERE run_id=%s""",
        (status, *counts, error, run_id),
    )


def _dq(conn, run_id, name, ok, details=""):
    conn.execute(
        "INSERT INTO audit.data_quality_results(run_id,check_name,status,details) VALUES (%s,%s,%s,%s)",
        (run_id, name, "PASS" if ok else "FAIL", details),
    )


def get_processed_files():

    with connect() as conn:
        initialize_database(conn)
        rows = conn.execute(
            "SELECT source_file, file_hash FROM audit.processed_files WHERE status='SUCCESS'"
        ).fetchall()
        conn.commit()
    return {source_file: file_hash for source_file, file_hash in rows}


def _batch_bounds(batch_id):

    periods = batch_id.split("_")
    start = pd.Period(periods[0], freq="M").start_time.date()
    end = (pd.Period(periods[-1], freq="M") + 1).start_time.date()
    return start, end


def _delete_batch_from_warehouse(conn, batch):

    bronze_table = (
        "bronze.vendas_cartoes" if batch.dataset == "cards"
        else "bronze.vendas_por_horario"
    )
    schema, name = bronze_table.split(".")
    conn.execute(
        sql.SQL("DELETE FROM {}.{} WHERE source_file=%s").format(
            sql.Identifier(schema), sql.Identifier(name)
        ),
        (batch.source_file,),
    )
    start, end = _batch_bounds(batch.batch_id)
    if batch.dataset == "cards":
        conn.execute(
            "DELETE FROM silver.vendas_cartoes WHERE data_transacao >= %s AND data_transacao < %s",
            (start, end),
        )
    else:
        conn.execute(
            "DELETE FROM silver.vendas_por_horario WHERE mes >= %s AND mes < %s",
            (start, end),
        )


def _bronze_frame(raw, dataset, source_file, batch_id):
    out = raw.copy()
    if dataset == "cards":
        out.columns = [
            "data_transacao", "data_liberacao_prevista", "bandeira",
            "forma_pagamento", "valor_bruto", "valor_taxa",
            "valor_liquido", "status",
        ]
    else:
        out.columns = ["mes", "hora", "qtd_clientes", "qtd_produtos", "total_venda"]
    out["source_file"] = source_file
    out["batch_id"] = batch_id
    return out


def load_monthly_warehouse(file_payloads, incremental=True):
    run_id = uuid4()
    counts = [0, 0, 0, 0]
    with connect() as conn:
        initialize_database(conn)
        _audit_start(conn, run_id)
        conn.commit()
        try:
            if not incremental:
                for table in [
                    "bronze.vendas_cartoes", "bronze.vendas_por_horario",
                    "silver.vendas_cartoes", "silver.vendas_por_horario",
                ]:
                    _truncate(conn, table)
                conn.execute("TRUNCATE audit.processed_file_events, audit.processed_files")

            warehouse_changed = False
            for batch, raw, clean in file_payloads:
                previous = conn.execute(
                    "SELECT file_hash FROM audit.processed_files "
                    "WHERE source_file=%s AND status='SUCCESS'",
                    (batch.source_file,),
                ).fetchone()

                if previous and previous[0] == batch.file_hash:
                    logger.info("Skipping unchanged file %s", batch.source_file)
                    continue


                if previous and previous[0] is None:
                    logger.info("Registering baseline hash for legacy file %s", batch.source_file)
                    conn.execute(
                        "UPDATE audit.processed_files SET file_hash=%s, processed_at=now(), run_id=%s "
                        "WHERE source_file=%s",
                        (batch.file_hash, run_id, batch.source_file),
                    )
                    conn.execute(
                        """INSERT INTO audit.processed_file_events
                        (source_file,dataset,batch_id,file_hash,action,rows_read,run_id)
                        VALUES (%s,%s,%s,%s,'HASH_REGISTERED',%s,%s)""",
                        (batch.source_file, batch.dataset, batch.batch_id, batch.file_hash, len(raw), run_id),
                    )
                    continue

                action = "PROCESSED"
                if previous:
                    action = "REPROCESSED"
                    logger.warning(
                        "Content change detected for %s; reprocessing batch %s",
                        batch.source_file, batch.batch_id,
                    )
                    _delete_batch_from_warehouse(conn, batch)

                bronze = _bronze_frame(raw, batch.dataset, batch.source_file, batch.batch_id)
                bronze_table = (
                    "bronze.vendas_cartoes" if batch.dataset == "cards"
                    else "bronze.vendas_por_horario"
                )
                silver_table = (
                    "silver.vendas_cartoes" if batch.dataset == "cards"
                    else "silver.vendas_por_horario"
                )
                bronze_inserted = _insert_df(conn, bronze_table, bronze, conflict=incremental)
                silver_inserted = _insert_df(conn, silver_table, clean, conflict=incremental)
                skipped = max(len(raw) - bronze_inserted, 0)
                warehouse_changed = True

                if batch.dataset == "cards":
                    counts[0] += bronze_inserted
                    counts[2] += silver_inserted
                else:
                    counts[1] += bronze_inserted
                    counts[3] += silver_inserted

                conn.execute(
                    """INSERT INTO audit.processed_files
                    (source_file,dataset,batch_id,file_hash,status,rows_read,rows_inserted,rows_skipped,run_id)
                    VALUES (%s,%s,%s,%s,'SUCCESS',%s,%s,%s,%s)
                    ON CONFLICT (source_file) DO UPDATE SET
                    dataset=EXCLUDED.dataset,batch_id=EXCLUDED.batch_id,file_hash=EXCLUDED.file_hash,
                    status='SUCCESS',rows_read=EXCLUDED.rows_read,rows_inserted=EXCLUDED.rows_inserted,
                    rows_skipped=EXCLUDED.rows_skipped,processed_at=now(),run_id=EXCLUDED.run_id,
                    error_message=NULL""",
                    (batch.source_file, batch.dataset, batch.batch_id, batch.file_hash,
                     len(raw), bronze_inserted, skipped, run_id),
                )
                conn.execute(
                    """INSERT INTO audit.processed_file_events
                    (source_file,dataset,batch_id,file_hash,action,rows_read,rows_inserted,rows_skipped,run_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (batch.source_file, batch.dataset, batch.batch_id, batch.file_hash, action,
                     len(raw), bronze_inserted, skipped, run_id),
                )

            cards_count = conn.execute("SELECT count(*) FROM silver.vendas_cartoes").fetchone()[0]
            hourly_count = conn.execute("SELECT count(*) FROM silver.vendas_por_horario").fetchone()[0]
            _dq(conn, run_id, "cards_not_empty", cards_count > 0, f"rows={cards_count}")
            _dq(conn, run_id, "hourly_not_empty", hourly_count > 0, f"rows={hourly_count}")
            invalid_net = conn.execute(
                "SELECT count(*) FROM silver.vendas_cartoes WHERE valor_liquido > valor_bruto"
            ).fetchone()[0]
            _dq(conn, run_id, "net_not_above_gross", invalid_net == 0, f"invalid_rows={invalid_net}")

            if warehouse_changed:
                build_star_schema(conn)
                _execute_sql_dir(conn, ROOT_DIR / "database" / "views")
            _audit_finish(conn, run_id, "SUCCESS", counts)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            initialize_database(conn)

            _audit_finish(conn, run_id, "FAILED", counts, str(exc)[:2000])
            conn.commit()
            raise
    logger.info("Monthly warehouse run %s completed", run_id)
    return str(run_id)


def build_star_schema(conn):
    for table in [
        "gold.fato_pagamentos", "gold.fato_vendas_horario", "gold.dim_tempo",
        "gold.dim_mes",
        "gold.dim_pagamento", "gold.dim_bandeira", "gold.dim_horario",
    ]:
        _truncate(conn, table)
    conn.execute("""INSERT INTO gold.dim_horario(hora_key,turno) SELECT h,
        CASE WHEN h BETWEEN 6 AND 11 THEN 'Manhã' WHEN h BETWEEN 12 AND 17 THEN 'Tarde'
        WHEN h BETWEEN 18 AND 23 THEN 'Noite' ELSE 'Madrugada' END
        FROM generate_series(0,23) h""")
    conn.execute("INSERT INTO gold.dim_pagamento(forma_pagamento) SELECT DISTINCT forma_pagamento FROM silver.vendas_cartoes ORDER BY 1")
    conn.execute("INSERT INTO gold.dim_bandeira(bandeira) SELECT DISTINCT bandeira FROM silver.vendas_cartoes ORDER BY 1")
    conn.execute("""INSERT INTO gold.dim_tempo(data_key,ano,mes,nome_mes,trimestre,dia,dia_semana)
        SELECT d::date,EXTRACT(YEAR FROM d)::int,EXTRACT(MONTH FROM d)::int,TO_CHAR(d,'TMMonth'),
        EXTRACT(QUARTER FROM d)::int,EXTRACT(DAY FROM d)::int,EXTRACT(ISODOW FROM d)::int
        FROM generate_series((SELECT MIN(data_transacao)::date FROM silver.vendas_cartoes),
        (SELECT MAX(data_transacao)::date FROM silver.vendas_cartoes),'1 day') d""")
    conn.execute("""INSERT INTO gold.dim_mes(mes_key,ano,numero_mes,nome_mes,ano_mes,trimestre)
        SELECT DISTINCT date_trunc('month',d)::date,extract(year from d)::int,
        extract(month from d)::int,
        CASE extract(month from d)::int
          WHEN 1 THEN 'Janeiro' WHEN 2 THEN 'Fevereiro' WHEN 3 THEN 'Março'
          WHEN 4 THEN 'Abril' WHEN 5 THEN 'Maio' WHEN 6 THEN 'Junho'
          WHEN 7 THEN 'Julho' WHEN 8 THEN 'Agosto' WHEN 9 THEN 'Setembro'
          WHEN 10 THEN 'Outubro' WHEN 11 THEN 'Novembro' ELSE 'Dezembro' END,
        to_char(d,'YYYY-MM'),extract(quarter from d)::int
        FROM (SELECT data_transacao::date AS d FROM silver.vendas_cartoes
              UNION ALL SELECT mes AS d FROM silver.vendas_por_horario) dates""")
    conn.execute("""INSERT INTO gold.fato_pagamentos(data_key,mes_key,hora_key,pagamento_key,bandeira_key,
        valor_bruto,valor_taxa,valor_liquido,status)
        SELECT s.data_transacao::date,date_trunc('month',s.data_transacao)::date,s.hora,p.pagamento_key,b.bandeira_key,s.valor_bruto,s.valor_taxa,
        s.valor_liquido,s.status FROM silver.vendas_cartoes s
        JOIN gold.dim_pagamento p USING(forma_pagamento) JOIN gold.dim_bandeira b USING(bandeira)""")
    conn.execute("""INSERT INTO gold.fato_vendas_horario(mes,hora_key,qtd_clientes,qtd_produtos,total_venda)
        SELECT mes,hora,qtd_clientes,qtd_produtos,total_venda FROM silver.vendas_por_horario""")
