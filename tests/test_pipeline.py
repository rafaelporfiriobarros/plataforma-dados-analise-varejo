import pandas as pd
from mercado_analytics.transformation.clean import clean_cards, clean_hourly
from mercado_analytics.quality.checks import validate_cards, validate_hourly
from mercado_analytics.analytics.marts import sales_by_hour

def test_card_money_and_pix_brand():
    raw = pd.DataFrame({
        "Data da Transação": ["01/01/2026 10:00"], "Data prevista de liberação": ["01/01/2026 10:00"],
        "Bandeira": [None], "Forma de Pagamento": ["Pix"], "Valor Bruto": ["10,00"],
        "Valor Taxa": ["0,10"], "Valor Líquido": ["9,90"], "Status": ["Aprovada"]})
    out = clean_cards(raw)
    assert out.loc[0, "valor_bruto"] == 10.0
    assert out.loc[0, "bandeira"] == "Não se aplica"
    assert validate_cards(out)

def test_weighted_ticket_by_hour():
    raw = pd.DataFrame({"mes":["2026-01","2026-02"],"hora":["10:00","10:00"],"qtd_clientes":[1,9],"qtd_produtos":[1,9],"total_venda":[100.0,90.0]})
    out = clean_hourly(raw)
    result = sales_by_hour(out)
    assert result.loc[0, "ticket_medio"] == 19.0
    assert validate_hourly(out)
