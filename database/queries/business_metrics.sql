-- Métricas centrais para consumo analítico
SELECT
  forma_pagamento,
  COUNT(*) AS transacoes,
  SUM(valor_bruto) AS valor_bruto,
  SUM(valor_taxa) AS taxas,
  SUM(valor_liquido) AS valor_liquido,
  SUM(valor_taxa) / NULLIF(SUM(valor_bruto), 0) AS taxa_efetiva
FROM silver.vendas_cartoes
WHERE status = 'Aprovada'
GROUP BY forma_pagamento
ORDER BY valor_bruto DESC;
