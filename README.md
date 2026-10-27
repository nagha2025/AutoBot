# AutoBot Wiring and Architecture

## 1. Overview

AutoBot is a mecanum-wheel autonomous ground rover. The Raspberry Pi 5 is the high-level computer running Ubuntu 24.04 and ROS 2 Jazzy. An ESP32-WROOM-32 DevKit replaces the Raspberry Pi Zero WH and handles low-level motor control and Bluetooth commands.

The Intel RealSense D421 depth camera is mounted rigidly to the chassis and connects directly to the Raspberry Pi 5 by USB. There is no pan-tilt mechanism, pan/tilt servo driver, or servo wiring.

## 2. Main components

- **Raspberry Pi 5** — ROS 2 Jazzy, sensor drivers, odometry/TF, SLAM and high-level autonomy.
- **ESP32-WROOM-32 DevKit** — motor control, PWM/direction outputs and Bluetooth command handling.
- **Two OPEN-SMART DRV8833 boards** — one board for the two left motors and one for the two right motors, subject to confirmation that each board's current rating is adequate for the motors.
- **Four mecanum DC gearmotors** — front-left, rear-left, front-right and rear-right.
- **Intel RealSense D421** — fixed depth camera, USB to Pi 5.
- **RPLidar C1** — USB to Pi 5.
- **BNO085 IMU** — I²C to Pi 5.
- **Two 7.4 V LiPo batteries** — one for electronics and one for motor power, as proposed.
- **Regulated DC-DC converters** — provide the required regulated logic/computer supply rails.

## 3. Data and control architecture
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/12c7f195-e476-41ac-98da-206a9d18393e" />



The Pi 5 handles perception, mapping and high-level decisions. The ESP32 receives movement commands over UART (and optionally Bluetooth) and drives the motor-driver inputs. The ESP32 is not a replacement for the Pi 5's ROS 2 computer; it is the low-level controller.

## 4. Proposed signal connections

These are **proposed pin assignments**, not a verified pinout for every ESP32 DevKit or OPEN-SMART board. Confirm the board silkscreen and firmware before wiring.

### Pi 5 ↔ ESP32 UART

| Signal | Raspberry Pi 5 | ESP32-WROOM-32 |
|---|---|---|
| Pi TX → ESP RX | GPIO14 / UART TX (physical pin 8, if using the default UART mapping) | GPIO16 (RX2) |
| Pi RX ← ESP TX | GPIO15 / UART RX (physical pin 10, if using the default UART mapping) | GPIO17 (TX2) |
| Ground | GND | GND |

Use 3.3 V UART logic. Cross TX to RX and RX to TX. Do not connect a 5 V UART signal to an ESP32 GPIO. Configure the Pi's UART and ensure the selected UART is not being used by a login console.

### BNO085 → Pi 5 I²C

| BNO085 breakout | Raspberry Pi 5 |
|---|---|
| VIN/VCC | 3.3 V only if supported by the specific breakout |
| GND | GND |
| SDA | GPIO2, physical pin 3 |
| SCL | GPIO3, physical pin 5 |

The original illustration's I²C labels were easy to confuse: **SDA goes to GPIO2 and SCL goes to GPIO3**. Check the breakout's voltage requirements and I²C address before powering it.

### ESP32 → DRV8833 inputs (provisional)

| Function | ESP32 GPIO proposed |
|---|---:|
| Left driver IN1 | GPIO26 |
| Left driver IN2 | GPIO27 |
| Left driver IN3 | GPIO14 |
| Left driver IN4 | GPIO13 |
| Right driver IN1 | GPIO25 |
| Right driver IN2 | GPIO33 |
| Right driver IN3 | GPIO32 |
| Right driver IN4 | GPIO23 |

This table is a **starting proposal only**. It assumes each DRV8833 board exposes four independent input pins and supports the intended two-motor wiring. Verify the actual OPEN-SMART board's pad labels and schematic. Some boards expose only a subset of chip pins or use a different layout. Avoid ESP32 boot-strapping pins unless their startup levels are understood.

The firmware must map each input pair to the correct motor and implement direction and PWM. Test with wheels lifted off the floor and at low duty cycle first. If a motor turns the wrong way, power down and swap that motor's output leads or correct the software mapping.

## 5. Motor-driver and power wiring

For each DRV8833 board:

- Connect the board's motor-supply input (often marked **VM**) to the motor battery positive, within the exact board and chip voltage limits.
- Connect board **GND** to motor-battery negative and the system common ground.
- Connect the two output terminals for each channel to one motor. Use the board's printed **OUT1/OUT2** or equivalent labels; do not infer pad positions from appearance alone.
- Connect the ESP32 GPIO control lines to the matching driver inputs.
- Keep motor wiring short and suitably rated. Add suitable supply decoupling close to the driver boards if not already present.

**Important:** A DRV8833 is a small dual H-bridge. Check the motor's stall current and the breakout's thermal/current limits. Four motors can exceed the safe capacity of a small breakout, especially at startup or when a wheel is stalled. Do not assume the board can safely supply two motors just because it has two channels.

## 6. Power architecture

The diagram proposes two 7.4 V LiPo packs:

- **Electronics pack:** feeds suitable DC-DC converters for the Pi 5 and ESP32/sensors.
- **Motor pack:** feeds the DRV8833 motor-supply inputs, within their allowed voltage range.

Use regulated rails with enough continuous and peak current capacity. The Pi 5 requires a stable 5 V supply with adequate current headroom; select a converter based on the actual Pi 5 load and its power-input method. The ESP32 DevKit may accept a suitable regulated 5 V input through its designated 5V/VIN input, or a regulated 3.3 V rail only at its 3V3 pin if correctly designed. **Never feed 7.4 V directly into the Pi 5, ESP32 5V/VIN, or sensor logic supply.**

Grounding depends on the exact driver and supply arrangement. For the UART signals to work, Pi 5 and ESP32 grounds must be common. A common ground is also normally required for ESP32-to-driver logic. Avoid accidentally connecting battery positive rails together. Use a fuse near each battery, secure connectors, protect against reverse polarity, and never leave a LiPo charging unattended.

## 7. Sensor connections

- **RealSense D421:** USB directly to Pi 5. Rigidly mount it on the chassis and confirm USB cable quality, bandwidth and power. The D421 is a depth/stereo device; do not assume it provides an RGB stream.
- **RPLidar C1:** USB directly to Pi 5. Confirm its USB power and driver configuration.
- **BNO085:** I²C as listed above. Enable I²C in the operating system and verify detection and ROS driver output.

## 8. Software responsibilities

### Raspberry Pi 5

- Ubuntu 24.04 and ROS 2 Jazzy
- RealSense driver and depth/infrared topics as supported by the D421
- RPLidar driver and `/scan`
- BNO085 IMU node and `/imu/data`
- Wheel odometry and TF, if encoder hardware is installed and connected to a suitable controller
- `robot_localization`, SLAM Toolbox and/or RTAB-Map as configured

### ESP32

- Bluetooth command handling, if retained
- UART command protocol with the Pi 5
- Movement-command parsing
- Motor direction and PWM outputs
- Optional encoder acquisition, if the encoder signals are wired to appropriate ESP32 inputs and the firmware supports them
- Safe stop behavior on invalid commands or communications timeout

The UART command format should match the protocol used by the existing AutoBot software or be updated consistently on both the Pi 5 and ESP32 firmware.

## 9. Bring-up checklist

1. With batteries disconnected, identify every pin from the actual board labels and manufacturer documentation.
2. Verify converter output voltages with a multimeter before connecting electronics.
3. Power the Pi 5 and ESP32 separately and confirm stable boot.
4. Test UART TX/RX and common ground before attaching motor drivers.
5. Connect one DRV8833 and one motor; test forward, reverse and stop with the wheel lifted.
6. Repeat for all four motors, then verify mecanum direction mapping at low speed.
7. Test sensor USB/I²C detection and ROS topics.
8. Check for brownouts, hot driver chips, loose connectors and battery voltage sag under load.
9. Test the emergency stop and communication-timeout stop before floor operation.

## 10. Accuracy note

The accompanying diagram is a conceptual wiring guide, not a manufacturer-verified netlist. The exact OPEN-SMART DRV8833 pad mapping, ESP32 DevKit revision, motor stall current, converter specifications and battery protection details were not supplied. Verify these before applying power.
