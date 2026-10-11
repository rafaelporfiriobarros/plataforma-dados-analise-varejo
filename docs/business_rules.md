# Regras de negócio

| Regra | Definição | Motivo |
|---|---|---|
| Ticket médio | `SUM(total_venda) / SUM(qtd_clientes)` | Evita média de médias e pondera corretamente o volume |
| Taxa efetiva | `SUM(valor_taxa) / SUM(valor_bruto)` | Mede o custo financeiro relativo |
| Receita líquida | `SUM(valor_liquido)` | Valor após taxas da fonte de pagamentos |
| PIX sem bandeira | `Não se aplica` | Bandeira de cartão não se aplica ao PIX |
| Reconciliação | `valor_bruto - valor_taxa = valor_liquido ± 0,02` | Detecta inconsistências financeiras respeitando arredondamento |
| Não negatividade | quantidades e valores analíticos >= 0 | Impede registros incompatíveis com o domínio atual |

## Observação sobre escopo

O faturamento consolidado da fonte de vendas por horário e o volume da fonte de pagamentos não são tratados como a mesma medida. O pipeline preserva essa distinção para evitar reconciliações indevidas entre fontes com escopos diferentes.
