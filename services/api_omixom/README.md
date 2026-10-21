# Integrador de clima externo — Omixom / OHMC (Laboratorio de Hidráulica-UNC)

Cumple RF-11/RF-14 (`docs/03_SRS.md` de `starlink-measurement-station`) — estación
más cercana al LIT investigada hasta ahora (misma facultad, FCEFyN/UNC). Publica
en `meteo/external/<node_id>`.

## ✅ Camino A (el implementado y probado, 12/9/2026) — API real del OHMC

La plataforma web de Omixom (`new.omixom.com`) no tiene API pública, pero el
**Observatorio Hidrometeorológico de Córdoba (OHMC)** sí — es una plataforma
**distinta** (`estaciones-beta.ohmc.com.ar`), con **cuenta separada** (no la
misma de Omixom), que expone la misma red de estaciones (incluida la del
Laboratorio de Hidráulica) vía REST con token.

- **Estación confirmada**: `station_id=89`, `"APRHi - Lab. Hidraulica-UNC"`.
- **Endpoint usado**: `GET /mediciones/ultimas?station_id=89` — última lectura
  de todas las variables en un solo call, ideal para el poll de 15 min de RF-11.
- **Variables mapeadas** (de las 25 que reporta la estación, confirmadas contra
  `GET /variables?station_id=89`):

  | `variable_id` | Nombre real | → campo de `env_metrics` |
  | --- | --- | --- |
  | 42 | Temperatura @2m | `temperature_c` |
  | 280 | Presión Atmosférica | `pressure_hpa` |
  | 504 | Humedad Relativa | `humidity_pct` |
  | 732 | Precipitacion | `precipitation_mm` |
  | 1213 | Velocidad del Viento Media @2m | `wind_speed_kmh` |
  | 1591 | Direccion del Viento @2m | `wind_direction_deg` |

  El resto (radiación solar, batería, índices de incendio, punto de rocío,
  ráfagas) no tiene lugar hoy en `env_metrics` — quedan sin usar, no perdidos
  (siguen en la respuesta cruda de la API si en algún momento se quieren sumar).
  `cloud_cover_pct` queda `null` — la estación no reporta nubosidad.

- **Cómo conseguir las credenciales** (son de la cuenta OHMC, no la de Omixom):
  1. Registrarse en `https://estaciones-beta.ohmc.com.ar/panel/login` (cuenta
     nueva, propia de esta plataforma).
  2. `OHMC_EMAIL`/`OHMC_PASSWORD` en el `.env` (nunca commiteados).
  3. El cliente (`src/ohmc_client.py`) hace login solo, cachea el token (JWT,
     dura unos días) y lo renueva automáticamente antes de vencer — no hay
     nada manual que rotar en producción.

**Probado en vivo el 12/9/2026** (no solo con mocks): login real + lectura real
de la estación, valores plausibles (~6°C, 90% humedad, sin lluvia — una mañana
fría de invierno en Córdoba).

## Camino B (fallback/histórico) — Reportes por mail

Sigue existiendo (`src/main_reports.py`, `src/report_ingestor.py`) para el caso
de necesitar backfillear un rango de fechas viejo que valga la pena traer de un
reporte exportado a mano, en vez de la API. No es la vía principal desde que se
confirmó el Camino A — correr con `python -m src.main_reports` en vez de
`python -m src.main` si hace falta.

## Correr localmente

```bash
cp .env.example .env   # completar OHMC_EMAIL/OHMC_PASSWORD
pip install -r requirements.txt
python -m pytest tests/ -v      # 14 tests
python -m src.main              # Camino A -- poll cada 15 min a la API real
```

## Docker

```bash
docker build -t api-omixom .
docker run --env-file .env api-omixom
```
