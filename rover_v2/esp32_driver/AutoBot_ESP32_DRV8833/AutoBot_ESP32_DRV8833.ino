/*
  AutoBot ESP32-WROOM-32 controller
  Direct GPIO control of two DRV8833 motor driver boards.
  No pan/tilt camera or PCA9685 servo driver is used.

  Arduino IDE board: "ESP32 Dev Module" (ESP32-WROOM-32)
  Serial Monitor: 115200 baud

  GPIO map (change to match your wiring):
    Motor 1 (front-left):  IN1=25, IN2=26
    Motor 2 (front-right): IN1=27, IN2=14
    Motor 3 (rear-left):   IN1=18, IN2=19
    Motor 4 (rear-right):  IN1=23, IN2=22

  Raspberry Pi 5 UART2 link:
    ESP32 GPIO16 (RX2) <- Pi 5 TX
    ESP32 GPIO17 (TX2) -> Pi 5 RX
    GND <-> GND
    UART baud: 115200

  Bluetooth Classic device name: AutoBot-ESP32
  Bluetooth and UART commands must end with newline:
    MOVE m1 m2 m3 m4       values -1.0 to 1.0
    MECANUM vx vy w        values -1.0 to 1.0
    TURN_LEFT speed
    TURN_RIGHT speed
    STOP
    MODE MANUAL            Bluetooth only
    MODE AUTO              Bluetooth only

  Safety / wiring:
    - Connect each DRV8833 nSLEEP pin to 3.3V, unless your board already
      pulls it high. If nSLEEP is low, the driver is disabled.
    - Connect ESP32 GND, both driver grounds, and Pi 5 GND together.
    - Power motors from the motor supply into driver VM; do not power motors
      from ESP32 GPIO or its 3.3V pin.
    - Verify the GPIO map before connecting motor power. Motor numbering and
      forward direction may need to be adjusted for your chassis.
*/

#include <Arduino.h>
#include <BluetoothSerial.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error "Bluetooth Classic is unavailable. Select a classic ESP32-WROOM-32 board."
#endif

// ---------- Configuration ----------
static constexpr uint32_t USB_SERIAL_BAUD = 115200;
static constexpr uint32_t PI_UART_BAUD = 115200;
static constexpr int PI_UART_RX_PIN = 16;
static constexpr int PI_UART_TX_PIN = 17;
static constexpr size_t COMMAND_BUFFER_SIZE = 160;

// Motor order follows the original firmware's M1, M2, M3, M4.
// Edit these pins to match your wiring.
static constexpr uint8_t MOTOR_IN1[4] = {25, 27, 18, 23};
static constexpr uint8_t MOTOR_IN2[4] = {26, 14, 19, 22};

// ---------- Runtime state ----------
BluetoothSerial SerialBT;
HardwareSerial PiSerial(2);
bool manualMode = true; // Matches the original Python code's startup mode.

String btBuffer;
String uartBuffer;

float clampThrottle(float value) {
  if (value > 1.0f) return 1.0f;
  if (value < -1.0f) return -1.0f;
  return value;
}

// Set one H-bridge channel using direction + PWM on the DRV8833 inputs.
// Positive and negative directions are electrical conventions; reverse the
// two input wires or swap these outputs if a wheel spins the wrong way.
void setOneMotor(uint8_t index, float throttle) {
  if (index >= 4) return;

  throttle = clampThrottle(throttle);
  const int pwm = (int)(fabsf(throttle) * 255.0f + 0.5f);

  if (throttle > 0.0f) {
    analogWrite(MOTOR_IN1[index], pwm);
    analogWrite(MOTOR_IN2[index], 0);
  } else if (throttle < 0.0f) {
    analogWrite(MOTOR_IN1[index], 0);
    analogWrite(MOTOR_IN2[index], pwm);
  } else {
    // Coast / stop. For active braking, set both inputs HIGH if desired.
    analogWrite(MOTOR_IN1[index], 0);
    analogWrite(MOTOR_IN2[index], 0);
  }
}

void setMotorSpeeds(float m1, float m2, float m3, float m4) {
  const float speeds[4] = {
    clampThrottle(m1), clampThrottle(m2),
    clampThrottle(m3), clampThrottle(m4)
  };

  for (uint8_t i = 0; i < 4; ++i) {
    setOneMotor(i, speeds[i]);
  }

  Serial.printf("Motor throttle: M1=%.2f M2=%.2f M3=%.2f M4=%.2f\n",
                speeds[0], speeds[1], speeds[2], speeds[3]);
}

void stopAllMotors() {
  for (uint8_t i = 0; i < 4; ++i) {
    analogWrite(MOTOR_IN1[i], 0);
    analogWrite(MOTOR_IN2[i], 0);
  }
  Serial.println("All motors stopped.");
}

void processCommand(String rawCommand, const char *source) {
  rawCommand.trim();
  if (rawCommand.length() == 0) return;

  Serial.printf("[RECEIVED %s] %s\n", source, rawCommand.c_str());
  rawCommand.toUpperCase();

  char commandCopy[COMMAND_BUFFER_SIZE];
  rawCommand.toCharArray(commandCopy, sizeof(commandCopy));

  char *tokens[6] = {nullptr};
  uint8_t count = 0;
  char *savePtr = nullptr;
  char *token = strtok_r(commandCopy, " \t,", &savePtr);
  while (token != nullptr && count < 6) {
    tokens[count++] = token;
    token = strtok_r(nullptr, " \t,", &savePtr);
  }
  if (count == 0) return;

  const char *action = tokens[0];

  // Only Bluetooth may change operating mode, matching the original code.
  if (strcmp(action, "MODE") == 0) {
    if (strcmp(source, "BT") != 0) {
      Serial.println("WARNING: MODE commands are allowed only over Bluetooth.");
      return;
    }
    if (count != 2) {
      Serial.println("Usage: MODE MANUAL or MODE AUTO");
      return;
    }

    if (strcmp(tokens[1], "MANUAL") == 0) {
      manualMode = true;
      Serial.println("OPERATIONAL MODE: MANUAL (Bluetooth movement active)");
    } else if (strcmp(tokens[1], "AUTO") == 0) {
      manualMode = false;
      Serial.println("OPERATIONAL MODE: AUTO (Pi 5 UART movement active)");
    } else {
      Serial.println("ERROR: Use MODE MANUAL or MODE AUTO.");
    }
    return;
  }

  // STOP is accepted from either source regardless of operating mode.
  if (strcmp(action, "STOP") == 0) {
    stopAllMotors();
    return;
  }

  // Preserve the original command-source permissions.
  if (strcmp(source, "UART") == 0 && manualMode) {
    Serial.println("IGNORED UART: rover is in MANUAL mode.");
    return;
  }
  if (strcmp(source, "BT") == 0 && !manualMode) {
    Serial.println("IGNORED BT command: rover is in AUTO mode.");
    return;
  }

  if (strcmp(action, "MOVE") == 0 && count == 5) {
    setMotorSpeeds(atof(tokens[1]), atof(tokens[2]),
                   atof(tokens[3]), atof(tokens[4]));
  } else if (strcmp(action, "MECANUM") == 0 && count == 4) {
    float vx = atof(tokens[1]);
    float vy = atof(tokens[2]);
    float w  = atof(tokens[3]);

    // Same mecanum mixing equations as the Python implementation.
    float m1 = vx - vy - w;
    float m2 = vx + vy + w;
    float m3 = vx + vy - w;
    float m4 = vx - vy + w;

    // Normalize together so ratios are retained if a value exceeds +/-1.
    float maxAbs = fmaxf(fmaxf(fabsf(m1), fabsf(m2)),
                         fmaxf(fabsf(m3), fabsf(m4)));
    if (maxAbs > 1.0f) {
      m1 /= maxAbs;
      m2 /= maxAbs;
      m3 /= maxAbs;
      m4 /= maxAbs;
    }
    setMotorSpeeds(m1, m2, m3, m4);
  } else if (strcmp(action, "TURN_LEFT") == 0 && count == 2) {
    float speed = clampThrottle(atof(tokens[1]));
    setMotorSpeeds(-speed, speed, -speed, speed);
  } else if (strcmp(action, "TURN_RIGHT") == 0 && count == 2) {
    float speed = clampThrottle(atof(tokens[1]));
    setMotorSpeeds(speed, -speed, speed, -speed);
  } else {
    Serial.printf("WARNING: Unrecognized command from %s: %s\n",
                  source, rawCommand.c_str());
  }
}

// Process newline-terminated commands without blocking either input.
void readCommandStream(Stream &stream, String &buffer, const char *source) {
  while (stream.available() > 0) {
    const char c = (char)stream.read();
    if (c == '\r') continue;

    if (c == '\n') {
      processCommand(buffer, source);
      buffer = "";
    } else if (buffer.length() < COMMAND_BUFFER_SIZE - 1) {
      buffer += c;
    } else {
      buffer = "";
      Serial.printf("WARNING: Overlong command discarded from %s\n", source);
    }
  }
}

void setup() {
  Serial.begin(USB_SERIAL_BAUD);
  delay(400);
  Serial.println("\nAutoBot ESP32 DRV8833 controller starting...");

  // Configure all H-bridge inputs low before accepting commands.
  for (uint8_t i = 0; i < 4; ++i) {
    pinMode(MOTOR_IN1[i], OUTPUT);
    pinMode(MOTOR_IN2[i], OUTPUT);
    digitalWrite(MOTOR_IN1[i], LOW);
    digitalWrite(MOTOR_IN2[i], LOW);
    analogWrite(MOTOR_IN1[i], 0);
    analogWrite(MOTOR_IN2[i], 0);
  }

  PiSerial.begin(PI_UART_BAUD, SERIAL_8N1, PI_UART_RX_PIN, PI_UART_TX_PIN);
  Serial.printf("Pi 5 UART ready: %lu baud, ESP32 RX=%d TX=%d\n",
                (unsigned long)PI_UART_BAUD, PI_UART_RX_PIN, PI_UART_TX_PIN);

  if (SerialBT.begin("AutoBot-ESP32")) {
    Serial.println("Bluetooth Classic ready: AutoBot-ESP32");
  } else {
    Serial.println("WARNING: Bluetooth Classic failed to start.");
  }

  Serial.println("Default mode: MANUAL");
  Serial.println("Ready. Send commands terminated by newline.");
}

void loop() {
  readCommandStream(SerialBT, btBuffer, "BT");
  readCommandStream(PiSerial, uartBuffer, "UART");
  delay(2);
}
