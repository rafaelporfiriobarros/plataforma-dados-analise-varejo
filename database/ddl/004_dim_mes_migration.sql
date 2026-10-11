
CREATE TABLE IF NOT EXISTS gold.dim_mes (
  mes_key DATE PRIMARY KEY,
  ano INTEGER NOT NULL,
  numero_mes INTEGER NOT NULL,
  nome_mes TEXT NOT NULL,
  ano_mes TEXT NOT NULL,
  trimestre INTEGER NOT NULL
);
ALTER TABLE gold.fato_pagamentos ADD COLUMN IF NOT EXISTS mes_key DATE;
INSERT INTO gold.dim_mes(mes_key,ano,numero_mes,nome_mes,ano_mes,trimestre)
SELECT DISTINCT date_trunc('month', d)::date, extract(year from d)::int,
  extract(month from d)::int,
  CASE extract(month from d)::int
    WHEN 1 THEN 'Janeiro' WHEN 2 THEN 'Fevereiro' WHEN 3 THEN 'Março'
    WHEN 4 THEN 'Abril' WHEN 5 THEN 'Maio' WHEN 6 THEN 'Junho'
    WHEN 7 THEN 'Julho' WHEN 8 THEN 'Agosto' WHEN 9 THEN 'Setembro'
    WHEN 10 THEN 'Outubro' WHEN 11 THEN 'Novembro' ELSE 'Dezembro' END,
  to_char(d,'YYYY-MM'), extract(quarter from d)::int
FROM (
  SELECT data_key AS d FROM gold.fato_pagamentos
  UNION ALL SELECT mes AS d FROM gold.fato_vendas_horario
) dates WHERE d IS NOT NULL
ON CONFLICT(mes_key) DO NOTHING;
UPDATE gold.fato_pagamentos SET mes_key=date_trunc('month',data_key)::date
WHERE mes_key IS DISTINCT FROM date_trunc('month',data_key)::date;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_fato_pagamentos_dim_mes'
     AND conrelid='gold.fato_pagamentos'::regclass) THEN
    ALTER TABLE gold.fato_pagamentos ADD CONSTRAINT fk_fato_pagamentos_dim_mes
      FOREIGN KEY(mes_key) REFERENCES gold.dim_mes(mes_key);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_fato_vendas_dim_mes'
     AND conrelid='gold.fato_vendas_horario'::regclass) THEN
    ALTER TABLE gold.fato_vendas_horario ADD CONSTRAINT fk_fato_vendas_dim_mes
      FOREIGN KEY(mes) REFERENCES gold.dim_mes(mes_key);
  END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_fato_pagamentos_mes ON gold.fato_pagamentos(mes_key);
