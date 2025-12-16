```sudo -i```

```cd /sys/kernel/config/usb_gadget```

```
mkdir wheel
cd wheel
```
```
echo 0x1d6b > idVendor      # Linux Foundation
echo 0x0104 > idProduct     # HID gadget
echo 0x0100 > bcdDevice
echo 0x0200 > bcdUSB
```
```
mkdir -p strings/0x409
echo "0001"        > strings/0x409/serialnumber
echo "Le Potato"  > strings/0x409/manufacturer
echo "Wheel HID"  > strings/0x409/product
```

```
mkdir -p functions/hid.usb0
```

```
echo 1 > functions/hid.usb0/protocol
echo 1 > functions/hid.usb0/subclass
echo 2 > functions/hid.usb0/report_length
```

```
echo -ne \
'\x05\x01'\
'\x09\x04'\
'\xA1\x01'\
'\x09\x01'\
'\xA1\x00'\
'\x05\x01'\
'\x09\x31'\
'\x16\x01\x80'\
'\x26\xFF\x7F'\
'\x75\x10'\
'\x95\x01'\
'\x81\x02'\
'\xC0'\
'\xC0' \
> functions/hid.usb0/report_desc
```

```
mkdir -p configs/c.1
mkdir -p configs/c.1/strings/0x409
echo "Wheel Config" > configs/c.1/strings/0x409/configuration
echo 250 > configs/c.1/MaxPower
```

```
ln -s functions/hid.usb0 configs/c.1/
```

```
echo fe800000.usb > UDC
```
Dont forget to change the fe800000.usb to the your value.
