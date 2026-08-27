import requests
import time
from requests.exceptions import RequestException, Timeout


class WhatsAppSender:
    """
    Envia mensagens de texto via Evolution API v2.

    Parâmetros:
        api_url → URL base da Evolution API (ex: http://localhost:8080)
        instance → Nome da instância cadastrada na Evolution API
        api_key → Chave de autenticação da Evolution API
        timeout → Tempo máximo de espera para resposta (segundos)
        retries → Número de tentativas em caso de falha
    """

    def __init__(self, api_url: str, instance: str, api_key: str, timeout: int = 30, retries: int = 3):
        self.api_url = api_url.rstrip("/")
        self.instance = instance
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.retries = retries

        # URLs para Evolution GO
        self._text_url = f"{self.api_url}/send/text"
        self._media_url = f"{self.api_url}/send/media"
        # Endpoints de instância
        self._status_url = f"{self.api_url}/instance/status"
        self._connect_url = f"{self.api_url}/instance/connect"
        self._all_url = f"{self.api_url}/instance/all"

    def testar_conexao(self) -> bool:
        """
        Testa se a Evolution API (GO) está acessível e a instância está conectada.
        Verifica Connected + LoggedIn no endpoint /instance/status.
        Se desconectada, tenta reconectar automaticamente.
        """
        headers = {"apikey": self.api_key}
        timeout = 10

        # 1. Verificar se a API responde
        try:
            response = requests.get(self.api_url, timeout=timeout)
            # Evolution Go retorna 404 na raiz, mas isso prova que está viva
        except Exception as e:
            print(f"[WhatsAppSender] API não está acessível: {e}")
            return False

        # 2. Verificar status da instância via /instance/status
        try:
            print(f"[WhatsAppSender] Verificando status: {self._status_url}")
            response = requests.get(self._status_url, headers=headers, timeout=timeout)

            if response.status_code == 200:
                data = response.json()
                info = data.get("data", {})
                connected = info.get("Connected", False)
                logged_in = info.get("LoggedIn", False)
                print(f"[WhatsAppSender] Connected: {connected}, LoggedIn: {logged_in}")

                if connected and logged_in:
                    return True

                # Se não está conectada, tentar reconectar
                if not connected:
                    print("[WhatsAppSender] Instância desconectada. Tentando reconectar...")
                    try:
                        body = {"instanceName": self.instance}
                        r = requests.post(self._connect_url, json=body, headers=headers, timeout=timeout)
                        print(f"[WhatsAppSender] Reconnect response: {r.status_code}")
                        if r.status_code == 200:
                            # Aguardar reconexão
                            time.sleep(3)
                            # Verificar novamente
                            r2 = requests.get(self._status_url, headers=headers, timeout=timeout)
                            if r2.status_code == 200:
                                info2 = r2.json().get("data", {})
                                connected2 = info2.get("Connected", False)
                                logged_in2 = info2.get("LoggedIn", False)
                                print(f"[WhatsAppSender] Após reconexão — Connected: {connected2}, LoggedIn: {logged_in2}")
                                return connected2 and logged_in2
                    except Exception as e_reconnect:
                        print(f"[WhatsAppSender] Erro ao reconectar: {e_reconnect}")

                # Está conectada mas não logada — precisa escanear QR
                if connected and not logged_in:
                    print("[WhatsAppSender] Instância conectada mas não autenticada. Escaneie o QR code.")
                    return False

            elif response.status_code == 401:
                print(f"[WhatsAppSender] API Key não autorizada para status. Tentando /instance/all...")
        except Exception as e:
            print(f"[WhatsAppSender] Erro ao verificar status: {e}")

        # 3. Fallback: /instance/all (requer GLOBAL_API_KEY)
        try:
            response = requests.get(self._all_url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                instances = data.get("data", []) if isinstance(data, dict) else data
                for inst in instances:
                    if inst.get("name") == self.instance:
                        is_connected = inst.get("connected", False)
                        print(f"[WhatsAppSender] Fallback /instance/all — connected: {is_connected}")
                        return is_connected
        except Exception:
            pass

        print(f"[WhatsAppSender] Não conseguiu verificar status da instância")
        return False

    def enviar(self, numero: str, mensagem: str, caminho_imagem: "str | None" = None) -> bool:
        """
        Envia mensagem de texto (ou mídia) via Evolution GO.
        Implementa lógica de retentativa e timeout configurável.
        """
        headers = {
            "apikey": self.api_key.strip(),
            "Content-Type": "application/json",
        }

        # Debug: mostrar informações da chave (sem expor a completa)
        print(f"[WhatsAppSender] API Key (primeiros 10 chars): {self.api_key.strip()[:10]}")
        print(f"[WhatsAppSender] API Key length: {len(self.api_key)}")
        
        # Limpar número (remover espaços, traços, parênteses)
        numero_wpp = numero.replace("@s.whatsapp.net", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        # Garantir formato com código do país
        if not numero_wpp.startswith("55"):
            numero_wpp = "55" + numero_wpp
        print(f"[WhatsAppSender] Enviando para: {numero_wpp}")

        for i in range(self.retries):
            try:
                if caminho_imagem:
                    try:
                        import base64
                        with open(caminho_imagem, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

                        payload_media = {
                            "instanceName": self.instance,
                            "number": numero_wpp,
                            "media": encoded_string,
                            "mimeType": "image/jpeg",
                            "caption": mensagem
                        }

                        response = requests.post(
                            self._media_url,
                            json=payload_media,
                            headers=headers,
                            timeout=int(self.timeout * 1.5)
                        )

                        print(f"[WhatsAppSender] Response media: {response.status_code} - {response.text[:200]}")
                        response.raise_for_status()
                        return True
                    except Exception as e_media:
                        print(f"[WhatsAppSender] Falha no envio de mídia (tentativa {i+1}/{self.retries}): {e_media}. Tentando texto...")

                payload_text = {
                    "instanceName": self.instance,
                    "number": numero_wpp,
                    "text": mensagem
                }

                print(f"[WhatsAppSender] Enviando para URL: {self._text_url}")

                response = requests.post(
                    self._text_url,
                    json=payload_text,
                    headers=headers,
                    timeout=self.timeout
                )

                print(f"[WhatsAppSender] Response text: {response.status_code} - {response.text[:200]}")
                response.raise_for_status()
                return True

            except requests.exceptions.RequestException as e:
                print(f"[WhatsAppSender] Erro no envio para {numero} (tentativa {i+1}/{self.retries}): {e}")
                if i < self.retries - 1:
                    time.sleep(2)
                else:
                    return False

        return False
