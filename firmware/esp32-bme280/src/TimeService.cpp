#include "TimeService.h"

#include <ctime>

#include "AppConfig.h"

void TimeService::loop(bool networkAvailable) {
  if (networkAvailable && !ntpStarted_) {
    // UTC: desplazamiento y horario de verano en cero.
    configTime(0, 0, AppConfig::NTP_SERVER);
    ntpStarted_ = true;
    Serial.println("[Tiempo] Sincronización NTP iniciada.");
  }
}

bool TimeService::synchronized() const {
  // Evita considerar válida la fecha por defecto de un ESP32 recién iniciado.
  return std::time(nullptr) > 1'700'000'000;
}

String TimeService::nowIso8601() const {
  if (!synchronized()) {
    return "";
  }

  const std::time_t now = std::time(nullptr);
  std::tm utcTime{};
  gmtime_r(&now, &utcTime);

  char buffer[25]{};
  std::strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &utcTime);
  return String(buffer);
}
