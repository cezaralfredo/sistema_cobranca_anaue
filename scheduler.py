"""
Agendador do Sistema de Cobrança Anaue.

Executa diariamente (horário configurável via CRON_HOUR/CRON_MINUTE e TZ) a
régua de cobrança (main.executar_regua) dentro do próprio container.

Substitui o padrão anterior (container cron com docker-socket a fazer
`docker exec` num worker) por um único serviço interno, sem depender de
imagem de cron externa nem de acesso ao /var/run/docker.sock.
"""

import datetime
import os
from zoneinfo import ZoneInfo

import main as cobranca


def _proximo_instante(hour: int, minute: int, tz: str) -> datetime.datetime:
    tzinfo = ZoneInfo(tz)
    agora = datetime.datetime.now(tzinfo)
    alvo = agora.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if alvo <= agora:
        alvo += datetime.timedelta(days=1)
    return alvo


def main_loop():
    hour = int(os.getenv("CRON_HOUR", "9"))
    minute = int(os.getenv("CRON_MINUTE", "0"))
    tz = os.getenv("TZ", "America/Sao_Paulo")
    print(f"[AGENDADOR] Regua de cobranca roda diariamente as {hour:02d}:{minute:02d} ({tz})")

    while True:
        alvo = _proximo_instante(hour, minute, tz)
        espera = (alvo - datetime.datetime.now(alvo.tzinfo)).total_seconds()
        print(f"[AGENDADOR] Proxima execucao em {espera / 3600:.2f}h -> {alvo.isoformat()}")

        time.sleep(espera + 1)

        try:
            cobranca.executar_regua()
        except Exception as e:  # noqa: BLE001 - nunca deixar o agendador morrer
            print(f"[AGENDADOR] Execucao falhou: {e}")
        time.sleep(10)


if __name__ == "__main__":
    import time
    main_loop()