CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS audit.pipeline_runs (
    run_id uuid PRIMARY KEY,
    pipeline_name text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    status text NOT NULL,
    rows_bronze_cards int DEFAULT 0,
    rows_bronze_hourly int DEFAULT 0,
    rows_silver_cards int DEFAULT 0,
    rows_silver_hourly int DEFAULT 0,
    error_message text
);

CREATE TABLE IF NOT EXISTS audit.data_quality_results (
    id bigserial PRIMARY KEY,
    run_id uuid NOT NULL REFERENCES audit.pipeline_runs (run_id),
    check_name text NOT NULL,
    status text NOT NULL,
    checked_at timestamptz NOT NULL DEFAULT now(),
    details text
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_cards_business ON silver.vendas_cartoes (
    data_transacao,
    forma_pagamento,
    valor_bruto,
    valor_liquido,
    status
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_hourly_business ON silver.vendas_por_horario (mes, hora);


CREATE TABLE IF NOT EXISTS audit.processed_files (
    source_file text PRIMARY KEY,
    dataset text NOT NULL,
    batch_id text NOT NULL,
    status text NOT NULL,
    rows_read int NOT NULL DEFAULT 0,
    rows_inserted int NOT NULL DEFAULT 0,
    rows_skipped int NOT NULL DEFAULT 0,
    processed_at timestamptz NOT NULL DEFAULT now(),
    run_id uuid REFERENCES audit.pipeline_runs(run_id),
    error_message text
);

CREATE INDEX IF NOT EXISTS idx_processed_files_batch
    ON audit.processed_files(batch_id, dataset);


ALTER TABLE audit.processed_files
    ADD COLUMN IF NOT EXISTS file_hash text;

CREATE TABLE IF NOT EXISTS audit.processed_file_events (
    id bigserial PRIMARY KEY,
    source_file text NOT NULL,
    dataset text NOT NULL,
    batch_id text NOT NULL,
    file_hash text NOT NULL,
    action text NOT NULL CHECK (action IN ('PROCESSED', 'REPROCESSED', 'HASH_REGISTERED')),
    rows_read int NOT NULL DEFAULT 0,
    rows_inserted int NOT NULL DEFAULT 0,
    rows_skipped int NOT NULL DEFAULT 0,
    processed_at timestamptz NOT NULL DEFAULT now(),
    run_id uuid REFERENCES audit.pipeline_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_processed_file_events_source
    ON audit.processed_file_events(source_file, processed_at DESC);
