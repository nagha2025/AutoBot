#!/usr/bin/env python3
import time
import socket
import threading
import serial
import board
from adafruit_motorkit import MotorKit
from adafruit_servokit import ServoKit

# Initialize hardware controllers
motor_kit = MotorKit(i2c=board.I2C())
motors = [motor_kit.motor1, motor_kit.motor2, motor_kit.motor3, motor_kit.motor4]

try:
    servo_kit = ServoKit(channels=16, i2c=board.I2C())
    SERVO_PAN = 0
    SERVO_TILT = 1
    print("-> 16-Channel Servo HAT initialized successfully.")
except Exception as e:
    servo_kit = None
    print(f"[WARNING]: Servo HAT initialization failed: {e}")

# Configuration Constants
BT_PORT = 1
UART_PORT = "/dev/serial0"
UART_BAUD = 115200

# Global Mode Flag: True = Manual (Bluetooth), False = Autonomous (Pi 5 UART)
manual_mode = True
mode_lock = threading.Lock()

def set_motor_speeds(m1: float, m2: float, m3: float, m4: float) -> None:
    speeds = [m1, m2, m3, m4]
    for i, speed in enumerate(speeds):
        clamped = max(-1.0, min(1.0, speed)) if speed is not None else None
        motors[i].throttle = clamped
    print(f"-> Set Motor Throttles: M1={m1}, M2={m2}, M3={m3}, M4={m4}")

def stop_all_motors():
    for m in motors:
        m.throttle = 0.0
    print("-> All motors stopped.")

def set_servo_angle(channel: int, angle: float):
    if servo_kit is not None:
        clamped_angle = max(0.0, min(180.0, angle))
        servo_kit.servo[channel].angle = clamped_angle
        print(f"-> Servo Channel {channel} set to {clamped_angle}°")
    else:
        print("[ERROR]: Servo HAT not available.")

def process_command(cmd: str, source: str):
    """
    Processes commands based on the source (BT or UART) and current operational mode.
    """
    global manual_mode
    raw_cmd = cmd.strip()
    if not raw_cmd:
        return

    print(f"\n[RECEIVED {source}]: '{raw_cmd}'")
    cmd_upper = raw_cmd.upper()
    parts = cmd_upper.split()
    if not parts:
        return
    
    action = parts[0]

    # Handle Mode switching (Exclusively allowed via Bluetooth)
    if action == "MODE":
        if source != "BT":
            print("[WARNING]: Mode change commands are restricted to Bluetooth only.")
            return
        if len(parts) == 2:
            new_mode = parts[1]
            with mode_lock:
                if new_mode == "MANUAL":
                    manual_mode = True
                    print(">>> OPERATIONAL MODE: MANUAL (Bluetooth Control Active)")
                elif new_mode == "AUTO":
                    manual_mode = False
                    print(">>> OPERATIONAL MODE: AUTO (Raspberry Pi 5 UART Control Active)")
                else:
                    print(f"[ERROR]: Unknown mode '{new_mode}'. Use MANUAL or AUTO.")
        return

    # Check execution permissions based on mode
    with mode_lock:
        current_manual = manual_mode

    if source == "UART" and current_manual:
        print("[IGNORED UART]: Rover is currently in MANUAL mode. Switch to AUTO via Bluetooth to allow Pi 5 navigation.")
        return
    if source == "BT" and not current_manual and action not in ["STOP", "PAN", "TILT"]:
        print("[WARNING BT]: Rover is in AUTO mode. Movement commands overridden. Switch to MANUAL to drive via Bluetooth.")
        return

    try:
        if action == "MOVE" and len(parts) == 5:
            m1, m2, m3, m4 = map(float, parts[1:])
            set_motor_speeds(m1, m2, m3, m4)

        elif action == "MECANUM" and len(parts) == 4:
            vx, vy, w = map(float, parts[1:])
            m1 = vx - vy - w
            m2 = vx + vy + w
            m3 = vx + vy - w
            m4 = vx - vy + w
            set_motor_speeds(m1, m2, m3, m4)

        elif action == "TURN_LEFT" and len(parts) == 2:
            speed = float(parts[1])
            set_motor_speeds(-speed, speed, -speed, speed)

        elif action == "TURN_RIGHT" and len(parts) == 2:
            speed = float(parts[1])
            set_motor_speeds(speed, -speed, speed, -speed)

        elif action == "PAN" and len(parts) == 2:
            angle = float(parts[1])
            set_servo_angle(SERVO_PAN, angle)

        elif action == "TILT" and len(parts) == 2:
            angle = float(parts[1])
            set_servo_angle(SERVO_TILT, angle)

        elif action == "STOP":
            stop_all_motors()

        else:
            print(f"[WARNING]: Unrecognized command structure from {source}: '{raw_cmd}'")

    except ValueError:
        print(f"[ERROR]: Failed to parse numeric values from {source} command: '{raw_cmd}'")

def bluetooth_server_thread():
    """Background thread to handle Bluetooth RFCOMM client connections."""
    server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    try:
        server_sock.bind(("00:00:00:00:00:00", BT_PORT))
    except OSError:
        server_sock.bind(("", BT_PORT))
        
    server_sock.listen(1)
    print(f"Bluetooth server listening on RFCOMM channel {BT_PORT}...")

    while True:
        try:
            client_sock, client_info = server_sock.accept()
            print(f"Accepted Bluetooth connection from {client_info}")

            while True:
                data = client_sock.recv(1024)
                if not data:
                    break
                line = data.decode('utf-8', errors='ignore')
                for cmd in line.splitlines():
                    process_command(cmd, "BT")

        except (socket.error, OSError) as e:
            print(f"[BT ERROR]: Connection lost ({e}). Waiting for new connection...")
        except Exception as e:
            print(f"[BT EXCEPTION]: {e}")
        finally:
            try:
                client_sock.close()
            except NameError:
                pass

def uart_listener_thread():
    """Background thread to listen for navigation commands from Raspberry Pi 5 over UART."""
    print(f"Starting UART listener on {UART_PORT} at {UART_BAUD} baud...")
    try:
        ser = serial.Serial(UART_PORT, UART_BAUD, timeout=0.1)
    except Exception as e:
        print(f"[CRITICAL UART ERROR]: Could not open serial port {UART_PORT}: {e}")
        return

    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    process_command(line, "UART")
            else:
                time.sleep(0.01)
        except Exception as e:
            print(f"[UART ERROR]: {e}")
            time.sleep(1)

def main():
    stop_all_motors()
    print(f"Initial State -> Operational Mode: MANUAL (Default)")

    # Start Bluetooth server thread
    bt_thread = threading.Thread(target=bluetooth_server_thread, daemon=True)
    bt_thread.start()

    # Start UART listener thread for Pi 5 communication
    uart_thread = threading.Thread(target=uart_listener_thread, daemon=True)
    uart_thread.start()

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting program...")
        stop_all_motors()

if __name__ == "__main__":
    main()