import logging
import os

import pandas as pd

from mercado_analytics.analytics.marts import build_kpis, payments, sales_by_hour
from mercado_analytics.config import GOLD_DIR, SILVER_DIR
from mercado_analytics.ingestion.load import discover_raw_batches, load_batch
from mercado_analytics.quality.checks import validate_cards, validate_hourly
from mercado_analytics.transformation.clean import clean_cards, clean_hourly

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


def _combine(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _clean_all_batches(batches):
    cards, hourly = [], []
    for batch in batches:
        raw = load_batch(batch)
        if batch.dataset == "cards":
            cards.append(clean_cards(raw))
        else:
            hourly.append(clean_hourly(raw))
    return _combine(cards).drop_duplicates(), _combine(hourly).drop_duplicates()


def run(load_db: bool | None = None):
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    if load_db is None:
        load_db = os.getenv("LOAD_TO_POSTGRES", "false").lower() in {"1", "true", "yes"}

    batches = discover_raw_batches()
    if not batches:
        raise FileNotFoundError(
            "Nenhum arquivo mensal encontrado. Use nomes como "
            "vendas_cartoes_2026_09.csv e vendas_por_horario_2026_09.csv."
        )

    if load_db:
        from mercado_analytics.database.postgres import get_processed_files

        processed = get_processed_files()

        pending = [
            b for b in batches
            if b.source_file not in processed
            or processed[b.source_file] is None
            or processed[b.source_file] != b.file_hash
        ]
    else:
        pending = batches

    if not pending:
        logger.info("No new or changed monthly RAW files to process")
        return

    logger.info("Found %s new/changed RAW file(s)", len(pending))
    raw_cards: list[pd.DataFrame] = []
    raw_hourly: list[pd.DataFrame] = []
    clean_cards_frames: list[pd.DataFrame] = []
    clean_hourly_frames: list[pd.DataFrame] = []
    file_payloads = []

    for batch in pending:
        logger.info("Processing %s [%s] sha256=%s", batch.source_file, batch.batch_id, batch.file_hash[:12])
        raw = load_batch(batch)
        if batch.dataset == "cards":
            clean = clean_cards(raw)
            validate_cards(clean)
            raw_cards.append(raw)
            clean_cards_frames.append(clean)
        else:
            clean = clean_hourly(raw)
            validate_hourly(clean)
            raw_hourly.append(raw)
            clean_hourly_frames.append(clean)
        file_payloads.append((batch, raw, clean))

    cards = _combine(clean_cards_frames)
    hourly = _combine(clean_hourly_frames)

    logger.info("Running data quality checks")
    if not cards.empty:
        validate_cards(cards)
    if not hourly.empty:
        validate_hourly(hourly)

    if load_db:
        logger.info("Loading monthly Bronze/Silver/Gold into PostgreSQL")
        from mercado_analytics.database.postgres import load_monthly_warehouse

        load_monthly_warehouse(
            file_payloads,
            incremental=os.getenv("INCREMENTAL_LOAD", "true").lower()
            in {"1", "true", "yes"},
        )


        cards, hourly = _clean_all_batches(batches)
    else:
        logger.info("PostgreSQL load disabled; building local cumulative outputs from discovered files")
        cards, hourly = _clean_all_batches(batches)

    for path, df in [
        (SILVER_DIR / "vendas_cartoes.csv", cards),
        (SILVER_DIR / "vendas_por_horario.csv", hourly),
    ]:
        if not df.empty:
            df.to_csv(path, index=False)

    if not load_db and not cards.empty and not hourly.empty:
        build_kpis(cards, hourly).to_csv(GOLD_DIR / "kpis.csv", index=False)
        sales_by_hour(hourly).to_csv(GOLD_DIR / "vendas_por_hora.csv", index=False)
        payments(cards).to_csv(GOLD_DIR / "meios_pagamento.csv", index=False)

    logger.info("Pipeline completed successfully")


if __name__ == "__main__":
    run()
