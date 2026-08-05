#pragma once

#include <Arduino.h>

class TimeService {
 public:
  void loop(bool networkAvailable);
  bool synchronized() const;
  String nowIso8601() const;

 private:
  bool ntpStarted_ = false;
};
