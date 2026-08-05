# Starter del módulo ambiental de la tesis

## Qué se carga en la placa

Solamente el contenido de `firmware/esp32-bme280` se compila como firmware y se sube al ESP32.

## Qué corre en la PC o Raspberry Pi

`infrastructure/mosquitto` levanta el broker Mosquitto mediante Docker. No se carga en la placa.

## Preparación

1. Abrir `firmware/esp32-bme280` como proyecto PlatformIO.
2. Copiar `include/Secrets.example.h` como `include/Secrets.h`.
3. Completar Wi-Fi en `Secrets.h`.
4. Cambiar `MQTT_HOST` en `include/AppConfig.h` por la IP LAN de la PC/RPi.
5. Confirmar el modelo real de ESP32 y los pines SDA/SCL.

## Levantar Mosquitto

```bash
cd infrastructure/mosquitto
docker compose up -d
docker compose logs -f
```

## Probar el broker sin ESP32

Terminal 1:

```bash
./scripts/mqtt-subscribe.sh
```

Terminal 2:

```bash
./scripts/mqtt-publish-test.sh
```

## Compilar y cargar

Desde PlatformIO:

- Build: icono de tilde.
- Upload: icono de flecha.
- Serial Monitor: icono de enchufe/monitor, a 115200 baud.

## Contrato pendiente

El payload `envelope + metrics` está aislado en `src/PayloadBuilder.cpp`. Es provisional hasta confirmar con Aldana el ADR-01 actualizado.

El tópico de estado se conserva como `system/status/<node_id>`, tal como indicó Aldana. Queda pendiente decidir si necesitará un sufijo de componente para evitar que diferentes productores sobrescriban el mismo mensaje retained.
