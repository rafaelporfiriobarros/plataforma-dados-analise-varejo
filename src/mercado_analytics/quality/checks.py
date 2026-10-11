def validate_cards(df):
    errors = []
    if df["data_transacao"].isna().any():
        errors.append("data_transacao contains null/invalid values")
    if (df[["valor_bruto", "valor_taxa", "valor_liquido"]] < 0).any().any():
        errors.append("negative monetary values found")
    diff = (df["valor_bruto"] - df["valor_taxa"] - df["valor_liquido"]).abs()
    if (diff > 0.02).any():
        errors.append("gross - fee != net beyond tolerance")
    if errors:
        raise ValueError("; ".join(errors))
    return True


def validate_hourly(df):
    if (df[["qtd_clientes", "qtd_produtos", "total_venda"]] < 0).any().any():
        raise ValueError("negative hourly metrics found")
    return True
