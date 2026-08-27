def gerar_mensagem(nome: str, pix: str, estagio: str, vencimento: str = "", valor: str = "", mensagem_customizada: str = "") -> str:
    """
    Gera o texto da mensagem de cobrança personalizada por estágio.

    Parâmetros:
        nome    → Nome completo do cliente
        pix     → Chave PIX
        estagio → Estágio da régua (t_minus_5, t_minus_2, t_0, t_plus_2, manual)
        vencimento → Data de vencimento formatada (ex: 10/10/2026)
        valor      → Valor cobrado formatado (ex: R$ 50,00)
        mensagem_customizada → Mensagem customizada opcional definida para o cliente

    Retorno:
        Texto formatado da mensagem.
    """
    primeiro_nome = nome.split()[0] if nome else "Cliente"

    if mensagem_customizada:
        return mensagem_customizada.replace("{nome}", primeiro_nome).replace("{pix}", pix).replace("{vencimento}", vencimento).replace("{valor}", valor)

    # Mensagens diferenciadas por estágio
    mensagens = {
        "t_minus_5": (
            f"Olá {primeiro_nome}, paz e bem!\n\n"
            "Esperamos que nosso serviço esteja atendendo às suas expectativas.\n"
            f"Seu vencimento é dia {vencimento}. Considere antecipar seu pagamento.\n\n"
            f"*Valor: {valor}*\n"
            "*Forma de pagamento:*\n"
            "PIX (CPF): 388.010.273-20\n"
            "Banco Sicredi - Titular: Cezar Alfredo dos Santos Alves\n\n"
            "Agradecemos antecipadamente sua atenção.\n"
            "# Para cancelar entre em contato. #"
        ),
        "t_minus_2": (
            f"Olá {primeiro_nome}, paz e bem!\n\n"
            f"Lembramos que seu pagamento vence em 2 dias ({vencimento}).\n\n"
            f"*Valor: {valor}*\n"
            "*Forma de pagamento:*\n"
            "PIX (CPF): 388.010.273-20\n"
            "Banco Sicredi - Titular: Cezar Alfredo dos Santos Alves\n\n"
            "Agradecemos antecipadamente sua atenção.\n"
            "# Para cancelar entre em contato. #"
        ),
        "t_0": (
            f"Olá {primeiro_nome}, paz e bem!\n\n"
            f"Hoje é o dia do vencimento ({vencimento}).\n\n"
            f"*Valor: {valor}*\n"
            "*Forma de pagamento:*\n"
            "PIX (CPF): 388.010.273-20\n"
            "Banco Sicredi - Titular: Cezar Alfredo dos Santos Alves\n\n"
            "Agradecemos antecipadamente sua atenção.\n"
            "# Para cancelar entre em contato. #"
        ),
        "t_plus_2": (
            f"Olá {primeiro_nome}, paz e bem!\n\n"
            f"Seu pagamento está atrasado há 2 dias (vencimento: {vencimento}).\n"
            "Por favor, regularize sua situação o quanto antes.\n\n"
            f"*Valor: {valor}*\n"
            "*Forma de pagamento:*\n"
            "PIX (CPF): 388.010.273-20\n"
            "Banco Sicredi - Titular: Cezar Alfredo dos Santos Alves\n\n"
            "# Para cancelar entre em contato. #"
        ),
        "manual": (
            f"Olá {primeiro_nome}, paz e bem!\n\n"
            "Que o serviço de hospedagem esteja atendendo às suas expectativas.\n"
            f"Data de vencimento: {vencimento}.\n\n"
            f"*Valor: {valor}*\n"
            "*Forma de pagamento:*\n"
            "PIX (CPF): 388.010.273-20\n"
            "Banco Sicredi - Titular: Cezar Alfredo dos Santos Alves\n\n"
            "Agradecemos antecipadamente sua atenção.\n"
            "Obs.: Envio automático e recorrente via *Email e/ou Whatsapp*.\n"
            "# Para cancelar entre em contato. #"
        ),
    }

    return mensagens.get(estagio, mensagens["manual"])

