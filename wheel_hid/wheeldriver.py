#!/usr/bin/env python3
import sys
import time
import serial
import argparse
import platform

# Platform-dependent libraries
if platform.system() == "Windows":
    import pyvjoy
else:
    import uinput

# ------------------------
# Argument parsing
# ------------------------
parser = argparse.ArgumentParser(description="Wheel HID PC Receiver")
parser.add_argument("--debug", action="store_true", help="Show axis percentages and debug info")
parser.add_argument("--auto", action="store_true", help="Automatically pair and start")
parser.add_argument("--port", type=str, default=None, help="Serial port (e.g. COM3 or /dev/ttyUSB0)")
args = parser.parse_args()

DEBUG = args.debug

# ------------------------
# Axis Settings
# ------------------------
AXES_CONFIG = {
    "A": {"name": "A_axis", "centred": True},
    "B": {"name": "B_axis", "centred": False},
}

SMOOTHING = 0.2
smoothed = {axis: 0.0 for axis in AXES_CONFIG}

# ------------------------
# Mapping functions
# ------------------------
def map_to_percent(value, min_val, max_val, centred=True):
    if max_val == min_val:
        return 0.0
    pct = (value - min_val) / (max_val - min_val)
    if centred:
        return pct * 2.0 - 1.0  # -1 to 1
    return pct  # 0 to 1

def apply_smoothing(old, new):
    return old * SMOOTHING + new * (1.0 - SMOOTHING)

# ------------------------
# Serial & Pairing
# ------------------------
SERIAL_BAUD = 115200
PAIRING_CODE = "FSMINEWHEEL123"  # Can be randomized
serial_port = None

def connect_serial(port=None):
    import serial.tools.list_ports
    if port:
        return serial.Serial(port, SERIAL_BAUD, timeout=0.1)
    # Auto-detect
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        try:
            s = serial.Serial(p.device, SERIAL_BAUD, timeout=0.1)
            return s
        except:
            continue
    raise RuntimeError("No serial port found")

def perform_pairing(ser):
    print("Pairing request sent. Waiting for response...")
    ser.write(f"PAIR:{PAIRING_CODE}\n".encode())
    t0 = time.time()
    while True:
        if ser.in_waiting:
            line = ser.readline().decode().strip()
            if line == f"PAIR_OK:{PAIRING_CODE}":
                print("Pairing successful!")
                return True
        if time.time() - t0 > 10:
            print("Pairing timeout. Retry.")
            return False

# ------------------------
# HID Setup
# ------------------------
if platform.system() == "Windows":
    j = pyvjoy.VJoyDevice(1)
else:
    device = uinput.Device([uinput.ABS_X + (0, 32767, 0, 0)])

# ------------------------
# Main Loop
# ------------------------
def main():
    global smoothed
    while True:
        try:
            ser = connect_serial(args.port)
            if not args.auto:
                if not perform_pairing(ser):
                    time.sleep(2)
                    continue
            print("Receiving data...")
            min_val = 0
            max_val = 65535
            while True:
                line = ser.readline().decode().strip()
                if not line:
                    continue
                try:
                    value = int(line)
                except:
                    continue
                # Map & smooth
                for axis_key, axis_cfg in AXES_CONFIG.items():
                    pct = map_to_percent(value, min_val, max_val, axis_cfg["centred"])
                    smoothed[axis_key] = apply_smoothing(smoothed[axis_key], pct)
                    # Send to HID
                    scaled = int((smoothed[axis_key]+1)/2*32767) if axis_cfg["centred"] else int(smoothed[axis_key]*32767)
                    if platform.system() == "Windows":
                        j.set_axis(pyvjoy.HID_USAGE_X, scaled)
                    else:
                        device.emit(uinput.ABS_X, scaled, syn=True)
                    if DEBUG:
                        print(f"{axis_cfg['name']}: {smoothed[axis_key]*100:.2f}%")
        except KeyboardInterrupt:
            print("Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
