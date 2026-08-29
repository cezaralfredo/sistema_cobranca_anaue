"""
Orquestrador principal do Sistema de Cobrança Anaue.

Fluxo:
  1. Conecta ao MongoDB e busca clientes com cobrança pendente
  2. Para cada cliente, calcula o estágio na régua de cobrança
  3. Se houver estágio válido e ainda não notificado:
     a. Gera a mensagem personalizada
     b. Envia via WhatsApp (Evolution API)
     c. Envia via E-mail (SMTP)
     d. Registra o envio no banco de dados
"""

import config
from skills import (
    calcular_estagio,
    gerar_mensagem,
    DatabaseManager,
    WhatsAppSender,
    EmailSender,
)
import time
import random
import argparse


def executar_regua(enviar_whatsapp=True, enviar_email=True):
    """
    Executa a régua de cobrança para todos os clientes pendentes.
    Permite filtrar o canal de envio (WhatsApp/E-mail).
    """

    # 1. Inicializar serviços
    db = DatabaseManager()
    
    whatsapp = None
    if enviar_whatsapp:
        whatsapp = WhatsAppSender(
            api_url=config.WHATSAPP_API_URL, 
            instance=config.WHATSAPP_INSTANCE,
            api_key=config.WHATSAPP_API_KEY,
            timeout=config.WHATSAPP_TIMEOUT,
            retries=config.WHATSAPP_RETRIES
        )
        
    email = None
    if enviar_email:
        email = EmailSender(
            smtp_server=config.SMTP_SERVER,
            smtp_port=config.SMTP_PORT,
            email_user=config.EMAIL_USER,
            email_pass=config.EMAIL_PASS,
        )

    # 2. Buscar clientes pendentes
    clientes = db.buscar_clientes_pendentes()
    print(f"[INFO] {len(clientes)} cliente(s) pendente(s) encontrado(s).")
    print(f"[MODO] Canais ativos: {'WhatsApp ' if enviar_whatsapp else ''}{'E-mail' if enviar_email else ''}")

    enviados = 0

    for cliente in clientes:
        nome = cliente.get("nome", "Cliente")
        telefone = cliente.get("telefone", "")
        email_dest = cliente.get("email", "")
        pix = cliente.get("cobranca", {}).get("pix", "")
        data_vencimento = cliente.get("cobranca", {}).get("data_vencimento", "")
        valor_raw = cliente.get("cobranca", {}).get("valor", 0)
        notificacoes_anteriores = cliente.get("notificacoes_enviadas", [])
        mensagem_customizada = cliente.get("mensagem_customizada", "")

        # Formatação de data e valor para a mensagem
        vencimento_f = data_vencimento
        if data_vencimento:
            try:
                from datetime import datetime
                vencimento_f = datetime.strptime(data_vencimento, "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                pass
        
        valor_f = f"R$ {valor_raw:_.2f}".replace(".", ",").replace("_", ".")

        # 3. Calcular estágio
        estagio = calcular_estagio(data_vencimento)

        if estagio is None:
            continue  # Hoje não é dia de notificar este cliente

        if estagio in notificacoes_anteriores:
            continue  # Já foi notificado neste estágio

        # 4. Gerar mensagem
        mensagem = gerar_mensagem(
            nome=nome, 
            pix=pix, 
            estagio=estagio, 
            vencimento=vencimento_f, 
            valor=valor_f, 
            mensagem_customizada=mensagem_customizada
        )

        if not mensagem:
            continue

        print(f"[COBRANÇA] {nome} -> Estágio: {estagio}")

        # Caminho da imagem (QR Code)
        import os
        caminho_qrcode = os.path.join(os.path.dirname(__file__), "static", "qrcode_cpf.jpg")
        imagem_anexo = caminho_qrcode if os.path.exists(caminho_qrcode) else None

        processado_com_sucesso = False

        # 5. Enviar WhatsApp
        if enviar_whatsapp and whatsapp and telefone:
            ok_whatsapp = whatsapp.enviar(telefone, mensagem)
            status_wpp = "OK" if ok_whatsapp else "FALHA"
            print(f"  WhatsApp ({telefone}): {status_wpp}")
            if ok_whatsapp:
                processado_com_sucesso = True

        # 6. Enviar E-mail
        if enviar_email and email and email_dest:
            assunto = "Lembrete de Pagamento – Anaue"
            ok_email = email.enviar(email_dest, assunto, mensagem, caminho_imagem=imagem_anexo)
            status_mail = "OK" if ok_email else "FALHA"
            print(f"  E-mail ({email_dest}): {status_mail}")
            if ok_email:
                processado_com_sucesso = True


        # 7. Registrar envio no banco (Se pelo menos um canal solicitado teve sucesso ou se tentamos apenas um)
        # Se pedimos os dois, e um deu OK, registramos. Se pedimos um, e deu OK, registramos.
        if processado_com_sucesso:
            db.registrar_envio(cliente["_id"], estagio)
            enviados += 1

        # 8. Intervalo para o próximo envio (apenas se enviou WhatsApp para evitar bloqueio)
        if enviar_whatsapp and telefone:
            intervalo = random.uniform(config.WHATSAPP_DELAY_MIN, config.WHATSAPP_DELAY_MAX)
            print(f"  [Aguardando {intervalo:.1f}s antes da próxima mensagem...]")
            time.sleep(intervalo)

    print(f"\n[RESULTADO] {enviados} cliente(s) notificado(s) com sucesso.")

    # 8. Fechar conexão
    db.fechar_conexao()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa a régua de cobrança Anaue.")
    parser.add_argument("--whatsapp", action="store_true", help="Envia apenas via WhatsApp")
    parser.add_argument("--email", action="store_true", help="Envia apenas via E-mail")
    
    args = parser.parse_args()

    # Se nenhum argumento for passado, envia por ambos
    wpp = args.whatsapp
    eml = args.email
    
    if not wpp and not eml:
        wpp = True
        eml = True
    elif wpp and eml:
        # Se passar os dois, envia pelos dois (comportamento explícito)
        pass
    else:
        # Se passar apenas um, o outro fica falso (comportamento seletivo)
        pass

    print("=" * 50)
    print("  Sistema de Cobrança Anaue – Régua Automática")
    print("=" * 50)
    print()
    
    executar_regua(enviar_whatsapp=wpp, enviar_email=eml)
