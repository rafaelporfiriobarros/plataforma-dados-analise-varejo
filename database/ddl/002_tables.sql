CREATE TABLE IF NOT EXISTS bronze.vendas_cartoes (
    data_transacao TEXT,
    data_liberacao_prevista TEXT,
    bandeira TEXT,
    forma_pagamento TEXT,
    valor_bruto TEXT,
    valor_taxa TEXT,
    valor_liquido TEXT,
    status TEXT,
    source_file TEXT NOT NULL,
    batch_id TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE NULLS NOT DISTINCT (
        data_transacao,
        data_liberacao_prevista,
        bandeira,
        forma_pagamento,
        valor_bruto,
        valor_taxa,
        valor_liquido,
        status,
        source_file
    )
);
CREATE TABLE IF NOT EXISTS bronze.vendas_por_horario (
    mes TEXT,
    hora TEXT,
    qtd_clientes TEXT,
    qtd_produtos TEXT,
    total_venda TEXT,
    source_file TEXT NOT NULL,
    batch_id TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (mes, hora, source_file)
);
CREATE TABLE IF NOT EXISTS silver.vendas_cartoes (
  data_transacao TIMESTAMP NOT NULL, data_liberacao_prevista TIMESTAMP,
  bandeira TEXT NOT NULL, forma_pagamento TEXT NOT NULL,
  valor_bruto NUMERIC(14,2) NOT NULL, valor_taxa NUMERIC(14,2) NOT NULL,
  valor_liquido NUMERIC(14,2) NOT NULL, status TEXT NOT NULL, mes TEXT NOT NULL, hora INTEGER NOT NULL,
  UNIQUE (data_transacao, forma_pagamento, bandeira, valor_bruto, valor_taxa, valor_liquido, status)
);
CREATE TABLE IF NOT EXISTS silver.vendas_por_horario (
    mes DATE NOT NULL,
    hora INTEGER NOT NULL,
    qtd_clientes INTEGER NOT NULL,
    qtd_produtos INTEGER NOT NULL,
    total_venda NUMERIC(14,2) NOT NULL,

    UNIQUE (mes, hora)
);
CREATE TABLE IF NOT EXISTS gold.dim_tempo (
  data_key DATE PRIMARY KEY, ano INTEGER NOT NULL, mes INTEGER NOT NULL,
  nome_mes TEXT NOT NULL, trimestre INTEGER NOT NULL, dia INTEGER NOT NULL, dia_semana INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS gold.dim_mes (
  mes_key DATE PRIMARY KEY,
  ano INTEGER NOT NULL,
  numero_mes INTEGER NOT NULL,
  nome_mes TEXT NOT NULL,
  ano_mes TEXT NOT NULL,
  trimestre INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS gold.dim_pagamento (
  pagamento_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, forma_pagamento TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS gold.dim_bandeira (
  bandeira_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, bandeira TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS gold.dim_horario (
  hora_key INTEGER PRIMARY KEY CHECK (hora_key BETWEEN 0 AND 23), turno TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gold.fato_pagamentos (
  pagamento_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  data_key DATE NOT NULL REFERENCES gold.dim_tempo(data_key),
  mes_key DATE REFERENCES gold.dim_mes(mes_key),
  hora_key INTEGER NOT NULL REFERENCES gold.dim_horario(hora_key),
  pagamento_key INTEGER NOT NULL REFERENCES gold.dim_pagamento(pagamento_key),
  bandeira_key INTEGER NOT NULL REFERENCES gold.dim_bandeira(bandeira_key),
  valor_bruto NUMERIC(14,2) NOT NULL, valor_taxa NUMERIC(14,2) NOT NULL,
  valor_liquido NUMERIC(14,2) NOT NULL, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gold.fato_vendas_horario (
    venda_horario_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mes DATE NOT NULL REFERENCES gold.dim_mes(mes_key),
    hora_key INTEGER NOT NULL REFERENCES gold.dim_horario(hora_key),
    qtd_clientes INTEGER NOT NULL,
    qtd_produtos INTEGER NOT NULL,
    total_venda NUMERIC(14,2) NOT NULL,

    UNIQUE (mes, hora_key)
);
CREATE INDEX IF NOT EXISTS idx_fato_pagamentos_data ON gold.fato_pagamentos(data_key);
CREATE INDEX IF NOT EXISTS idx_fato_pagamentos_pagamento ON gold.fato_pagamentos(pagamento_key);
CREATE INDEX IF NOT EXISTS idx_fato_vendas_hora ON gold.fato_vendas_horario(hora_key);

CREATE INDEX IF NOT EXISTS idx_fato_pagamentos_mes ON gold.fato_pagamentos(mes_key);
