# Stack meteorológico — ejecución y validación

Este directorio contiene la infraestructura necesaria para ejecutar el subsistema meteorológico de la estación StarlinkPI.

El stack integra:

- Mosquitto como broker MQTT.
- Integrador OHMC para obtener datos meteorológicos reales.
- Consumer MQTT para validar y persistir las mediciones.
- PostgreSQL + TimescaleDB para almacenamiento histórico.
- Grafana para visualización de series temporales.

Actualmente se encuentra validado el flujo:

```text
API OHMC
   │
   ▼
api_omixom
   │
   │ MQTT
   ▼
Mosquitto
   │
   ▼
meteo_consumer
   │
   ▼
TimescaleDB
   │
   ▼
Grafana
```

## 1. Estado actual

El stack permite almacenar y visualizar datos meteorológicos provenientes de la estación OHMC del Laboratorio de Hidráulica de la UNC.

Variables actualmente integradas:

- Temperatura.
- Humedad relativa.
- Presión atmosférica.
- Precipitación.
- Velocidad del viento.
- Dirección del viento.

El dashboard Grafana `Datos Ambientales` visualiza actualmente:

- Temperatura.
- Humedad relativa.
- Presión atmosférica.
- Precipitación.

La integración con el sensor físico BME280/ESP32 y con el sensor local de lluvia MH-RD se valida por separado y no es necesaria para ejecutar este stack con OHMC.

> El MH-RD no debe interpretarse directamente como un pluviómetro en milímetros. La precipitación cuantitativa almacenada actualmente en `precipitation_mm` proviene de OHMC.

---

## 2. Requisitos

Se requiere:

- Linux o un sistema compatible con Docker.
- Docker Engine.
- Docker Compose v2.
- Acceso a Internet.
- Credenciales válidas para la API OHMC.

Puertos utilizados en el host:

| Servicio | Puerto |
|---|---:|
| Mosquitto MQTT | `1883` |
| Grafana | `3001` |

TimescaleDB se utiliza únicamente dentro de la red Docker del stack y no expone su puerto PostgreSQL al host.

---

## 3. Configuración de OHMC

Las credenciales no se almacenan en Git.

Crear el archivo local:

```bash
cp services/api_omixom/.env.example \
   services/api_omixom/.env
```

Editar:

```bash
nano services/api_omixom/.env
```

Completar como mínimo:

```dotenv
OHMC_EMAIL=<usuario>
OHMC_PASSWORD=<contraseña>
```

La configuración utilizada actualmente es:

```dotenv
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_QOS=1
MQTT_KEEPALIVE_SECONDS=60
MQTT_CONNECT_TIMEOUT_SECONDS=10

NODE_ID=lit-cordoba-01
SCHEMA_VERSION=1.0
POLL_INTERVAL_SECONDS=900
REQUEST_TIMEOUT_SECONDS=15

OHMC_BASE_URL=https://estaciones-beta.ohmc.com.ar/api/v1
OHMC_EMAIL=
OHMC_PASSWORD=
OHMC_STATION_ID=89

WATCH_DIR=/data/reportes-omixom
SCAN_INTERVAL_SECONDS=300
```

Durante la ejecución mediante Docker Compose, `MQTT_HOST` es reemplazado automáticamente por:

```text
broker
```

porque los contenedores se comunican utilizando los nombres de servicio de la red interna de Docker.

El archivo:

```text
services/api_omixom/.env
```

está excluido del repositorio mediante `.gitignore` y nunca debe ser versionado.

---

## 4. Validar la configuración de Docker Compose

Desde la raíz del repositorio:

```bash
docker compose \
  -f infrastructure/meteo-db/docker-compose.yml \
  config --quiet
```

Si el comando no produce salida, la configuración de Compose es válida.

---

## 5. Levantar el stack

Desde la raíz del repositorio:

```bash
docker compose \
  -f infrastructure/meteo-db/docker-compose.yml \
  up -d --build
```

Docker Compose debe levantar los siguientes servicios:

```text
broker
meteo_db
meteo_consumer
api_omixom
grafana
```

Comprobar el estado:

```bash
docker compose \
  -f infrastructure/meteo-db/docker-compose.yml \
  ps
```

Se espera que:

- `broker` esté `Up`.
- `api_omixom` esté `Up`.
- `meteo_consumer` esté `Up`.
- `grafana` esté `Up`.
- `meteo_db` esté `Up` y `healthy`.

---

## 6. Verificar la integración OHMC → MQTT

Consultar los logs del integrador:

```bash
docker compose \
  -f infrastructure/meteo-db/docker-compose.yml \
  logs --tail 40 api_omixom
```

Una ejecución correcta debe mostrar mensajes equivalentes a:

```text
[CONFIG] Broker: broker:1883
[CONFIG] Tópico: meteo/external/lit-cordoba-01
[CONFIG] Estación OHMC: station_id=89 (Lab. Hidráulica-UNC)
[MQTT] Conectando a broker:1883...
[MQTT] Conectado al broker.
[OHMC] Token ausente o por vencer, autenticando...
[OHMC] Publicado (...) → meteo/external/lit-cordoba-01
```

El integrador realiza consultas periódicas con un intervalo configurable mediante:

```dotenv
POLL_INTERVAL_SECONDS=900
```

El valor por defecto corresponde a 15 minutos.

---

## 7. Verificar los datos almacenados

Las mediciones ambientales se almacenan en la hypertable:

```text
env_metrics
```

Consultar las últimas mediciones de OHMC:

```bash
docker compose \
  -f infrastructure/meteo-db/docker-compose.yml \
  exec -T meteo_db \
  psql -U meteo_app -d meteo_data -c "
SELECT
    time,
    node_id,
    source,
    producer,
    temperature_c,
    humidity_pct,
    pressure_hpa,
    precipitation_mm,
    wind_speed_kmh,
    wind_direction_deg
FROM env_metrics
WHERE producer = 'ohmc'
ORDER BY time DESC
LIMIT 10;
"
```

Para los datos provenientes de OHMC se espera:

```text
source   = real
producer = ohmc
node_id  = lit-cordoba-01
```

La tabla puede contener valores nulos en variables que una fuente meteorológica determinada no proporcione.

---

## 8. Visualización en Grafana

Grafana se encuentra disponible en:

```text
http://localhost:3001
```

Credenciales de desarrollo por defecto:

```text
Usuario:    admin
Contraseña: grafana_dev_password
```

Estas credenciales son únicamente valores por defecto para el entorno local y deben modificarse para un despliegue definitivo.

El datasource:

```text
Meteo TimescaleDB
```

es provisionado automáticamente y se conecta a `meteo_db` mediante la red interna de Docker.

El dashboard:

```text
Datos Ambientales
```

también se provisiona automáticamente desde:

```text
infrastructure/grafana/provisioning/dashboards/json/meteo-overview.json
```

Actualmente contiene cuatro paneles:

1. Temperatura.
2. Humedad relativa.
3. Presión atmosférica.
4. Precipitación.

Cada productor meteorológico se representa como una serie independiente cuando existen datos disponibles.

---

## 9. Contrato MQTT ambiental

Los datos meteorológicos utilizan los tópicos:

```text
meteo/sensor/<node_id>
meteo/external/<node_id>
meteo/status/<node_id>
```

Para este nodo:

```text
node_id = lit-cordoba-01
```

Ejemplos:

```text
meteo/sensor/lit-cordoba-01
meteo/external/lit-cordoba-01
meteo/status/lit-cordoba-01
```

El contrato distingue dos conceptos:

```text
source
```

indica la naturaleza del dato:

```text
real
mock
```

mientras que:

```text
producer
```

identifica su origen concreto, por ejemplo:

```text
bme280
open_meteo
ohmc
```

Esto permite incorporar nuevas fuentes sin modificar la semántica general del contrato.

---

## 10. Detener el stack

Para detener y eliminar los contenedores manteniendo los datos:

```bash
docker compose \
  -f infrastructure/meteo-db/docker-compose.yml \
  down
```

Los datos almacenados en TimescaleDB y Grafana permanecen en volúmenes Docker.

Para volver a levantar el entorno:

```bash
docker compose \
  -f infrastructure/meteo-db/docker-compose.yml \
  up -d --build
```

### Atención: eliminación completa de datos

El siguiente comando también elimina los volúmenes:

```bash
docker compose \
  -f infrastructure/meteo-db/docker-compose.yml \
  down -v
```

Debe utilizarse únicamente cuando se desea reinicializar completamente las bases de datos y la configuración persistente de Grafana.

---

## 11. Prueba de reproducibilidad realizada

El stack fue validado realizando el siguiente procedimiento:

```text
docker compose down
        │
        ▼
docker compose up -d --build
        │
        ├── Mosquitto iniciado
        ├── TimescaleDB healthy
        ├── Consumer iniciado
        ├── Integrador OHMC iniciado
        └── Grafana iniciado
```

Después del arranque:

1. `api_omixom` autenticó automáticamente contra OHMC.
2. Se conectó a `broker:1883`.
3. Publicó una medición en `meteo/external/lit-cordoba-01`.
4. `meteo_consumer` procesó el mensaje.
5. La medición fue persistida en `env_metrics`.
6. Los datos históricos anteriores permanecieron almacenados.
7. Grafana recuperó el datasource y el dashboard provisionados.

Esto permite reproducir el pipeline meteorológico sin iniciar manualmente procesos Python.

---

## 12. Troubleshooting

### El servicio `api_omixom` no inicia

Comprobar que exista:

```text
services/api_omixom/.env
```

y que contenga credenciales OHMC válidas.

Consultar:

```bash
docker compose \
  -f infrastructure/meteo-db/docker-compose.yml \
  logs api_omixom
```

---

### OHMC no se conecta al broker

Dentro de Docker el broker debe ser:

```text
broker:1883
```

No debe utilizarse `localhost`, ya que dentro del contenedor `localhost` hace referencia al propio contenedor.

---

### Grafana no muestra datos

Comprobar primero que existan registros:

```bash
docker compose \
  -f infrastructure/meteo-db/docker-compose.yml \
  exec -T meteo_db \
  psql -U meteo_app -d meteo_data -c "
SELECT time, producer, temperature_c
FROM env_metrics
ORDER BY time DESC
LIMIT 10;
"
```

Después comprobar el datasource `Meteo TimescaleDB` desde Grafana.

---

### El dashboard no refleja un cambio realizado en el JSON

Reiniciar Grafana:

```bash
docker compose \
  -f infrastructure/meteo-db/docker-compose.yml \
  restart grafana
```

y actualizar el navegador.

---

## 13. Componentes pendientes de integración física

El stack descripto en este documento permite ejecutar completamente la adquisición meteorológica mediante OHMC.

Quedan como tareas independientes de validación física:

- ESP32 + BME280.
- Publicación del BME280 real mediante MQTT.
- Sensor local de lluvia MH-RD.
- Validación del comportamiento del sensor de lluvia.
- Integración conjunta con el dominio Starlink.
- Dashboard temporal conjunto entre métricas meteorológicas y métricas de red.

Estas tareas no impiden reproducir ni validar el pipeline OHMC → MQTT → TimescaleDB → Grafana documentado aquí.
