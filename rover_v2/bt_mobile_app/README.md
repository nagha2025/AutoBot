# Rover Controller - Android App

An Android mobile application to control a rover via Bluetooth connection to Raspberry Pi Zero WH.

## Features

- Bluetooth connectivity to Raspberry Pi Zero WH
- D-pad style directional control
- Real-time command sending
- Connection status monitoring
- Support for paired device selection

## App Commands

The app sends single-character commands to control the rover:

- **F** - Move Forward
- **B** - Move Backward
- **L** - Turn Left
- **R** - Turn Right
- **S** - Stop (sent automatically when button is released)

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

## Raspberry Pi Zero WH Setup

### 1. Enable Bluetooth on Raspberry Pi

```bash
sudo apt update
sudo apt install bluetooth bluez bluez-tools
sudo systemctl start bluetooth
sudo systemctl enable bluetooth
```

### 2. Configure Bluetooth Serial Port

```bash
# Install serial port utilities
sudo apt install python3-pip python3-serial

# Enable serial port
sudo raspi-config
# Navigate to Interface Options -> Serial Port
# Enable serial port but disable serial console
```

### 3. Setup Bluetooth Serial Profile

```bash
# Install bluetooth serial utilities
sudo apt install libbluetooth-dev

# Create a Bluetooth serial service
sudo nano /etc/systemd/system/bluetooth-serial.service
```

Add the following content:

```ini
[Unit]
Description=Bluetooth Serial Service
After=bluetooth.service

[Service]
ExecStart=/usr/bin/python3 /home/pi/rover_control.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

### 4. Python Control Script

Create the rover control script:

```bash
nano /home/pi/rover_control.py
```

```python
#!/usr/bin/env python3
import bluetooth
import RPi.GPIO as GPIO
import time

# GPIO Pin Configuration
# Adjust these based on your motor driver connections
MOTOR_LEFT_FORWARD = 17
MOTOR_LEFT_BACKWARD = 18
MOTOR_RIGHT_FORWARD = 22
MOTOR_RIGHT_BACKWARD = 23

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(MOTOR_LEFT_FORWARD, GPIO.OUT)
GPIO.setup(MOTOR_LEFT_BACKWARD, GPIO.OUT)
GPIO.setup(MOTOR_RIGHT_FORWARD, GPIO.OUT)
GPIO.setup(MOTOR_RIGHT_BACKWARD, GPIO.OUT)

# Initialize all motors to off
GPIO.output(MOTOR_LEFT_FORWARD, GPIO.LOW)
GPIO.output(MOTOR_LEFT_BACKWARD, GPIO.LOW)
GPIO.output(MOTOR_RIGHT_FORWARD, GPIO.LOW)
GPIO.output(MOTOR_RIGHT_BACKWARD, GPIO.LOW)

def stop_motors():
    """Stop all motors"""
    GPIO.output(MOTOR_LEFT_FORWARD, GPIO.LOW)
    GPIO.output(MOTOR_LEFT_BACKWARD, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_FORWARD, GPIO.LOW)
    GPIO.output(MOTOR_RIGHT_BACKWARD, GPIO.LOW)

def move_forward():
    """Move rover forward"""
    stop_motors()
    GPIO.output(MOTOR_LEFT_FORWARD, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_FORWARD, GPIO.HIGH)

def move_backward():
    """Move rover backward"""
    stop_motors()
    GPIO.output(MOTOR_LEFT_BACKWARD, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_BACKWARD, GPIO.HIGH)

def turn_left():
    """Turn rover left"""
    stop_motors()
    GPIO.output(MOTOR_LEFT_BACKWARD, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_FORWARD, GPIO.HIGH)

def turn_right():
    """Turn rover right"""
    stop_motors()
    GPIO.output(MOTOR_LEFT_FORWARD, GPIO.HIGH)
    GPIO.output(MOTOR_RIGHT_BACKWARD, GPIO.HIGH)

def main():
    # Bluetooth server setup
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)
    
    # Get the port number
    port = server_sock.getsockname()[1]
    
    # Set the device to discoverable
    uuid = "00001101-0000-1000-8000-00805F9B34FB"
    bluetooth.advertise_service(server_sock, "RoverController", service_id=uuid,
                               service_classes=[uuid],
                               profiles=[bluetooth.SERIAL_PORT_PROFILE])
    
    print(f"Waiting for connection on RFCOMM channel {port}...")
    
    try:
        while True:
            client_sock, address = server_sock.accept()
            print(f"Connected to {address}")
            
            try:
                while True:
                    data = client_sock.recv(1024)
                    if not data:
                        break
                    
                    command = data.decode('utf-8').strip().upper()
                    print(f"Received command: {command}")
                    
                    if command == 'F':
                        move_forward()
                    elif command == 'B':
                        move_backward()
                    elif command == 'L':
                        turn_left()
                    elif command == 'R':
                        turn_right()
                    elif command == 'S':
                        stop_motors()
                    
            except IOError as e:
                print(f"Connection error: {e}")
            finally:
                stop_motors()
                client_sock.close()
                print("Connection closed")
                
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        stop_motors()
        server_sock.close()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
```

Make the script executable:

```bash
chmod +x /home/pi/rover_control.py
```

### 5. Start the Bluetooth Service

```bash
sudo systemctl daemon-reload
sudo systemctl start bluetooth-serial
sudo systemctl enable bluetooth-serial
```

## Hardware Setup

### Required Components

- Raspberry Pi Zero WH
- Motor Driver (L298N or similar)
- 2x DC Motors with wheels
- Motor driver power supply (battery pack)
- Jumper wires
- Breadboard (optional)

### Wiring Diagram

```
Raspberry Pi Zero WH          L298N Motor Driver
------------------          --------------------
GPIO 17          ----->    IN1
GPIO 18          ----->    IN2
GPIO 22          ----->    IN3
GPIO 23          ----->    IN4
5V               ----->    +12V (if using 5V motors)
GND              ----->    GND

Motor Driver              Motors
-------------            -------
OUT1, OUT2      ----->    Left Motor
OUT3, OUT4      ----->    Right Motor
```

### Power Considerations

- Use a separate battery pack for motors (do not power motors from Pi)
- Common ground between Pi and motor driver is essential
- Recommended: 2x 18650 Li-ion cells (7.4V) for motors

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

## Testing

1. Once connected, press the direction buttons
2. Verify the rover moves in the expected direction
3. Release the button - the rover should stop automatically
4. Test all directions: Forward, Backward, Left, Right

## Troubleshooting

### App cannot find paired devices
- Ensure Bluetooth is enabled on your Android device
- Check that you've paired the Raspberry Pi in Android Bluetooth settings
- Restart the app after pairing

### Connection fails
- Verify the Python script is running on Raspberry Pi: `sudo systemctl status bluetooth-serial`
- Check Bluetooth is enabled on Raspberry Pi: `sudo systemctl status bluetooth`
- Ensure the Raspberry Pi is discoverable: `sudo bluetoothctl discoverable on`

### Motors don't respond
- Check GPIO pin connections
- Verify motor driver has power
- Test motors directly with power supply
- Check Python script for errors: `sudo journalctl -u bluetooth-serial -f`

### App crashes
- Check Android logcat for error messages
- Ensure all permissions are granted
- Verify Android version compatibility (7.0+)

## Customization

### Changing GPIO Pins

Edit the pin definitions in `rover_control.py`:

```python
MOTOR_LEFT_FORWARD = 17  # Change to your pin
MOTOR_LEFT_BACKWARD = 18  # Change to your pin
# etc.
```

### Adding Speed Control

To add PWM speed control, modify the script:

```python
# Add at the top
from RPi.GPIO import PWM

# In setup
left_motor_pwm = GPIO.PWM(MOTOR_LEFT_FORWARD, 1000)
right_motor_pwm = GPIO.PWM(MOTOR_RIGHT_FORWARD, 1000)
left_motor_pwm.start(50)  # 50% speed
right_motor_pwm.start(50)
```

### Adding Additional Commands

To add more commands, modify both the app and Python script:

**In MainActivity.kt:**
```kotlin
// Add new button with command
btnExtra.setOnTouchListener(createDirectionTouchListener("X"))
```

**In rover_control.py:**
```python
elif command == 'X':
    # Your custom action
    pass
```

## License

This project is open source and available for educational and personal use.

## Support

For issues or questions, please check the troubleshooting section or verify your hardware connections.
