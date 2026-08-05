#pragma once

// Copiar este archivo como Secrets.h y completar los valores.
// Secrets.h está ignorado por Git para no subir credenciales.
namespace Secrets {
inline constexpr char WIFI_SSID[] = "NOMBRE_DE_TU_WIFI";
inline constexpr char WIFI_PASSWORD[] = "CLAVE_DE_TU_WIFI";

// En el Mosquitto local de desarrollo se permite acceso anónimo,
// por eso estos campos pueden quedar vacíos al principio.
inline constexpr char MQTT_USERNAME[] = "";
inline constexpr char MQTT_PASSWORD[] = "";
}  // namespace Secrets
