# AutoBot ESP32 + DRV8833 Firmware

Arduino firmware for the AutoBot mecanum-wheel rover using an **ESP32-WROOM-32 / classic ESP32 DevKit** and two DRV8833 dual H-bridge motor-driver boards. This version does not use the Raspberry Pi Zero WH or pan/tilt servos. The Raspberry Pi 5 can send autonomous movement commands over UART. Bluetooth Classic is available for manual commands.

## Files

- `AutoBot_ESP32_DRV8833_WakePins32_33.ino` — firmware sketch.
- `README_AutoBot_ESP32_DRV8833.md` — this guide.

## 1. Arduino IDE setup

1. Install the Espressif **ESP32** board package in Arduino IDE's Boards Manager.
2. Open the `.ino` sketch.
3. Select **ESP32 Dev Module** (for an ESP32-WROOM-32 board).
4. Select the correct USB/COM port.
5. Upload the sketch.
6. Open Serial Monitor at **115200 baud**.

The sketch uses `BluetoothSerial`, which requires a classic ESP32 with Bluetooth Classic support. It is not compatible with ESP32 variants that only support Bluetooth Low Energy, such as ESP32-C3/S3 in typical configurations.

## 2. Motor and wake-pin wiring

### DRV8833 wake pins

| ESP32 pin | Connect to |
|---|---|
| GPIO 32 | Driver 1 `nSLEEP` / `SLP` |
| GPIO 33 | Driver 2 `nSLEEP` / `SLP` |
| GND | GND on both driver boards and motor supply negative |

At startup, the sketch configures GPIO 32 and GPIO 33 as outputs and drives both HIGH to wake the drivers. Check the exact breakout-board pin labels/schematic first. If a board already ties `nSLEEP` high, follow that board's documentation and avoid conflicting wiring.

### Motor inputs

The sketch currently assigns the motor input pins as follows. Each motor's two inputs must go to one DRV8833 H-bridge channel. Confirm the physical wheel-to-channel mapping before applying motor power.

| Motor | ESP32 input 1 | ESP32 input 2 |
|---|---:|---:|
| M1 (front-left) | GPIO 25 | GPIO 26 |
| M2 (front-right) | GPIO 27 | GPIO 14 |
| M3 (rear-left) | GPIO 18 | GPIO 19 |
| M4 (rear-right) | GPIO 23 | GPIO 22 |

### Motor supply and common ground

- Connect the motor battery positive to each driver's `VM` / motor-supply input, and battery negative to driver GND.
- Connect ESP32 GND, both driver grounds, and Raspberry Pi 5 GND together when UART is connected.
- Do **not** power motors from ESP32 GPIO pins or the ESP32 3.3 V output.
- The DRV8833 IC motor-supply range is typically 2.7–10.8 V; check your specific breakout's ratings and wiring. A nominal 2-cell LiPo is 7.4 V and reaches 8.4 V when fully charged, within the IC's range, but check the battery and board specifications.

## 3. Raspberry Pi 5 UART wiring

| ESP32 | Raspberry Pi 5 |
|---|---|
| GPIO 16 (UART RX2) | Pi TX |
| GPIO 17 (UART TX2) | Pi RX |
| GND | GND |

UART baud rate is **115200**. Use the correct Pi UART pins and logic-level wiring; do not connect a 5 V UART signal to the ESP32.

## 4. Bluetooth

The Bluetooth Classic device name is **`AutoBot-ESP32`**. Pair/connect from the controller app or a compatible Bluetooth Classic terminal. Commands must end with a newline (`\n`).

The firmware starts in **MANUAL** mode: Bluetooth movement commands are accepted and ordinary UART movement commands are ignored. Send `MODE AUTO` over Bluetooth to switch to AUTO mode, where UART movement commands are accepted and Bluetooth movement commands are ignored. `STOP` is accepted from either source in either mode.

## 5. Supported commands

Commands are case-insensitive. Values are expected between `-1.0` and `1.0`; motor throttle values are clamped to that range.

| Command | Purpose | Example |
|---|---|---|
| `MOVE m1 m2 m3 m4` | Set each motor throttle independently | `MOVE 0.5 0.5 0.5 0.5` |
| `MECANUM vx vy w` | Mecanum movement mix: forward/back, lateral, rotation | `MECANUM 0.5 0 0` |
| `TURN_LEFT speed` | Rotate left using the firmware's motor mix | `TURN_LEFT 0.3` |
| `TURN_RIGHT speed` | Rotate right using the firmware's motor mix | `TURN_RIGHT 0.3` |
| `STOP` | Stop all motors (coast) | `STOP` |
| `MODE MANUAL` | Enable Bluetooth movement control | `MODE MANUAL` |
| `MODE AUTO` | Enable Pi 5 UART movement control | `MODE AUTO` |

For `MECANUM`, `vx`, `vy`, and `w` are normalized command values, not physical units (m/s or rad/s). The exact direction depends on motor mounting, wheel orientation and wiring; verify and adjust the mixing or motor signs after testing.

## 6. Safe first test

1. Turn the robot off before changing wiring.
2. Raise the chassis so all wheels are clear of the floor. Secure the robot so it cannot fall.
3. Verify GPIO assignments, motor-driver outputs, `nSLEEP` wiring, battery polarity and common ground.
4. Power the ESP32 and motor drivers. Check Serial Monitor for startup messages, including the wake-pin message.
5. Test one motor at low throttle with `MOVE`, then test `STOP`. Confirm wheel direction before testing the full chassis.
6. If a motor does not move, measure motor supply at `VM`, check that each `nSLEEP` pin is HIGH, confirm the selected GPIOs match the wiring, and verify the command appears in Serial Monitor.

**Safety:** Keep hands, cables and clothing away from wheels. Disconnect the motor battery before rewiring. A software `STOP` is not a substitute for a physical power disconnect or emergency stop.

## 7. Troubleshooting

- **Bluetooth connects but motors do not move:** Check `VM`, common GND, the `nSLEEP` pins, motor outputs, GPIO mapping and whether the correct mode is active.
- **Bluetooth command is ignored:** Check the Serial Monitor. In AUTO mode, movement commands from Bluetooth are intentionally ignored; use `MODE MANUAL` to return to manual control.
- **Pi UART command is ignored:** Send `MODE AUTO` over Bluetooth first. Check GPIO 16/17 crossover, common GND, baud rate and newline termination.
- **Wheel direction is wrong:** Swap that motor's two output wires or invert that motor's command sign in the firmware.
- **Robot moves unexpectedly or resets:** Stop testing and check for shorts, motor-current/power-supply issues, loose grounds and voltage dips.

## 8. Important configuration note

The motor pin mapping and mecanum mixing equations are starting points. Verify them against the actual wiring and wheel orientation. Make changes with motor power disconnected, then test at low speed with the wheels raised.
