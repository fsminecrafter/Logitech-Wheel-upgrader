#!/usr/bin/env python3

import os
import sys
import time
import json
import subprocess
import termios
import tty
import select

CONFIG_DIR = os.path.expanduser("~/.wheel_hid")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
VENV_DIR = os.path.join(CONFIG_DIR, "joystickenv")

DEFAULT_I2C_BUS = "1"

# -------------------------------------------------

def preflight_info():
    print("""
================ PRE-SETUP CHECKLIST ================

Before continuing, make sure:

1) I2C is enabled
   - Run: sudo armbian-config
   - System → Hardware → Enable I2C
   - Reboot after enabling

2) USB HID gadget is set up
   - libcomposite enabled
   - /dev/hidg0 exists
   - The Le Potato is connected via USB OTG to your PC

3) You are running this as a normal user
   (sudo will be requested when needed)

=====================================================
""")

def ask_yn(prompt):
    while True:
        ans = input(f"{prompt} (y/N): ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("", "n", "no"):
            return False

# -------------------------------------------------
# Dependency handling
# -------------------------------------------------

def pip_install(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0

def ensure_venv():
    if not os.path.exists(VENV_DIR):
        print("Creating virtual environment: joystickenv")
        subprocess.run(["python3", "-m", "venv", VENV_DIR], check=True)

    pip = os.path.join(VENV_DIR, "bin", "pip")
    print("Installing dependencies into joystickenv...")
    subprocess.run([pip, "install", "adafruit-circuitpython-ads1x15"], check=True)

def install_dependencies():
    print("Installing system dependencies...")
    subprocess.run(["sudo", "apt", "update"], check=False)
    subprocess.run(
        ["sudo", "apt", "install", "-y",
         "python3-pip", "python3-smbus", "i2c-tools", "python3-venv"],
        check=False
    )

    print("Trying system pip install...")
    ok = pip_install([
        "pip3", "install", "--break-system-packages",
        "adafruit-circuitpython-ads1x15"
    ])

    if not ok:
        print("System pip failed.")
        ensure_venv()
    else:
        print("System pip install successful.")

# -------------------------------------------------
# Config helpers
# -------------------------------------------------

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# -------------------------------------------------
# I2C helpers
# -------------------------------------------------

def scan_i2c():
    result = subprocess.run(
        ["i2cdetect", "-y", DEFAULT_I2C_BUS],
        capture_output=True, text=True
    )
    found = []
    for line in result.stdout.splitlines():
        for p in line.split()[1:]:
            if p != "--":
                try:
                    found.append(int(p, 16))
                except:
                    pass
    return found

def find_ads1115():
    print("Set the pot to MAX...")
    time.sleep(2)
    addrs = scan_i2c()
    if not addrs:
        print("Could not be found")
        print("Set the pot to MIN in 5 seconds.")
        time.sleep(5)
        addrs = scan_i2c()
        if not addrs:
            print("Could not be found")
            return None
    return addrs[0]

# -------------------------------------------------
# ADC reading (imports delayed)
# -------------------------------------------------

def read_adc(addr):
    import board, busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn

    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c, address=addr)
    ads.gain = 2 / 3
    chan = AnalogIn(ads, ADS.P0)
    return chan.value

# -------------------------------------------------

def main():
    preflight_info()

    if not ask_yn("Continue setup?"):
        sys.exit(0)

    if not ask_yn("Have you enabled I2C?"):
        print("Enable I2C first, then re-run setup.")
        sys.exit(1)

    install_dependencies()

    cfg = load_config()

    if "address" in cfg and ask_yn("Load saved sensor address?"):
        addr = int(cfg["address"], 16)
        print(f"Using saved address: {hex(addr)}")
    else:
        if ask_yn("Do you know the sensor address?"):
            addr = int(input("Enter address (hex): "), 16)
        else:
            while True:
                addr = find_ads1115()
                if addr is not None:
                    print(f"Address found: {hex(addr)}")
                    break
                if not ask_yn("Retry?"):
                    sys.exit(1)

        if ask_yn("Save address?"):
            cfg["address"] = hex(addr)
            save_config(cfg)

    if ask_yn("Start calibration?"):
        cal = {}
        input("Set pot to MAX, press Enter")
        cal["max"] = read_adc(addr)
        input("Set pot to MIN, press Enter")
        cal["min"] = read_adc(addr)
        input("Set pot to CENTER, press Enter")
        cal["center"] = read_adc(addr)

        if ask_yn("Save calibration?"):
            cfg["calibration"] = cal
            cfg["address"] = hex(addr)
            save_config(cfg)

    print("Setup complete.")
    print(f"Virtualenv used: {'YES' if os.path.exists(VENV_DIR) else 'NO'}")

if __name__ == "__main__":
    main()
