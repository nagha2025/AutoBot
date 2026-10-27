# AutoBot --- Autonomous Ground Rover

AutoBot is a four-wheel mecanum autonomous ground rover. This repository
contains software for two generations of manual drive control, ESP32
motor-controller firmware, and ROS 2 packages for sensing, odometry,
mapping, and robot integration.

## Repository structure

``` text
AutoBot/
├── bt_mobile_app/
├── bt_mobile_app-ESP32version/
├── esp32_driver/
├── ros2_pkgs/
└── rpi_motor_driver/
```

## Folder guide

### `bt_mobile_app/` --- Android app for the Raspberry Pi Zero WH version

This folder contains the original Android mobile application, written in
**Kotlin**. It connects to the **Raspberry Pi Zero WH** over Bluetooth
so the phone can be used to drive AutoBot.

The app provides the manual driving interface and sends movement/stop
commands to the Pi Zero WH. The Pi runs the Python motor-control script
in `rpi_motor_driver/`, which controls the motors through its
motor-driver hardware. The older design also included camera pan/tilt
control.

Use this app with the original Pi Zero WH motor-controller architecture.

### `bt_mobile_app-ESP32version/` --- Android app for the ESP32 version

This folder contains the Kotlin Android app variant intended for the
updated architecture, where an **ESP32-WROOM-32 / ESP32 DevKit** is the
low-level motor controller.

The phone communicates with the ESP32 over Bluetooth, and the ESP32
controls the wheel motors through the two DRV8833 motor-driver boards.
This version is intended to be used with the firmware in
`esp32_driver/`. The pan-tilt mechanism is not part of the updated
build; the RealSense D421 is mounted directly on the chassis.

The app and firmware must use matching Bluetooth settings and command
strings. Check both folders if commands are not recognised.

### `esp32_driver/` --- ESP32 motor-controller firmware

This folder contains the ESP32 firmware, intended to be uploaded with
the **Arduino IDE** to an ESP32-WROOM-32 / standard ESP32 DevKit.

The firmware receives drive commands and controls four drive motors
through **two DRV8833 dual H-bridge boards**. The ESP32 handles
low-level motor control; the Raspberry Pi 5 remains the main computer
for ROS 2, sensor processing, mapping, and autonomy. A UART link can be
used between the Pi 5 and ESP32 when configured in the firmware.

Integration notes:

-   Bluetooth commands must match `bt_mobile_app-ESP32version/`.
-   UART TX and RX should be crossed: Pi TX → ESP32 RX, and ESP32 TX →
    Pi RX.
-   The Pi 5 and ESP32 must share a **common ground** for reliable UART
    communication.
-   Confirm GPIO assignments, DRV8833 sleep/wake pins, motor polarity,
    and wheel order against the actual wiring and sketch.
-   Test with the wheels lifted clear of the ground before driving.

Refer to the firmware source for the definitive pin map and supported
commands.

### `ros2_pkgs/` --- ROS 2 sensing and autonomy packages

This folder contains AutoBot's ROS 2 packages. The current software
baseline is **ROS 2 Jazzy on Ubuntu 24.04**.

The package set includes:

-   **`imu_node_pkg`** --- reads the BNO085 IMU and publishes
    measurements such as `/imu/data`.
-   **`wheel_odometry`** --- reads wheel encoder signals and publishes
    raw wheel odometry on `/odom_raw`.
-   **`robot_bringup`** --- launch and configuration files for bringing
    up robot components, static transforms, and sensor fusion with
    `robot_localization` EKF.
-   **LiDAR integration** --- AutoBot uses an RPLidar C1 with the
    `sllidar_ros2` driver, which publishes scans on `/scan`. Depending
    on the workspace, this driver may be installed separately rather
    than included here.
-   **Mapping and visual SLAM** --- SLAM Toolbox can be used for LiDAR
    mapping, while RTAB-Map can be configured for stereo visual mapping.
    These may be installed separately from this repository.

The Raspberry Pi 5 runs the high-level ROS 2 stack. RViz2 can run on the
Pi or on a separate Ubuntu VM/workstation over the network.

Important configuration notes:

-   Ensure topic names and frame IDs agree across launch and
    configuration files.
-   Check the TF tree linking `base_link`, `odom`, `map`, LiDAR, and
    camera frames.
-   The RealSense D421 is a stereo/depth device without a conventional
    RGB stream. Stereo visual SLAM should use the rectified left/right
    infrared images and their matching camera-info topics.
-   Verify wheel-odometry kinematics against the mecanum chassis.
    Differential-drive equations do not correctly model mecanum lateral
    movement.
-   Check launch files for machine-specific absolute paths before
    running them on another computer.

Build the packages from a sourced ROS 2 Jazzy environment using `colcon`
from the relevant workspace root. Consult each package's `package.xml`,
setup files, launch files, and configuration files for exact
dependencies and commands.

### `rpi_motor_driver/` --- Python motor control for the Raspberry Pi Zero WH

This folder contains the original **Python** low-level motor-control
software for the Raspberry Pi Zero WH architecture. The main script is
`motor_serial_control.py`.

In the older build, the script used Adafruit MotorKit to control four DC
motors and ServoKit for camera pan/tilt. It accepted commands over
Bluetooth RFCOMM and UART, including movement, stop, speed/mode, and
pan/tilt commands.

This is the legacy Pi Zero WH motor-controller implementation. It is
separate from the ESP32 firmware and is not required for direct motor
control when the ESP32 is used instead. The pan/tilt functions are
legacy features and are not part of the updated ESP32 build.

For the original architecture, ensure the Python dependencies,
motor-driver hardware, Bluetooth settings, UART configuration, and
command protocol match the code.

## System architecture

### Original Pi Zero WH motor-control version

``` text
Android app (Kotlin)
        │ Bluetooth
        ▼
Raspberry Pi Zero WH
Python: rpi_motor_driver
        │
        ▼
Motor-driver hardware
        │
        ▼
Four drive motors
```

### Updated ESP32 motor-control version

``` text
Android app (Kotlin)
        │ Bluetooth
        ▼
ESP32-WROOM-32
Arduino firmware: esp32_driver
        │ GPIO / PWM
        ▼
2 × DRV8833 motor-driver boards
        │
        ▼
Four drive motors

Raspberry Pi 5 (ROS 2 Jazzy)
 ├── RPLidar C1
 ├── RealSense D421 stereo/depth camera
 ├── BNO085 IMU
 ├── Wheel odometry and sensor fusion
 └── SLAM / mapping / autonomy
        │
        └── UART link to ESP32, when enabled
```

The mobile app is used for manual teleoperation. The Pi 5 runs
high-level sensing and autonomy. The exact integration of ROS 2 motion
commands with the ESP32 depends on the UART protocol and the nodes
currently configured.

## Which folder should I use?

  -----------------------------------------------------------------------
  Goal                                Folder
  ----------------------------------- -----------------------------------
  Modify the original Android app for `bt_mobile_app/`
  the Pi Zero WH version              

  Modify the Android app for direct   `bt_mobile_app-ESP32version/`
  Bluetooth control of the ESP32      

  Modify or upload ESP32 motor        `esp32_driver/`
  firmware with Arduino IDE           

  Develop ROS 2 sensing, odometry,    `ros2_pkgs/`
  bringup, and autonomy               

  Maintain the legacy Pi Zero WH      `rpi_motor_driver/`
  Python motor-control script         
  -----------------------------------------------------------------------

## Safety and integration notes

-   Lift the chassis so the wheels are off the ground during initial
    motor-direction tests.
-   Keep a reliable way to cut motor power during testing.
-   Do not power motors from ESP32 GPIO pins or the board's 3.3 V
    output.
-   Check the exact DRV8833 breakout board's motor-supply and logic
    requirements.
-   Connect grounds appropriately wherever boards exchange UART or other
    electrical signals.
-   Verify voltage levels, current capacity, polarity, and wiring before
    powering the robot.
-   Do not let two independent controllers issue motor commands
    simultaneously unless control arbitration is explicitly implemented.

## Development status

AutoBot has evolved from a Raspberry Pi Zero WH motor-controller design
to an ESP32-based low-level controller, while retaining the Raspberry Pi
5 for ROS 2 and autonomy. The Pi Zero WH Android app and Python driver
are retained for the legacy implementation; the ESP32 app and firmware
support the newer motor-control architecture.

For exact pin assignments, command strings, launch arguments, and
dependency versions, treat the source code and configuration files in
each folder as authoritative.
