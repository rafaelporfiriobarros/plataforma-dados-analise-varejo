import pandas as pd

def build_kpis(cards: pd.DataFrame, hourly: pd.DataFrame) -> pd.DataFrame:
    approved = cards[cards["status"].eq("Aprovada")]
    clients = hourly["qtd_clientes"].sum()
    sales = hourly["total_venda"].sum()
    return pd.DataFrame([{
        "faturamento_loja": sales,
        "clientes": clients,
        "produtos": hourly["qtd_produtos"].sum(),
        "ticket_medio": sales / clients if clients else 0,
        "volume_cartoes": approved["valor_bruto"].sum(),
        "receita_liquida_cartoes": approved["valor_liquido"].sum(),
        "taxas_cartoes": approved["valor_taxa"].sum(),
        "taxa_efetiva": approved["valor_taxa"].sum() / approved["valor_bruto"].sum() if approved["valor_bruto"].sum() else 0,
    }])

def sales_by_hour(hourly: pd.DataFrame) -> pd.DataFrame:
    g = hourly.groupby("hora", as_index=False).agg(total_venda=("total_venda", "sum"), qtd_clientes=("qtd_clientes", "sum"), qtd_produtos=("qtd_produtos", "sum"))
    g["ticket_medio"] = g["total_venda"].div(g["qtd_clientes"]).fillna(0)
    return g

def payments(cards: pd.DataFrame) -> pd.DataFrame:
    return cards.groupby("forma_pagamento", as_index=False).agg(transacoes=("forma_pagamento", "size"), valor_bruto=("valor_bruto", "sum"), valor_taxa=("valor_taxa", "sum"), valor_liquido=("valor_liquido", "sum"))
