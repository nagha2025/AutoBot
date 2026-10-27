# Rover Controller - Android App

An Android mobile application to control a mecanum rover via Bluetooth connection to ESP32.

## Features

- Bluetooth connectivity to ESP32
- Directional control with speed adjustment (0.5 to 1.0)
- Mecanum drive support (lateral movement and rotation)
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
  - Motor 1: front-left, Motor 2: front-right, Motor 3: rear-left, Motor 4: rear-right

### Mecanum Drive Commands
- **MECANUM vx vy w** - Mecanum drive control
  - vx: lateral velocity (positive for right, negative for left)
  - vy: forward velocity
  - w: rotational velocity (positive for clockwise, negative for counter-clockwise)
  - Example: `MECANUM 0.0 0.7 0.0` (lateral movement right)

### Turn Commands
- **TURN_LEFT speed** - Turn left with differential drive
- **TURN_RIGHT speed** - Turn right with differential drive

### Stop Command
- **STOP** - Stop all motors

### Mode Commands
- **MODE MANUAL** - Switch to Bluetooth control mode
- **MODE AUTO** - Switch to UART control mode (for Raspberry Pi 5 autonomous navigation)

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

## ESP32 Hardware Setup

### Required Components
- ESP32-WROOM-32 Dev Module
- 2x DRV8833 Motor Driver Boards
- 4x DC Motors with wheels (for mecanum drive)
- Motor driver power supply (battery pack)
- Jumper wires

### GPIO Configuration (Default in firmware)
The ESP32 firmware uses the following GPIO pins (edit the Arduino sketch to match your wiring):

**Motor 1 (front-left):** IN1=GPIO25, IN2=GPIO26
**Motor 2 (front-right):** IN1=GPIO27, IN2=GPIO14
**Motor 3 (rear-left):** IN1=GPIO18, IN2=GPIO19
**Motor 4 (rear-right):** IN1=GPIO23, IN2=GPIO22

**Raspberry Pi 5 UART2 link:**
- ESP32 GPIO16 (RX2) <- Pi 5 TX
- ESP32 GPIO17 (TX2) -> Pi 5 RX
- GND <-> GND
- UART baud: 115200

### DRV8833 Connections
For each DRV8833 driver board:
- Connect nSLEEP pin to 3.3V (unless your board already pulls it high)
- Connect ESP32 GND, both driver grounds together
- Power motors from motor supply into driver VM (do not power from ESP32)

### ESP32 Firmware

The ESP32 firmware (`AutoBot_ESP32_DRV8833.ino`) should be uploaded using Arduino IDE:
- Board: "ESP32 Dev Module" (ESP32-WROOM-32)
- Upload Speed: 921600
- CPU Frequency: 240MHz
- Flash Frequency: 80MHz
- Flash Mode: QIO
- Flash Size: 4MB (32Mb)
- Partition Scheme: Default

The firmware processes these commands:
- `MOVE m1 m2 m3 m4` - Direct motor control (-1.0 to 1.0)
- `MECANUM vx vy w` - Mecanum drive kinematics with normalization
- `TURN_LEFT speed` - Turn left
- `TURN_RIGHT speed` - Turn right
- `STOP` - Stop all motors
- `MODE MANUAL/AUTO` - Switch between Bluetooth and UART control

### Safety Notes
- Verify the GPIO map before connecting motor power
- Motor numbering and forward direction may need adjustment for your chassis
- If a wheel spins the wrong way, swap the two input wires or reverse the outputs in the firmware
- Connect ESP32 GND, both driver grounds, and Pi 5 GND together

## Pairing the Android App with ESP32

1. **ESP32 Bluetooth Setup**
   - The ESP32 will appear as "AutoBot-ESP32" in Bluetooth scan
   - The firmware automatically starts Bluetooth Classic on boot

2. **On Android Device:**
   - Enable Bluetooth
   - Scan for devices
   - Look for "AutoBot-ESP32"
   - Pair with the device
   - No PIN is typically required

3. **Start the App:**
   - Open the Rover Controller app
   - Select "AutoBot-ESP32" from the dropdown
   - Tap "Connect"
   - Status should show "Connected to AutoBot-ESP32"

## Using the App

### Direction Control
- **Forward/Backward**: Move the rover forward or backward
- **Left/Right**: Rotate the rover in place (spin)
- Speed can be adjusted from 0.5 to 1.0 using Increase/Decrease buttons

### Mecanum Drive
- **Lateral Left/Right**: Move the rover sideways without turning
- These use the MECANUM command format with vx parameter

### Stop
- Press the STOP button to halt all motors immediately
- STOP is also sent automatically when you release any movement button

## Testing

1. Once connected, test direction buttons to verify movement
2. Adjust speed and test again
3. Test lateral movement buttons
4. Verify STOP button halts all movement
5. Check motor directions - reverse wiring if needed

## Troubleshooting

### App cannot find paired devices
- Ensure Bluetooth is enabled on your Android device
- Check that you've paired the ESP32 in Android Bluetooth settings
- Restart the app after pairing
- Verify ESP32 is powered on and firmware is running

### Connection fails
- Verify ESP32 is powered on and Bluetooth is active
- Check ESP32 Serial Monitor for Bluetooth initialization status
- Ensure ESP32 is within Bluetooth range
- Restart ESP32 if connection issues persist

### Motors don't respond
- Verify GPIO pin connections match firmware configuration
- Check that DRV8833 nSLEEP pins are connected to 3.3V
- Verify motor driver has power
- Test motors directly with power supply
- Check ESP32 Serial Monitor for command reception
- Verify motor wiring - swap IN1/IN2 if motor spins wrong direction

### Rover moves in wrong direction
- Swap the two input wires for the affected motor
- Or modify the GPIO configuration in the Arduino sketch
- The firmware includes comments explaining forward direction conventions

### App crashes
- Check Android logcat for error messages
- Ensure all permissions are granted
- Verify Android version compatibility (7.0+)

## Customization

### Changing GPIO Pins

Edit the ESP32 Arduino sketch to match your wiring:
```cpp
static constexpr uint8_t MOTOR_IN1[4] = {25, 27, 18, 23};  // Change to your pins
static constexpr uint8_t MOTOR_IN2[4] = {26, 14, 19, 22};  // Change to your pins
```

### Adjusting Motor Speed Range

The app limits speed to 0.5-1.0. To change this range, modify MainActivity.kt:
```kotlin
private var currentSpeed = 0.5  // Starting speed
// In speed button logic, adjust the range
```

### Changing Bluetooth Device Name

Edit the ESP32 Arduino sketch:
```cpp
if (SerialBT.begin("YourDeviceName")) {
```

### Adding New Commands

To add custom commands, modify both the app and ESP32 firmware:

**In MainActivity.kt:**
```kotlin
// Add new button
btnCustom.setOnClickListener {
    sendCommand("CUSTOM value")
}
```

**In ESP32 Arduino sketch:**
```cpp
else if (strcmp(action, "CUSTOM") == 0 && count == 2) {
    float value = atof(tokens[1]);
    // Your custom action
}
```

## Operational Modes

The system supports two operational modes:

### MANUAL Mode (Default)
- Rover controlled via Bluetooth from Android app
- All movement commands are processed
- Mode switched via Bluetooth: `MODE MANUAL`

### AUTO Mode
- Rover controlled via UART from Raspberry Pi 5
- Bluetooth movement commands are ignored (except STOP)
- UART2 link at 115200 baud
- Switch to AUTO mode via Bluetooth: `MODE AUTO`

## UART Connection to Raspberry Pi 5

For autonomous navigation, connect ESP32 to Raspberry Pi 5:
- ESP32 GPIO16 (RX2) -> Pi 5 TX
- ESP32 GPIO17 (TX2) -> Pi 5 RX
- GND <-> GND
- UART baud: 115200

The ESP32 listens for commands on UART2 in AUTO mode.

## License

This project is open source and available for educational and personal use.

## Support

For issues or questions, please check the troubleshooting section or verify your hardware connections.
