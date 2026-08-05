#pragma once

#include <Arduino.h>

namespace AppConfig {

// Identifica la instalación completa, no solamente el sensor.
inline constexpr char NODE_ID[] = "lit-cordoba-01";

// Identifica este sensor físico dentro del nodo.
inline constexpr char SENSOR_UID[] = "bme280-01";

// Identifica al programa MQTT que corre en el ESP32.
inline constexpr char MQTT_CLIENT_ID[] = "esp32-bme280-lit-cordoba-01";

// Durante el desarrollo debe ser la IP LAN de la PC donde corre Mosquitto.
// No usar "localhost": para el ESP32, localhost es el propio ESP32.
inline constexpr char MQTT_HOST[] = "192.168.1.10";
inline constexpr uint16_t MQTT_PORT = 1883;

// Contrato MQTT actual. El payload está centralizado en PayloadBuilder.cpp
// para poder modificarlo fácilmente cuando el equipo congele el esquema.
inline constexpr char SENSOR_TOPIC_PREFIX[] = "meteo/sensor/";
inline constexpr char STATUS_TOPIC_PREFIX[] = "system/status/";

// El SRS define 60 segundos por defecto.
inline constexpr uint32_t SAMPLE_INTERVAL_MS = 60'000;
inline constexpr uint32_t HEARTBEAT_INTERVAL_MS = 30'000;

// Pines habituales en un ESP32 DevKit clásico. Confirmar para la placa real.
inline constexpr int I2C_SDA_PIN = 21;
inline constexpr int I2C_SCL_PIN = 22;
inline constexpr uint8_t BME280_ADDRESS_PRIMARY = 0x76;
inline constexpr uint8_t BME280_ADDRESS_SECONDARY = 0x77;

inline constexpr char NTP_SERVER[] = "pool.ntp.org";

// Backoff: 1, 2, 4, 8, 16 y luego máximo 30 segundos.
inline constexpr uint32_t BACKOFF_INITIAL_MS = 1'000;
inline constexpr uint32_t BACKOFF_MAX_MS = 30'000;
inline constexpr uint32_t WIFI_CONNECT_TIMEOUT_MS = 15'000;

}  // namespace AppConfig
