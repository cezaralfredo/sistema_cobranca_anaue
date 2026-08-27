import smtplib
import os
import mimetypes
from email.message import EmailMessage


class EmailSender:
    """
    Envia e-mails via SMTP com suporte a SSL.

    Parâmetros:
        smtp_server → Endereço do servidor SMTP (ex: "smtp.gmail.com")
        smtp_port   → Porta do servidor (ex: 465 para SSL, 587 para STARTTLS)
        email_user  → Endereço de e-mail remetente
        email_pass  → Senha ou App Password do remetente
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        email_user: str,
        email_pass: str,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_user = email_user
        self.email_pass = email_pass

    def enviar(self, destinatario: str, assunto: str, corpo: str, caminho_imagem: str = None) -> bool:
        """
        Envia um e-mail em formato texto puro via SMTP_SSL, com a opção de anexar imagem.
        """
        msg = EmailMessage()
        msg.set_content(corpo)
        msg["Subject"] = assunto
        msg["From"] = self.email_user
        msg["To"] = destinatario

        if caminho_imagem and os.path.exists(caminho_imagem):
            try:
                with open(caminho_imagem, 'rb') as f:
                    img_data = f.read()
                msg.add_attachment(img_data, maintype='image', subtype='png', filename='qrcode.png')
            except Exception as e:
                print(f"[EmailSender] Falha ao anexar imagem: {e}")

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.email_user, self.email_pass)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"[EmailSender] Erro ao enviar para {destinatario}: {e}")
            return False
