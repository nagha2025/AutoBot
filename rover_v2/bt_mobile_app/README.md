# Rover Controller - Android App

An Android mobile application to control a mecanum rover via Bluetooth connection to Raspberry Pi.

## Features

- Bluetooth connectivity to Raspberry Pi
- Directional control with speed adjustment (0.5 to 1.0)
- Mecanum drive support (lateral movement and rotation)
- PAN and TILT servo control (30-120° and 25-75°)
- Real-time command sending
- Connection status monitoring
- Support for paired device selection
- Light theme UI

## App Commands

The app sends the following commands to control the rover:

### Movement Commands
- **MOVE m1 m2 m3 m4** - Direct motor speed control (e.g., `MOVE 0.5 0.5 0.5 0.5`)
  - All motors at current speed for forward
  - Negative values for backward

### Mecanum Drive Commands
- **MECANUM vx vy w** - Mecanum drive control
  - vx: lateral velocity (positive for right, negative for left)
  - vy: forward velocity
  - w: rotational velocity (positive for clockwise, negative for counter-clockwise)
  - Example: `MECANUM 0.0 0.7 0.0` (lateral movement right)

### Servo Control Commands
- **PAN angle** - Set PAN servo angle (30-120° range)
  - Example: `PAN 45`
- **TILT angle** - Set TILT servo angle (25-75° range)
  - Example: `TILT 35`

### Stop Command
- **STOP** - Stop all motors

## Android App Setup

### Prerequisites

- Android Studio (latest version)
- Android device with Bluetooth support (Android 7.0 or higher)
- Minimum SDK: 24 (Android 7.0)
- Target SDK: 34 (Android 14)

### Building the App

1. Open Android Studio
2. Select "Open an Existing Project"
3. Navigate to this project directory
4. Wait for Gradle sync to complete
5. Connect your Android device via USB
6. Click the "Run" button or press Shift+F10

### Permissions

The app requires the following permissions:
- Bluetooth
- Bluetooth Admin
- Bluetooth Connect (Android 12+)
- Bluetooth Scan (Android 12+)
- Fine Location (required for Bluetooth device discovery)

These permissions are requested at runtime on first launch.

## Raspberry Pi Setup

### 1. Enable I2C and Bluetooth on Raspberry Pi

```bash
sudo apt update
sudo apt install python3-pip python3-serial

# Enable I2C and UART
sudo raspi-config
# Navigate to Interface Options -> I2C -> Enable
# Navigate to Interface Options -> Serial Port -> Enable serial port, disable serial console
```

### 2. Install Required Python Libraries

```bash
pip3 install adafruit-circuitpython-motorkit
pip3 install adafruit-circuitpython-servokit
pip3 install adafruit-circuitpython-motor
pip3 install pyserial
```

### 3. Hardware Setup

#### Required Components
- Raspberry Pi (Zero WH or any Pi with I2C support)
- Adafruit DC Motor HAT (or compatible MotorKit)
- Adafruit 16-Channel PWM/Servo HAT (or compatible ServoKit)
- 4x DC Motors with wheels (for mecanum drive)
- 2x Servo motors (for PAN and TILT)
- Motor driver power supply (battery pack)
- Jumper wires

#### I2C Connection
Connect the Motor HAT and Servo HAT to the Raspberry Pi via I2C:
- SDA -> GPIO 2 (SDA)
- SCL -> GPIO 3 (SCL)
- VCC -> 5V
- GND -> GND

#### Motor Connections
Connect 4 motors to the Motor HAT:
- Motor 1 -> Motor1 terminals
- Motor 2 -> Motor2 terminals
- Motor 3 -> Motor3 terminals
- Motor 4 -> Motor4 terminals

#### Servo Connections
Connect servos to the Servo HAT:
- PAN Servo -> Channel 0
- TILT Servo -> Channel 1

### 4. Python Control Script

The motor control script (`motor_serial_control.py`) should be placed on your Raspberry Pi. Key features:

- **Motor Control**: Uses Adafruit MotorKit for 4-motor mecanum drive
- **Servo Control**: Uses Adafruit ServoKit for PAN and TILT
- **Bluetooth Server**: Socket-based RFCOMM server on channel 1
- **UART Listener**: Receives commands from Raspberry Pi 5 for autonomous mode
- **Mode Switching**: Supports MANUAL (Bluetooth) and AUTO (UART) modes

The script processes these commands:
- `MOVE m1 m2 m3 m4` - Direct motor control
- `MECANUM vx vy w` - Mecanum drive kinematics
- `TURN_LEFT speed` - Turn left with differential drive
- `TURN_RIGHT speed` - Turn right with differential drive
- `PAN angle` - Set PAN servo angle
- `TILT angle` - Set TILT servo angle
- `STOP` - Stop all motors
- `MODE MANUAL/AUTO` - Switch between Bluetooth and UART control

### 5. Run the Motor Control Script

```bash
cd /path/to/motor_serial_control.py
python3 motor_serial_control.py
```

Or create a systemd service for auto-start:

```bash
sudo nano /etc/systemd/system/rover-motor.service
```

Add:
```ini
[Unit]
Description=Rover Motor Control Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/motor_serial_control.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start rover-motor
sudo systemctl enable rover-motor
```

## Pairing the Android App with Raspberry Pi

1. **Enable Bluetooth on Raspberry Pi**
   ```bash
   sudo bluetoothctl
   power on
   agent on
   default-agent
   discoverable on
   pairable on
   ```

2. **On Android Device:**
   - Enable Bluetooth
   - Scan for devices
   - Look for your Raspberry Pi (usually named "raspberrypi" or similar)
   - Pair with the device
   - Enter PIN if prompted (default is often "0000" or "1234")

3. **Verify Pairing:**
   ```bash
   # On Raspberry Pi
   bluetoothctl
   paired-devices
   ```

4. **Start the App:**
   - Open the Rover Controller app
   - Select your Raspberry Pi from the dropdown
   - Tap "Connect"
   - Status should show "Connected to [device name]"

## Using the App

### Direction Control
- **Forward/Backward**: Move the rover forward or backward
- **Left/Right**: Turn the rover (differential drive)
- Speed can be adjusted from 0.5 to 1.0 using Increase/Decrease buttons

### Mecanum Drive
- **Lateral Left/Right**: Move the rover sideways without turning
- **Clockwise/Counter-CW**: Rotate the rover in place
- These use the MECANUM command format

### Camera Control
- **PAN Slider**: Control horizontal camera angle (30-120°)
- **TILT Slider**: Control vertical camera angle (25-75°)
- Commands are sent when you release the slider

### Stop
- Press the STOP button to halt all motors immediately
- STOP is also sent automatically when you release any movement button

## Testing

1. Once connected, test direction buttons to verify movement
2. Adjust speed and test again
3. Test lateral movement and rotation buttons
4. Test PAN and TILT sliders
5. Verify STOP button halts all movement

## Troubleshooting

### App cannot find paired devices
- Ensure Bluetooth is enabled on your Android device
- Check that you've paired the Raspberry Pi in Android Bluetooth settings
- Restart the app after pairing

### Connection fails
- Verify the Python script is running on Raspberry Pi
- Check Bluetooth is enabled on Raspberry Pi: `sudo systemctl status bluetooth`
- Ensure the Raspberry Pi is discoverable: `sudo bluetoothctl discoverable on`
- Check for errors in the Python script output

### Motors don't respond
- Verify Motor HAT is properly connected via I2C
- Check that I2C is enabled: `sudo raspi-config`
- Verify motor HAT has power
- Test motors directly with power supply
- Check Python script for errors in the console

### Servos don't respond
- Verify Servo HAT is properly connected via I2C
- Check servo connections to correct channels
- Ensure servos have adequate power
- Verify PAN and TILT commands are being sent

### App crashes
- Check Android logcat for error messages
- Ensure all permissions are granted
- Verify Android version compatibility (7.0+)

## Customization

### Changing Servo Channels

Edit the motor_serial_control.py to change servo channels:
```python
SERVO_PAN = 0  # Change to your channel
SERVO_TILT = 1  # Change to your channel
```

### Adjusting Motor Speed Range

The app limits speed to 0.5-1.0. To change this range, modify MainActivity.kt:
```kotlin
private var currentSpeed = 0.5  // Starting speed
// In speed button logic, adjust the range
```

### Adding New Commands

To add custom commands, modify both the app and Python script:

**In MainActivity.kt:**
```kotlin
// Add new button
btnCustom.setOnClickListener {
    sendCommand("CUSTOM value")
}
```

**In motor_serial_control.py:**
```python
elif action == "CUSTOM" and len(parts) == 2:
    value = float(parts[1])
    # Your custom action
```

## Operational Modes

The system supports two operational modes:

### MANUAL Mode (Default)
- Rover controlled via Bluetooth from Android app
- All movement commands are processed
- PAN and TILT commands are always processed regardless of mode

### AUTO Mode
- Rover controlled via UART from Raspberry Pi 5
- Bluetooth movement commands are ignored (except STOP, PAN, TILT)
- Switch to AUTO mode via Bluetooth: `MODE AUTO`
- Switch back to MANUAL mode: `MODE MANUAL`

## License

This project is open source and available for educational and personal use.

## Support

For issues or questions, please check the troubleshooting section or verify your hardware connections.
