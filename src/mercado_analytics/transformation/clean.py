import pandas as pd

CARD_RENAME = {
    "Data da Transação": "data_transacao",
    "Data prevista de liberação": "data_liberacao_prevista",
    "Bandeira": "bandeira",
    "Forma de Pagamento": "forma_pagamento",
    "Valor Bruto": "valor_bruto",
    "Valor Taxa": "valor_taxa",
    "Valor Líquido": "valor_liquido",
    "Status": "status",
}


def _money(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )


def clean_cards(df: pd.DataFrame) -> pd.DataFrame:
    out = df.rename(columns=CARD_RENAME).copy().drop_duplicates()
    for col in ["data_transacao", "data_liberacao_prevista"]:
        out[col] = pd.to_datetime(out[col], dayfirst=True, errors="coerce")
    for col in ["valor_bruto", "valor_taxa", "valor_liquido"]:
        out[col] = _money(out[col])
    out["forma_pagamento"] = out["forma_pagamento"].str.strip().str.title()
    out["bandeira"] = out["bandeira"].fillna("Não se aplica").str.strip()
    out["status"] = out["status"].str.strip().str.title()
    out["mes"] = out["data_transacao"].dt.to_period("M").astype(str)
    out["hora"] = out["data_transacao"].dt.hour
    return out


def clean_hourly(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().drop_duplicates()
    out["mes"] = pd.to_datetime(out["mes"], format="%Y-%m", errors="coerce")
    out["hora"] = out["hora"].str.slice(0, 2).astype(int)
    for col in ["qtd_clientes", "qtd_produtos"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)
    out["total_venda"] = pd.to_numeric(out["total_venda"], errors="coerce")
    return out
