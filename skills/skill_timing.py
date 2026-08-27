from datetime import datetime


def calcular_estagio(data_vencimento_str: str) -> str | None:
    """
    Compara a data de vencimento com a data atual e retorna o estágio da régua de cobrança.

    Formato esperado da data: 'YYYY-MM-DD'

    Retornos possíveis:
        - "t_minus_5" → vence em 5 dias
        - "t_minus_2" → vence em 2 dias
        - "t_0"       → vence hoje
        - "t_plus_2"  → venceu há 2 dias
        - None        → data fora das regras definidas
    """
    hoje = datetime.now().date()
    vencimento = datetime.strptime(data_vencimento_str, "%Y-%m-%d").date()
    diferenca_dias = (vencimento - hoje).days

    regras = {
        5: "t_minus_5",
        2: "t_minus_2",
        0: "t_0",
        -2: "t_plus_2",
    }

    return regras.get(diferenca_dias, None)
