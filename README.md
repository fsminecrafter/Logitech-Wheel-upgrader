# Logitech-Wheel-upgrader
This is the software for the upgrade of the Logitech gaming wheel formula with vibrations. 
This software is made for Armbian (:

### ================ PRE-SETUP CHECKLIST ================

Before continuing, make sure:

1) I2C is enabled
   - Run: sudo armbian-config
   - System → Hardware → Enable I2C
   - Reboot after enabling

2) USB HID gadget is set up
   - dwc2 + libcomposite enabled
   - /dev/hidg0 exists
   - The Le Potato is connected via USB OTG to your PC

3) You are running this as a normal user
   (sudo will be requested when needed)
