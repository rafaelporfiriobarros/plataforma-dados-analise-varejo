# Dicionário de dados

## Fonte: vendas_cartoes

| Campo normalizado | Tipo | Descrição |
|---|---|---|
| data_transacao | date | Data em que o pagamento ocorreu |
| forma_pagamento | text | Crédito, Débito, Pix ou Voucher |
| bandeira | text | Bandeira do cartão; `Não se aplica` para PIX |
| valor_bruto | decimal | Valor original da transação |
| valor_taxa | decimal | Taxa financeira associada |
| valor_liquido | decimal | Valor líquido após taxa |

## Fonte: vendas_por_horario

| Campo normalizado | Tipo | Descrição |
|---|---|---|
| hora | inteiro/texto normalizado | Faixa/horário analisado |
| qtd_clientes | integer | Quantidade de clientes |
| qtd_produtos | integer | Quantidade de produtos vendidos |
| total_venda | decimal | Faturamento da observação |
| ticket_medio | decimal | Métrica derivada; para agregações finais é recalculada de forma ponderada |

## Gold: fato_pagamentos

| Campo | Tipo | Papel |
|---|---|---|
| pagamento_id | bigint | Chave substituta da fato |
| data_key | date | FK para `dim_tempo` |
| pagamento_key | integer | FK para `dim_pagamento` |
| bandeira_key | integer | FK para `dim_bandeira` |
| valor_bruto | decimal(14,2) | Medida aditiva |
| valor_taxa | decimal(14,2) | Medida aditiva |
| valor_liquido | decimal(14,2) | Medida aditiva |

## Views de consumo

`gold.vw_kpis`: visão executiva dos principais indicadores.

`gold.vw_vendas_por_hora`: desempenho consolidado por horário.

`gold.vw_meios_pagamento`: transações e valores por forma de pagamento.
