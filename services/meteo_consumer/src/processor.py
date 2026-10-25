import json
from typing import Any, Protocol

from pydantic import ValidationError

from .mapper import meteo_row
from .models import EnvPayloadIn


class InsertDB(Protocol):
    def insert(self, row: dict[str, Any]) -> None: ...


class MessageProcessor:
    """Procesa mensajes MQTT meteorológicos.

    Retorna True cuando el mensaje puede ACKearse:
    - fue persistido correctamente; o
    - es inválido de forma permanente y reintentarlo no serviría.

    Retorna False cuando hubo una falla de DB potencialmente transitoria,
    para evitar confirmar el mensaje QoS 1.
    """

    def __init__(self, db: InsertDB) -> None:
        self._db = db

    def process(self, raw_payload: bytes | str) -> bool:
        try:
            payload_dict = json.loads(raw_payload)
        except (json.JSONDecodeError, UnicodeDecodeError):
            print("[CONSUMER] JSON inválido; mensaje descartado.")
            return True

        try:
            payload = EnvPayloadIn.model_validate(payload_dict)
        except ValidationError as error:
            print(f"[CONSUMER] Payload meteorológico inválido: {error}")
            return True

        try:
            self._db.insert(meteo_row(payload))
        except Exception as error:
            print(f"[CONSUMER] Falló la persistencia en meteo_data: {error}")
            return False

        return True
