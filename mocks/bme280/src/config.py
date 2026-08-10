from dataclasses import dataclass
import os
from dotenv import load_dotenv

def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} debe ser booleano; se recibió {raw!r}.")

def _int(name: str, default: int, minimum: int | None = None) -> int:
    value = int(os.getenv(name, str(default)))
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} debe ser >= {minimum}.")
    return value

def _float(
    name: str,
    default: float,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    value = float(os.getenv(name, str(default)))
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} debe ser >= {minimum}.")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} debe ser <= {maximum}.")
    return value

@dataclass(frozen=True)
class Settings:
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    mqtt_qos: int
    mqtt_retain: bool
    mqtt_keepalive_seconds: int
    mqtt_connect_timeout_seconds: int
    node_id: str
    sensor_uid: str
    schema_version: str
    publish_interval_seconds: float
    time_warp_factor: float
    random_seed: int
    base_temperature_c: float
    base_humidity_pct: float
    base_pressure_hpa: float
    chaos_enabled: bool
    drop_probability: float

    @property
    def measurement_topic(self) -> str:
        return f"meteo/sensor/{self.node_id}"

    @property
    def status_topic(self) -> str:
        return f"system/status/{self.node_id}"

    @property
    def real_wait_seconds(self) -> float:
        return self.publish_interval_seconds / self.time_warp_factor

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
        mqtt_retain=_bool("MQTT_RETAIN", False),
        mqtt_keepalive_seconds=_int("MQTT_KEEPALIVE_SECONDS", 60, 1),
        mqtt_connect_timeout_seconds=_int("MQTT_CONNECT_TIMEOUT_SECONDS", 10, 1),
        node_id=os.getenv("NODE_ID", "lit-cordoba-01"),
        sensor_uid=os.getenv("SENSOR_UID", "bme280-mock-01"),
        schema_version=os.getenv("SCHEMA_VERSION", "1.0"),
        publish_interval_seconds=_float("PUBLISH_INTERVAL_SECONDS", 60.0, 0.1),
        time_warp_factor=_float("TIME_WARP_FACTOR", 1.0, 0.01),
        random_seed=_int("RANDOM_SEED", 42),
        base_temperature_c=_float("BASE_TEMPERATURE_C", 22.0),
        base_humidity_pct=_float("BASE_HUMIDITY_PCT", 60.0, 0.0, 100.0),
        base_pressure_hpa=_float("BASE_PRESSURE_HPA", 1012.0, 800.0, 1200.0),
        chaos_enabled=_bool("CHAOS_ENABLED", False),
        drop_probability=_float("DROP_PROBABILITY", 0.0, 0.0, 1.0),
    )
