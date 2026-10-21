from dataclasses import dataclass
import os
from dotenv import load_dotenv

def _int(name: str, default: int, minimum: int | None = None) -> int:
    value = int(os.getenv(name, str(default)))
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} debe ser >= {minimum}.")
    return value

@dataclass(frozen=True)
class Settings:
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    mqtt_qos: int
    mqtt_keepalive_seconds: int
    mqtt_connect_timeout_seconds: int
    node_id: str
    schema_version: str
    poll_interval_seconds: int
    request_timeout_seconds: int
    # Camino A (principal desde el 12/9/2026) -- API real del OHMC.
    ohmc_base_url: str
    ohmc_email: str
    ohmc_password: str
    ohmc_station_id: int
    # Camino B (fallback/histórico) -- reportes .xlsx exportados a mano desde
    # new.omixom.com. Se mantiene el código (report_ingestor.py) por si algún
    # día hace falta backfillear un rango que la API no tenga, pero main.py ya
    # no lo usa como vía principal.
    watch_dir: str
    scan_interval_seconds: int

    @property
    def measurement_topic(self) -> str:
        return f"meteo/external/{self.node_id}"

    @property
    def status_topic(self) -> str:
        return f"meteo/status/{self.node_id}"

    @property
    def processed_dir(self) -> str:
        return os.path.join(self.watch_dir, "processed")

    @property
    def failed_dir(self) -> str:
        return os.path.join(self.watch_dir, "failed")

def load_settings() -> Settings:
    load_dotenv()
    qos = _int("MQTT_QOS", 1, 0)
    if qos not in {0, 1, 2}:
        raise ValueError("MQTT_QOS debe ser 0, 1 o 2.")

    return Settings(
        mqtt_host=os.getenv("MQTT_HOST", "localhost"),
        mqtt_port=_int("MQTT_PORT", 1883, 1),
        mqtt_username=os.getenv("MQTT_USERNAME", ""),
        mqtt_password=os.getenv("MQTT_PASSWORD", ""),
        mqtt_qos=qos,
        mqtt_keepalive_seconds=_int("MQTT_KEEPALIVE_SECONDS", 60, 1),
        mqtt_connect_timeout_seconds=_int("MQTT_CONNECT_TIMEOUT_SECONDS", 10, 1),
        node_id=os.getenv("NODE_ID", "lit-cordoba-01"),
        schema_version=os.getenv("SCHEMA_VERSION", "1.0"),
        poll_interval_seconds=_int("POLL_INTERVAL_SECONDS", 900, 30),  # RF-11: 15 min default
        request_timeout_seconds=_int("REQUEST_TIMEOUT_SECONDS", 15, 1),
        ohmc_base_url=os.getenv("OHMC_BASE_URL", "https://estaciones-beta.ohmc.com.ar/api/v1"),
        ohmc_email=os.getenv("OHMC_EMAIL", ""),
        ohmc_password=os.getenv("OHMC_PASSWORD", ""),
        ohmc_station_id=_int("OHMC_STATION_ID", 89, 1),
        watch_dir=os.getenv("WATCH_DIR", "/data/reportes-omixom"),
        scan_interval_seconds=_int("SCAN_INTERVAL_SECONDS", 300, 10),
    )
