CREATE TABLE IF NOT EXISTS gold.dim_tempo (
  data_key DATE PRIMARY KEY,
  ano INTEGER,
  mes INTEGER,
  dia INTEGER,
  dia_semana INTEGER
);
CREATE TABLE IF NOT EXISTS gold.dim_pagamento (
  pagamento_key SERIAL PRIMARY KEY,
  forma_pagamento TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS gold.dim_bandeira (
  bandeira_key SERIAL PRIMARY KEY,
  bandeira TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS gold.fato_pagamentos (
  pagamento_id BIGSERIAL PRIMARY KEY,
  data_key DATE REFERENCES gold.dim_tempo(data_key),
  pagamento_key INTEGER REFERENCES gold.dim_pagamento(pagamento_key),
  bandeira_key INTEGER REFERENCES gold.dim_bandeira(bandeira_key),
  valor_bruto NUMERIC(14,2), valor_taxa NUMERIC(14,2), valor_liquido NUMERIC(14,2)
);
