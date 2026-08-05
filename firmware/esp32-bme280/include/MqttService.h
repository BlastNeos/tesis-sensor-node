#pragma once

#include <Arduino.h>
#include <MQTT.h>
#include <WiFi.h>

class MqttService {
 public:
  void begin(const String& lastWillPayload);
  void loop(bool networkAvailable, const String& timestampIso8601);

  bool connected() const;
  bool publishMeasurement(const String& payload);

 private:
  void attemptConnection(const String& timestampIso8601);
  void publishStatus(const char* status, const String& timestampIso8601);
  void scheduleNextAttempt();
  void resetBackoff();

  WiFiClient networkClient_;
  MQTTClient mqttClient_{512, 128};

  String sensorTopic_;
  String statusTopic_;

  uint32_t backoffMs_ = 0;
  uint32_t nextAttemptAtMs_ = 0;
  uint32_t lastHeartbeatAtMs_ = 0;
};
