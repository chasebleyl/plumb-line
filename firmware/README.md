# Firmware

CircuitPython code for the ESP32-S3 Reverse TFT Feather.

Hardware:
- Sensor: Adafruit 9-DOF Orientation IMU Fusion Breakout, BNO085 (#4754)
- Compute + display: Adafruit ESP32-S3 Reverse TFT Feather (#5691)

The firmware sits **outside** the onion architecture (see
`docs/architecture.md`): CircuitPython lacks `dataclasses`, `typing`, and
most of the stdlib, so it cannot run the core package. Instead it acts as a
dumb sensor peripheral — read the BNO085, print one raw reading per line
over USB serial. All normalization happens laptop-side in
`plumbline.infrastructure.sensors.bno085_serial`.

`code.py` goes on the CIRCUITPY drive.
