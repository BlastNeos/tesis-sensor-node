#include "WifiService.h"

#include <WiFi.h>

#include "AppConfig.h"
#include "Secrets.h"

void WifiService::begin() {
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(false);  // La reconexión la controlamos nosotros.
  resetBackoff();
  attemptConnection();
}

void WifiService::loop() {
  const bool isConnected = connected();

  if (isConnected && !wasConnected_) {
    Serial.printf("[WiFi] Conectado. IP del ESP32: %s\n",
                  WiFi.localIP().toString().c_str());
    attemptInProgress_ = false;
    resetBackoff();
  } else if (!isConnected && wasConnected_) {
    Serial.println("[WiFi] Se perdió la conexión.");
    attemptInProgress_ = false;
    scheduleNextAttempt();
  }

  wasConnected_ = isConnected;

  if (isConnected) {
    return;
  }

  // WiFi.begin() necesita tiempo. No debemos cancelar y reiniciar el intento
  // cada segundo mientras el ESP32 todavía está negociando con el router.
  if (attemptInProgress_) {
    const bool timedOut =
        millis() - attemptStartedAtMs_ >= AppConfig::WIFI_CONNECT_TIMEOUT_MS;
    if (!timedOut) {
      return;
    }

    Serial.println("[WiFi] El intento agotó el tiempo de espera.");
    WiFi.disconnect(false, false);
    attemptInProgress_ = false;
    scheduleNextAttempt();
  }

  if (millis() >= nextAttemptAtMs_) {
    attemptConnection();
  }
}

bool WifiService::connected() const {
  return WiFi.status() == WL_CONNECTED;
}

void WifiService::attemptConnection() {
  Serial.printf("[WiFi] Intentando conectar a %s...\n", Secrets::WIFI_SSID);
  WiFi.begin(Secrets::WIFI_SSID, Secrets::WIFI_PASSWORD);
  attemptInProgress_ = true;
  attemptStartedAtMs_ = millis();
}

void WifiService::scheduleNextAttempt() {
  if (backoffMs_ == 0) {
    backoffMs_ = AppConfig::BACKOFF_INITIAL_MS;
  }

  // Pequeño jitter para que varios dispositivos no reintenten al mismo tiempo.
  const uint32_t jitterMs = static_cast<uint32_t>(random(0, 500));
  nextAttemptAtMs_ = millis() + backoffMs_ + jitterMs;
  backoffMs_ = min(backoffMs_ * 2, AppConfig::BACKOFF_MAX_MS);
}

void WifiService::resetBackoff() {
  backoffMs_ = AppConfig::BACKOFF_INITIAL_MS;
  nextAttemptAtMs_ = millis();
}
