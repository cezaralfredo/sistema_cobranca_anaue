import requests
import time
from requests.exceptions import RequestException, Timeout


class WhatsAppSender:
    """
    Envia mensagens de texto via Evolution API v2 (evolution-foundation).

    Parâmetros:
        api_url → URL base da Evolution API (ex: http://evolution-api:8080)
        instance → Nome da instância cadastrada na Evolution API
        api_key → Chave de autenticação (token da instância OU AUTHENTICATION_API_KEY global)
        timeout → Tempo máximo de espera para resposta (segundos)
        retries → Número de tentativas em caso de falha
    """

    def __init__(self, api_url: str, instance: str, api_key: str, timeout: int = 30, retries: int = 3):
        self.api_url = api_url.rstrip("/")
        self.instance = instance
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.retries = retries

        # URLs para Evolution API v2 (instância vai no PATH)
        self._text_url = f"{self.api_url}/message/sendText/{self.instance}"
        self._media_url = f"{self.api_url}/message/sendMedia/{self.instance}"
        # Status/gestão da instância (v2)
        self._connection_state_url = f"{self.api_url}/instance/connectionState/{self.instance}"
        self._connect_url = f"{self.api_url}/instance/connect/{self.instance}"
        self._all_url = f"{self.api_url}/instance/fetchInstances"

    def testar_conexao(self) -> bool:
        """
        Testa se a Evolution API (v2) está acessível e a instância está conectada.
        Verifica state == "open" no endpoint /instance/connectionState/{instance}.
        Se desconectada, tenta reconectar automaticamente.
        """
        headers = {"apikey": self.api_key}
        timeout = 10

        # 1. Verificar se a API responde
        try:
            response = requests.get(self.api_url, timeout=timeout)
        except Exception as e:
            print(f"[WhatsAppSender] API não está acessível: {e}")
            return False

        # 2. Verificar estado da instância via /instance/connectionState
        try:
            response = requests.get(self._connection_state_url, headers=headers, timeout=timeout)
            print(f"[WhatsAppSender] connectionState [{self.instance}]: HTTP {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                instance_data = data.get("instance", {}) if isinstance(data, dict) else {}
                state = instance_data.get("state", "close")
                print(f"[WhatsAppSender] state: {state}")

                if state == "open":
                    return True

                # Não conectada → tentar reconectar
                print("[WhatsAppSender] Instância conectada? Não. Tentando reconectar...")
                try:
                    r = requests.post(self._connect_url, headers=headers, timeout=timeout)
                    print(f"[WhatsAppSender] Reconnect response: {r.status_code}")
                    if r.status_code in (200, 201):
                        time.sleep(3)
                        r2 = requests.get(self._connection_state_url, headers=headers, timeout=timeout)
                        if r2.status_code == 200:
                            state2 = r2.json().get("instance", {}).get("state", "close")
                            print(f"[WhatsAppSender] Após reconexão — state: {state2}")
                            return state2 == "open"
                except Exception as e_reconnect:
                    print(f"[WhatsAppSender] Erro ao reconectar: {e_reconnect}")

                return False
            elif response.status_code in (401, 403):
                print(f"[WhatsAppSender] API Key não autorizada para {self.instance}.")
        except Exception as e:
            print(f"[WhatsAppSender] Erro ao verificar estado: {e}")

        # 3. Fallback: /instance/fetchInstances (caso o connectionState falhe)
        try:
            response = requests.get(self._all_url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                instances = data.get("data", data) if isinstance(data, dict) else data
                if isinstance(instances, list):
                    for inst in instances:
                        if inst.get("name") == self.instance:
                            connected = inst.get("connectionStatus") == "open"
                            print(f"[WhatsAppSender] Fallback fetchInstances — connected: {connected}")
                            return connected
        except Exception:
            pass

        print(f"[WhatsAppSender] Não conseguiu verificar estado da instância")
        return False

    def enviar(self, numero: str, mensagem: str, caminho_imagem: "str | None" = None) -> bool:
        """
        Envia mensagem de texto (ou mídia) via Evolution API v2.
        Rotas: /message/sendText/{instance} e /message/sendMedia/{instance}.
        Implementa lógica de retentativa e timeout configurável.
        """
        headers = {
            "apikey": self.api_key.strip(),
            "Content-Type": "application/json",
        }

        # Debug: mostrar informações da chave (sem expor a completa)
        print(f"[WhatsAppSender] API Key (primeiros 10 chars): {self.api_key.strip()[:10]}")
        print(f"[WhatsAppSender] API Key length: {len(self.api_key)}")

        # Limpar número (remover espaços, traços, parênteses, sufixo)
        numero_wpp = numero.replace("@s.whatsapp.net", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        # Garantir formato com código do país (evita duplicar o 55)
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
                            "number": numero_wpp,
                            "mediatype": "image",
                            "media": encoded_string,
                            "caption": mensagem,
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
                    "number": numero_wpp,
                    "text": mensagem,
                }

                print(f"[WhatsAppSender] Enviando para URL: {self._text_url} ({numero_wpp})")

                response = requests.post(
                    self._text_url,
                    json=payload_text,
                    headers=headers,
                    timeout=self.timeout
                )

                print(f"[WhatsAppSender] Response text: {response.status_code} - {response.text[:200]}")
                # Instância desconectada → não é erro de payload, mas falha de envio
                if response.status_code == 500 and "Connection Closed" in response.text:
                    print("[WhatsAppSender] Instância desconectada — não foi possível enviar.")
                    return False
                response.raise_for_status()
                return True

            except requests.exceptions.RequestException as e:
                print(f"[WhatsAppSender] Erro no envio para {numero} (tentativa {i+1}/{self.retries}): {e}")
                if i < self.retries - 1:
                    time.sleep(2)
                else:
                    return False

        return False