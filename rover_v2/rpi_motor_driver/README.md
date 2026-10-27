# AutoBot Raspberry Pi Motor Controller

`motor_serial_control.py` is the low-level motor-control and
command-bridge program for the AutoBot rover. It runs on the Raspberry
Pi Zero WH and connects the rover's motor and servo controllers to two
command sources:

-   **Bluetooth RFCOMM** --- manual control from the Android driving
    app.
-   **UART serial** --- autonomous movement commands from the Raspberry
    Pi 5 running ROS 2.

The script uses Adafruit MotorKit to control four DC motors and, when
available, Adafruit ServoKit to control the pan/tilt servos.

> **Hardware note:** This README describes the current Python script. It
> includes pan/tilt support and uses Adafruit motor/servo HATs. It is
> not the ESP32 + DRV8833 firmware.

## Features

-   Controls four DC motors with signed throttle values from `-1.0` to
    `1.0`.
-   Accepts direct four-motor commands and mecanum-style velocity
    commands.
-   Supports left and right turns.
-   Supports camera pan and tilt servos on channels 0 and 1.
-   Receives commands over Bluetooth and UART in separate background
    threads.
-   Uses a mode switch to prevent manual movement commands and
    autonomous UART commands from controlling the motors at the same
    time.
-   Stops all motors when the program starts and when it is interrupted
    with `Ctrl+C`.

## Hardware and interfaces

  -----------------------------------------------------------------------
  Component / interface               Configuration in the script
  ----------------------------------- -----------------------------------
  Low-level controller                Raspberry Pi Zero WH

  DC motor controller                 Adafruit MotorKit-compatible I²C
                                      motor HAT/driver

  DC motors                           Four motors: `motor1` through
                                      `motor4`

  Servo controller                    16-channel PCA9685-compatible Servo
                                      HAT

  Pan servo                           Servo channel `0`

  Tilt servo                          Servo channel `1`

  Bluetooth                           RFCOMM channel `1`

  UART device                         `/dev/serial0`

  UART baud rate                      `115200`

  Default operating mode              `MANUAL`
  -----------------------------------------------------------------------

The script initializes the motor controller through `board.I2C()`. The
servo controller is initialized separately; if that initialization
fails, the program prints a warning and continues without servo control.

## Software requirements

Use a Raspberry Pi OS installation with Python 3 and the required
hardware libraries.

Typical packages are:

``` bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-serial
```

The script imports `serial`, `board`, `adafruit_motorkit`, and
`adafruit_servokit`. On Raspberry Pi OS, install the appropriate
Adafruit Blinka, MotorKit, and ServoKit libraries using Adafruit's
current installation guidance. A virtual environment may be required on
newer Raspberry Pi OS releases.

For example, in a project virtual environment:

``` bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install pyserial adafruit-blinka adafruit-circuitpython-motorkit adafruit-circuitpython-servokit
```

If I²C is not enabled, enable it using the Raspberry Pi configuration
tools and reboot. Confirm the motor and servo HATs are correctly powered
and detected before running the script.

Bluetooth must be enabled and configured on the Raspberry Pi. The
account running the program needs permission to use Bluetooth and the
serial device.

## Installation and running

Place `motor_serial_control.py` in your project directory, then run:

``` bash
python3 motor_serial_control.py
```

If you use a virtual environment, activate it first and run the script
with that environment's Python.

At startup, the program attempts to stop all four motors, starts the
Bluetooth server on RFCOMM channel 1, and starts the UART listener on
`/dev/serial0` at 115200 baud. The default mode is `MANUAL`.

Keep the robot's wheels raised off the ground during initial tests.
Verify the motor supply, common ground, I²C wiring, and driver/HAT
wiring before commanding movement.

## Operating modes

### Manual mode

Manual mode is the default. Bluetooth movement commands are accepted,
while movement commands arriving over UART are ignored.

Switch to manual mode from Bluetooth:

``` text
MODE MANUAL
```

### Autonomous mode

Switch to autonomous mode from Bluetooth:

``` text
MODE AUTO
```

In autonomous mode, UART movement commands from the Raspberry Pi 5 are
accepted. Bluetooth movement commands are ignored, but `STOP`, `PAN`,
and `TILT` remain permitted by the script.

Mode changes are accepted only from Bluetooth.

## Command reference

Commands are text lines. Numeric values are separated by spaces.
Commands received over Bluetooth and UART must end with a newline so the
receiver can process each command as a line.

  ------------------------------------------------------------------------
  Command                 Example                  Meaning
  ----------------------- ------------------------ -----------------------
  Set four motor          `MOVE 0.5 0.5 0.5 0.5`   Set motors 1--4
  throttles                                        independently

  Mecanum-style movement  `MECANUM 0.5 0.0 0.0`    Supply `vx vy w`; the
                                                   script converts these
                                                   values to four motor
                                                   commands

  Turn left               `TURN_LEFT 0.4`          Apply the script's
                                                   left-turn motor pattern

  Turn right              `TURN_RIGHT 0.4`         Apply the script's
                                                   right-turn motor
                                                   pattern

  Stop                    `STOP`                   Set all four motor
                                                   throttles to zero

  Pan camera              `PAN 90`                 Set servo channel 0 to
                                                   90 degrees

  Tilt camera             `TILT 45`                Set servo channel 1 to
                                                   45 degrees

  Select manual mode      `MODE MANUAL`            Allow Bluetooth
                                                   movement commands

  Select autonomous mode  `MODE AUTO`              Allow UART movement
                                                   commands
  ------------------------------------------------------------------------

### Motor command details

-   `MOVE` requires exactly four numeric values.
-   Each motor throttle is clamped to the range `-1.0` to `1.0`.
-   `MECANUM` takes `vx`, `vy`, and `w` and calculates:
    -   `m1 = vx - vy - w`
    -   `m2 = vx + vy + w`
    -   `m3 = vx + vy - w`
    -   `m4 = vx - vy + w`
-   The calculated motor values are individually clamped to `-1.0` to
    `1.0`; the script does not proportionally normalize all four values
    together.
-   `PAN` and `TILT` angles are clamped to `0`--`180` degrees.
-   If servo initialization fails, pan/tilt commands report that the
    Servo HAT is unavailable.

**Important:** The motor ordering and signs in the mecanum equations
must match the physical wheel placement and motor wiring. If a wheel
spins in the wrong direction, check the motor connections and the
command mapping.

## UART connection to the Raspberry Pi 5

The script opens:

``` text
/dev/serial0
115200 baud
```

Ensure the Pi Zero WH UART is enabled, that the Pi 5 and Pi Zero WH use
compatible UART logic levels, and that their grounds are connected.
Connect TX to the other device's RX and RX to the other device's TX. Do
not connect a 5 V UART signal directly to a Raspberry Pi GPIO UART.

The Raspberry Pi 5 should send one supported command per line. In
`MANUAL` mode, UART movement commands are intentionally ignored; switch
to `AUTO` using Bluetooth first.

## Bluetooth connection

The script listens for one RFCOMM client at a time on channel 1. The
Android app should connect to the Pi Zero WH and send the supported
commands as newline-terminated text.

When connected, the script prints received commands and reports whether
commands were accepted, ignored due to the current mode, or not
recognized.

## Troubleshooting

  -----------------------------------------------------------------------
  Symptom                             Checks
  ----------------------------------- -----------------------------------
  Motor HAT initialization fails      Check I²C is enabled, HAT seating,
                                      power, and installed Adafruit
                                      libraries.

  Bluetooth connection fails          Check Bluetooth service and
                                      pairing, RFCOMM permissions,
                                      channel 1, and whether another
                                      process is using the channel.

  UART cannot open                    Verify `/dev/serial0` exists, UART
                                      is enabled, permissions are
                                      correct, and the port is not
                                      occupied by a login console or
                                      another process.

  UART commands are ignored           The program starts in `MANUAL`;
                                      send `MODE AUTO` over Bluetooth to
                                      enable UART movement.

  Bluetooth movement commands are     Check whether the rover is in
  ignored                             `AUTO`; send `MODE MANUAL` over
                                      Bluetooth.

  Commands are unrecognized           Match the command spelling, number
                                      of arguments, spaces, and newline
                                      termination to the command
                                      reference.

  Motors do not move                  Test with wheels raised, confirm
                                      motor supply and common ground,
                                      inspect HAT/motor wiring, and
                                      verify nonzero throttle values
                                      appear in the console.

  Pan/tilt does not work              Check Servo HAT initialization, I²C
                                      connection, servo power, and
                                      channels 0 and 1.
  -----------------------------------------------------------------------

The script prints command and error messages to the terminal. Use these
messages to identify whether a command was received, rejected because of
the operating mode, or passed to a motor/servo function.

## Shutdown

Press `Ctrl+C` in the terminal running the script. The program catches
`KeyboardInterrupt` and commands all four motors to stop.

For safety, also use a physical power switch or emergency-stop
arrangement that can disconnect motor power. Software stopping is not a
substitute for a hardware emergency stop.

## Limitations and notes

-   The script provides low-level command execution; it does not itself
    run ROS 2 SLAM or Nav2.
-   The script has no explicit command watchdog that stops the motors
    after a Bluetooth/UART communication timeout. If a sender
    disconnects while a nonzero throttle is set, the last motor command
    may remain active until another command or shutdown occurs. Consider
    adding a timeout-based stop for safer operation.
-   The `MECANUM` equations are a simple mapping. Validate them against
    the rover's wheel layout and coordinate convention.
-   This code targets the Raspberry Pi + Adafruit HAT architecture. The
    newer ESP32 + DRV8833 architecture requires a different firmware and
    wiring setup.

## Source

[`rover_v2/rpi_motor_driver/motor_serial_control.py`](https://github.com/nagha2025/AutoBot/blob/main/rover_v2/rpi_motor_driver/motor_serial_control.py)
