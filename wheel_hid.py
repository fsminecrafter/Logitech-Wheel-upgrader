#!/usr/bin/env python3

import time
import struct
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# ---------------- CONFIG ----------------

I2C_BUS = 1                 # /dev/i2c-1
ADS_ADDRESS = 0x48          # default ADS1115 address
ADC_CHANNEL = 0             # A0
HID_DEVICE = "/dev/hidg0"   # HID gadget device

# Steering calibration (raw ADC values)
# You SHOULD adjust these after first run
ADC_MIN = 0
ADC_MAX = 32767

# Smoothing (0 = off, higher = smoother)
SMOOTHING = 0.2             # 0.0 .. 1.0

UPDATE_DELAY = 0.002        # seconds (~500 Hz)

# ----------------------------------------

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def map_range(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def main():
    # I2C setup
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c, address=ADS_ADDRESS)
    ads.gain = 2/3           # ±6.144V (safe for 5V pots)

    chan = AnalogIn(ads, ADS.P0)

    # Open HID device
    with open(HID_DEVICE, "wb", buffering=0) as hid:
        last_value = 0.0

        while True:
            raw = chan.value   # 0 .. 32767 typically

            # Clamp & map to HID range
            raw = clamp(raw, ADC_MIN, ADC_MAX)
            mapped = map_range(
                raw,
                ADC_MIN,
                ADC_MAX,
                -32767,
                32767
            )

            # Optional smoothing (low-pass filter)
            filtered = (last_value * SMOOTHING) + (mapped * (1.0 - SMOOTHING))
            last_value = filtered

            # Write HID report (16-bit signed, little-endian)
            hid.write(struct.pack("<h", int(filtered)))

            time.sleep(UPDATE_DELAY)

if __name__ == "__main__":
    main()
