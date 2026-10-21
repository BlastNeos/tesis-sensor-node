"""Cliente para la API real del OHMC (Observatorio Hidrometeorológico de
Córdoba) -- estaciones-beta.ohmc.com.ar/api/v1 -- Camino A, confirmado
funcionando el 12/9/2026 contra la estación real (`station_id=89`, "APRHi -
Lab. Hidraulica-UNC").

Auth: login (email+password) -> JWT Bearer, válido unos días (`exp` en el
propio token). Este cliente cachea el token en memoria y lo renueva solo
cuando falta poco para vencer -- nunca lo escribe a disco.

Endpoint de datos: GET /mediciones/ultimas?station_id=X -- devuelve la última
lectura de TODAS las variables de la estación en un solo call (no filtra por
variable_ids pese a aceptar el parámetro, se filtra acá del lado cliente).
"""

import base64
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

from .config import Settings
from .models import OmixomReading

# variable_id de la estación 89 (Lab. Hidráulica-UNC) -- confirmados contra
# GET /variables?station_id=89 el 12/9/2026. Si en algún momento se agrega
# otra estación con distinto conjunto de variable_id, esto pasa a necesitar
# un mapeo por estación, no una constante global.
VARIABLE_TEMPERATURE_C = 42
VARIABLE_PRESSURE_HPA = 280
VARIABLE_HUMIDITY_PCT = 504
VARIABLE_PRECIPITATION_MM = 732
VARIABLE_WIND_SPEED_KMH = 1213
VARIABLE_WIND_DIRECTION_DEG = 1591


class OhmcClientError(Exception):
    """Cualquier falla de login o de consulta de mediciones."""


@dataclass
class _CachedToken:
    value: str
    expires_at: float  # epoch seconds


def _decode_jwt_exp(token: str) -> float | None:
    """Lee el claim `exp` del JWT sin verificar la firma -- solo para saber
    cuándo conviene renovarlo, la firma la valida el propio servidor en cada
    request. Devuelve None si no se puede decodificar (no bloquea el login)."""
    try:
        payload_b64 = token.split(".")[1]
        padding = "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + padding))
        return float(payload["exp"])
    except (IndexError, ValueError, KeyError, TypeError):
        return None


class OhmcClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._token: _CachedToken | None = None

    def _login(self) -> _CachedToken:
        try:
            response = requests.post(
                f"{self._settings.ohmc_base_url}/auth/login",
                json={"email": self._settings.ohmc_email, "password": self._settings.ohmc_password},
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=self._settings.request_timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError) as error:
            raise OhmcClientError(f"Login al OHMC falló: {error}") from error

        token = body.get("access_token")
        if not token:
            raise OhmcClientError(f"Respuesta de login sin 'access_token': {body!r}")

        exp = _decode_jwt_exp(token)
        # Si no se puede leer el exp, se asume una validez corta (1h) para no
        # arriesgarse a reusar un token vencido mucho tiempo sin darse cuenta.
        expires_at = exp if exp is not None else time.time() + 3600
        return _CachedToken(value=token, expires_at=expires_at)

    def _get_token(self) -> str:
        # Renueva 5 minutos antes de vencer, no justo al vencer.
        if self._token is None or time.time() > self._token.expires_at - 300:
            print("[OHMC] Token ausente o por vencer, autenticando...")
            self._token = self._login()
        return self._token.value

    def fetch_latest_reading(self) -> OmixomReading:
        """Un solo GET a /mediciones/ultimas trae todas las variables de la
        estación; acá se filtran las 6 que importan para env_metrics y se
        arma un único OmixomReading. Si el login vencido causa un 401, se
        reintenta una vez con un token nuevo (por si venció justo entre la
        última renovación y este request)."""
        for attempt in (1, 2):
            token = self._get_token()
            try:
                response = requests.get(
                    f"{self._settings.ohmc_base_url}/mediciones/ultimas",
                    params={"station_id": self._settings.ohmc_station_id},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=self._settings.request_timeout_seconds,
                )
                if response.status_code == 401 and attempt == 1:
                    print("[OHMC] 401 con el token cacheado, forzando re-login.")
                    self._token = None
                    continue
                response.raise_for_status()
                body = response.json()
                return _build_reading(body.get("data", []))
            except (requests.RequestException, ValueError, KeyError) as error:
                raise OhmcClientError(f"No se pudo consultar /mediciones/ultimas: {error}") from error
        raise OhmcClientError("No se pudo autenticar contra el OHMC tras reintentar el login.")


def _build_reading(rows: list[dict]) -> OmixomReading:
    by_variable = {row["variable_id"]: row for row in rows}

    def value_of(variable_id: int) -> float | None:
        row = by_variable.get(variable_id)
        return None if row is None else row.get("valor")

    # El timestamp de referencia es el de la temperatura (siempre presente en
    # las pruebas hechas) -- si en algún momento faltara, usar el más reciente
    # de cualquier variable disponible en vez de fallar del todo.
    reference_row = by_variable.get(VARIABLE_TEMPERATURE_C) or next(iter(by_variable.values()), None)
    if reference_row is None:
        raise OhmcClientError("La respuesta de /mediciones/ultimas no trajo ninguna variable.")

    measured_at = datetime.fromisoformat(reference_row["valida_en"].replace("Z", "+00:00"))
    measured_at = measured_at.astimezone(timezone.utc)

    wind_direction = value_of(VARIABLE_WIND_DIRECTION_DEG)

    return OmixomReading(
        measured_at=measured_at,
        temperature_c=value_of(VARIABLE_TEMPERATURE_C),
        humidity_pct=value_of(VARIABLE_HUMIDITY_PCT),
        pressure_hpa=value_of(VARIABLE_PRESSURE_HPA),
        precipitation_mm=value_of(VARIABLE_PRECIPITATION_MM),
        wind_speed_kmh=value_of(VARIABLE_WIND_SPEED_KMH),
        wind_direction_deg=None if wind_direction is None else int(wind_direction),
    )
