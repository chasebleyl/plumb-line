# Firmware

CircuitPython code for the ESP32-S3 Reverse TFT Feather.

Hardware:
- Sensor: Adafruit 9-DOF Orientation IMU Fusion Breakout, BNO085 (#4754)
- Compute + display: Adafruit ESP32-S3 Reverse TFT Feather (#5691)

This firmware is the **POC 1 tethered-capture scaffold**, not the
destination (see `docs/architecture.md`, "Development topology"). During
POC 1 the onion runs on the laptop and the device acts as a dumb sensor
peripheral — read the BNO085, print one raw reading per line over USB
serial. All normalization happens laptop-side in
`plumbline.infrastructure.sensors.bno085_serial`.

From POC 2 onward the onion moves onto the chip: the `plumbline` package
deploys to the device, and this file's raw SHTP sensor loop becomes the
guts of the on-device BNO085 sensor adapter
(`infrastructure/sensors/`), with `code.py` shrinking to the
board-specific composition root that wires adapters together.

`code.py` goes on the CIRCUITPY drive.
