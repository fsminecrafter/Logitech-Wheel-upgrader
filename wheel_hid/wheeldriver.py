#!/usr/bin/env python3
import serial
import sys
import time
import platform

# Cross-platform joystick
USE_VJOY = platform.system() == "Windows"
USE_UINPUT = platform.system() != "Windows"

if USE_VJOY:
    import pyvjoy
elif USE_UINPUT:
    import uinput

SERIAL_PORT = "COM3" if USE_VJOY else "/dev/ttyACM0"
BAUDRATE = 115200
PAIRING_CODE = "FSMINEWHEEL123"
MAX_RETRIES = 5

# ---------------- INIT ----------------
def init_serial():
    for _ in range(MAX_RETRIES):
        try:
            s = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
            return s
        except Exception as e:
            print(f"[ERROR] Cannot open serial {SERIAL_PORT}: {e}")
            time.sleep(1)
    sys.exit(1)

ser = init_serial()
print(f"[INFO] Serial port {SERIAL_PORT} opened.")

# ---------------- Joystick ----------------
if USE_VJOY:
    j = pyvjoy.VJoyDevice(1)
elif USE_UINPUT:
    device = uinput.Device([uinput.ABS_X + (0, 32768, 0, 0)])

# ---------------- Helpers ----------------
smoothed = 0.0
SMOOTH_FACTOR = 0.2

def map_to_axis(value):
    value = max(-32767, min(32767, value))
    return int((value + 32767) * 32768 / 65534)

# ---------------- Pairing ----------------
paired = False
while not paired:
    try:
        line = ser.readline().decode("ascii", errors="ignore").strip()
        if line.startswith("PAIRING_REQUEST:"):
            code = line.split(":", 1)[1]
            if code == PAIRING_CODE:
                print("[INFO] Pairing success!")
                ser.write(b"PAIRING_OK\n")
                paired = True
    except Exception as e:
        print(f"[ERROR] Pairing exception: {e}")
        time.sleep(1)

# ---------------- Main Loop ----------------
while True:
    try:
        line = ser.readline().decode("ascii", errors="ignore").strip()
        if not line:
            continue

        if "READ_FAILED" in line:
            print("[Arduino ERROR] READ_FAILED")
            continue

        try:
            val = int(line)
        except ValueError:
            print(f"[Arduino ERROR] Invalid value: {line}")
            continue

        smoothed = smoothed * SMOOTH_FACTOR + val * (1 - SMOOTH_FACTOR)
        axis = map_to_axis(int(smoothed))

        if USE_VJOY:
            j.set_axis(pyvjoy.HID_USAGE_X, axis)
        else:
            device.emit(uinput.ABS_X, axis, syn=True)

        # Optional debug
        print(f"Arduino: {val}, Smoothed: {int(smoothed)}, Axis: {axis}")

    except KeyboardInterrupt:
        print("Exiting...")
        break
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        time.sleep(0.01)

