import base64
import json
import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.config import Settings
from src.ohmc_client import OhmcClient, OhmcClientError


def _settings(**overrides) -> Settings:
    base = dict(
        mqtt_host="localhost",
        mqtt_port=1883,
        mqtt_username="",
        mqtt_password="",
        mqtt_qos=1,
        mqtt_keepalive_seconds=60,
        mqtt_connect_timeout_seconds=10,
        node_id="lit-cordoba-01",
        schema_version="1.0",
        poll_interval_seconds=900,
        request_timeout_seconds=5,
        ohmc_base_url="https://estaciones-beta.ohmc.com.ar/api/v1",
        ohmc_email="test@mi.unc.edu.ar",
        ohmc_password="secreto",
        ohmc_station_id=89,
        watch_dir="/tmp/no-usado",
        scan_interval_seconds=300,
    )
    base.update(overrides)
    return Settings(**base)


def _fake_jwt(exp_seconds_from_now: float) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({"exp": time.time() + exp_seconds_from_now}).encode()
    ).rstrip(b"=").decode()
    return f"{header}.{payload}.firma-falsa"


def _response(payload, status: int = 200):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload
    response.raise_for_status.side_effect = requests.HTTPError(str(status)) if status >= 400 else None
    return response


# Fixture real, capturada de GET /mediciones/ultimas?station_id=89 el 12/9/2026.
REAL_ULTIMAS_RESPONSE = {
    "meta": {"limit": 20, "count": 20, "filters": {"station_id": 89}},
    "data": [
        {"variable_id": 42, "station_id": 89, "valida_en": "2026-09-12T16:10:00Z",
         "referencia_en": "2026-09-12T16:10:00Z", "tipo_valor": "escalar", "valor": 5.676657306800145},
        {"variable_id": 280, "station_id": 89, "valida_en": "2026-09-12T16:10:00Z",
         "referencia_en": "2026-09-12T16:10:00Z", "tipo_valor": "escalar", "valor": 982.125},
        {"variable_id": 504, "station_id": 89, "valida_en": "2026-09-12T16:10:00Z",
         "referencia_en": "2026-09-12T16:10:00Z", "tipo_valor": "escalar", "valor": 91.93016725674521},
        {"variable_id": 732, "station_id": 89, "valida_en": "2026-09-12T16:10:00Z",
         "referencia_en": "2026-09-12T16:10:00Z", "tipo_valor": "escalar", "valor": 0.0},
        {"variable_id": 1028, "station_id": 89, "valida_en": "2026-09-12T16:10:00Z",
         "referencia_en": "2026-09-12T16:10:00Z", "tipo_valor": "escalar", "valor": 203.95604395604394},
        {"variable_id": 1213, "station_id": 89, "valida_en": "2026-09-12T16:10:00Z",
         "referencia_en": "2026-09-12T16:10:00Z", "tipo_valor": "escalar", "valor": 10.621670400000001},
        {"variable_id": 1591, "station_id": 89, "valida_en": "2026-09-12T16:10:00Z",
         "referencia_en": "2026-09-12T16:10:00Z", "tipo_valor": "escalar", "valor": 202.5},
    ],
}


def test_fetch_latest_reading_maps_real_response_correctly() -> None:
    settings = _settings()
    client = OhmcClient(settings)

    with patch("src.ohmc_client.requests.post", return_value=_response({
        "access_token": _fake_jwt(3600), "token_type": "bearer",
    })), patch("src.ohmc_client.requests.get", return_value=_response(REAL_ULTIMAS_RESPONSE)):
        reading = client.fetch_latest_reading()

    assert reading.temperature_c == pytest.approx(5.676657306800145)
    assert reading.pressure_hpa == pytest.approx(982.125)
    assert reading.humidity_pct == pytest.approx(91.93016725674521)
    assert reading.precipitation_mm == 0.0
    assert reading.wind_speed_kmh == pytest.approx(10.621670400000001)
    assert reading.wind_direction_deg == 202
    assert reading.measured_at.isoformat() == "2026-09-12T16:10:00+00:00"


def test_login_failure_raises_clear_error() -> None:
    settings = _settings()
    client = OhmcClient(settings)

    with patch("src.ohmc_client.requests.post", return_value=_response({"detail": "credenciales inválidas"}, status=401)):
        with pytest.raises(OhmcClientError, match="Login al OHMC falló"):
            client.fetch_latest_reading()


def test_token_is_cached_across_calls() -> None:
    settings = _settings()
    client = OhmcClient(settings)

    with patch("src.ohmc_client.requests.post", return_value=_response({
        "access_token": _fake_jwt(3600), "token_type": "bearer",
    })) as mock_post, patch("src.ohmc_client.requests.get", return_value=_response(REAL_ULTIMAS_RESPONSE)):
        client.fetch_latest_reading()
        client.fetch_latest_reading()

    assert mock_post.call_count == 1  # segunda llamada reusó el token cacheado


def test_expired_token_triggers_relogin() -> None:
    settings = _settings()
    client = OhmcClient(settings)

    with patch("src.ohmc_client.requests.post", return_value=_response({
        "access_token": _fake_jwt(1),  # vence en 1s, el margen de renovación es 300s
        "token_type": "bearer",
    })) as mock_post, patch("src.ohmc_client.requests.get", return_value=_response(REAL_ULTIMAS_RESPONSE)):
        client.fetch_latest_reading()
        client.fetch_latest_reading()

    assert mock_post.call_count == 2  # el token ya estaba "por vencer", se renovó


def test_401_forces_relogin_once_then_succeeds() -> None:
    settings = _settings()
    client = OhmcClient(settings)

    get_responses = [_response({}, status=401), _response(REAL_ULTIMAS_RESPONSE)]

    with patch("src.ohmc_client.requests.post", return_value=_response({
        "access_token": _fake_jwt(3600), "token_type": "bearer",
    })) as mock_post, patch("src.ohmc_client.requests.get", side_effect=get_responses):
        reading = client.fetch_latest_reading()

    assert reading.temperature_c == pytest.approx(5.676657306800145)
    assert mock_post.call_count == 2  # login inicial + re-login forzado por el 401


def test_missing_variable_in_response_maps_to_none() -> None:
    settings = _settings()
    client = OhmcClient(settings)
    partial_response = {"data": [row for row in REAL_ULTIMAS_RESPONSE["data"] if row["variable_id"] != 732]}

    with patch("src.ohmc_client.requests.post", return_value=_response({
        "access_token": _fake_jwt(3600), "token_type": "bearer",
    })), patch("src.ohmc_client.requests.get", return_value=_response(partial_response)):
        reading = client.fetch_latest_reading()

    assert reading.precipitation_mm is None
    assert reading.temperature_c is not None  # el resto sigue mapeando bien
