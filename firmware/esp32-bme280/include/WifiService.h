#pragma once

#include <Arduino.h>

class WifiService {
 public:
  void begin();
  void loop();
  bool connected() const;

 private:
  void attemptConnection();
  void scheduleNextAttempt();
  void resetBackoff();

  uint32_t backoffMs_ = 0;
  uint32_t nextAttemptAtMs_ = 0;
  bool wasConnected_ = false;
  bool attemptInProgress_ = false;
  uint32_t attemptStartedAtMs_ = 0;
};
