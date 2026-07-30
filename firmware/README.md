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

The firmware is two files: `code.py`, the board-specific composition
root (display blanking, rail power-cycle, I2C and driver setup), and
`sensor_loop.py`, the steady-state raw SHTP read loop. The loop lives in
its own module so it runs unchanged under CPython, where
`tests/test_sensor_loop.py` regression-tests it — including recovery
from a wedged sensor (still ACKing but returning only errors or garbage
headers after an I2C glitch): after enough consecutive failed reads the
loop reports `# recover:` on the stream and re-initializes the sensor.

From POC 2 onward the onion moves onto the chip: the `plumbline` package
deploys to the device, and the raw SHTP sensor loop becomes the guts of
the on-device BNO085 sensor adapter (`infrastructure/sensors/`), with
`code.py` shrinking to the board-specific composition root that wires
adapters together.

`code.py` and `sensor_loop.py` go on the CIRCUITPY drive.
