#pragma once

#include <Arduino.h>
#include <MQTT.h>
#include <WiFi.h>

class MqttService {
 public:
  void begin(const String& lastWillPayload);
  void loop(bool networkAvailable);

  bool connected();
  bool publishMeasurement(const String& payload);

 private:
  void attemptConnection();
  void publishStatus(const char* status);
  void scheduleNextAttempt();
  void resetBackoff();

  WiFiClient networkClient_;
  MQTTClient mqttClient_{512, 512};

  String sensorTopic_;
  String statusTopic_;

  uint32_t backoffMs_ = 0;
  uint32_t nextAttemptAtMs_ = 0;
  uint32_t lastHeartbeatAtMs_ = 0;
};
