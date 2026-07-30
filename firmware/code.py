# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Dumb sensor peripheral: print one raw BNO085 reading per line over USB serial.

Line format (CSV, one reading per line):

    t_ns,qi,qj,qk,qw,gx,gy,gz,ax,ay,az

- t_ns: time.monotonic_ns() on the Feather (monotonic, ns; laptop assigns
  wall-clock time on receipt)
- qi,qj,qk,qw: rotation vector quaternion, chip frame
- gx,gy,gz: calibrated gyro, rad/s, chip frame
- ax,ay,az: linear acceleration (gravity-removed on-chip), m/s², chip frame

One line is printed per fresh rotation-vector report (the stroke-analysis
clock, 100 Hz); gyro/accel fields carry the latest report of each. No
normalization here — axis remap, units, and framing are laptop-side
(plumbline.infrastructure.sensors.bno085_serial), per firmware/README.md.

The adafruit_bno08x driver is used only for startup (reset handshake and
feature enablement); the steady-state loop (sensor_loop.py, deployed
alongside this file) reads SHTP packets straight off the I2C bus and
parses the three report types inline. The driver's own packet processing
tops out near 150 reports/s and collapses above that, which is why it
can't be used for the 300 reports/s this firmware requests.

If the sensor wedges (still ACKing but returning only errors or garbage
headers, as seen when the STEMMA QT connection glitches), the loop calls
back into _init_sensor: re-instantiating the driver soft-resets the
sensor, features are re-enabled, and the stream resumes.
"""

import time
from struct import pack_into

import board
import busio
import digitalio
import displayio
from adafruit_bno08x import (
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_LINEAR_ACCELERATION,
    BNO_REPORT_ROTATION_VECTOR,
)
from adafruit_bno08x.i2c import BNO08X_I2C

import sensor_loop

_REPORT_INTERVAL_US = 10_000  # 100 Hz per feature

_FEATURES = (
    BNO_REPORT_ROTATION_VECTOR,
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_LINEAR_ACCELERATION,
)

# CircuitPython mirrors the console to the built-in TFT; scrolling it costs
# on the order of 100 ms per printed line, which would dominate the sample
# cadence. Blank the display so print() only feeds USB serial.
board.DISPLAY.root_group = displayio.Group()

# Power-cycle the shared TFT/STEMMA rail so the BNO085 boots from a known
# state — after a soft reboot it can be holding SDA low mid-transaction,
# which fails busio's pull-up check. (The unused TFT stays dark.)
_rail = digitalio.DigitalInOut(board.TFT_I2C_POWER)
_rail.switch_to_output(value=False)
time.sleep(0.1)
_rail.value = True
time.sleep(0.3)

# The BNO085 supports 400 kHz I2C; STEMMA_I2C() defaults to 100 kHz.
i2c = None
for _attempt in range(5):
    try:
        i2c = busio.I2C(board.SCL, board.SDA, frequency=400_000)
        break
    except RuntimeError:
        time.sleep(0.5)
if i2c is None:
    i2c = busio.I2C(board.SCL, board.SDA, frequency=400_000)

# adafruit_bno08x hardcodes a 50 ms (20 Hz) report interval in
# enable_feature, inlined into the .mpy, so after each enable we re-send the
# SH-2 Set Feature Command ourselves with the interval we actually want.
_SET_FEATURE_COMMAND = 0xFD
_BNO_CHANNEL_CONTROL = 2


def _init_sensor():
    """(Re-)initialize the BNO085 and return its I2C bus device.

    Instantiating the driver runs its reset handshake, which soft-resets
    the sensor — this is also the wedge-recovery path.
    """
    bno = BNO08X_I2C(i2c)
    for feature in _FEATURES:
        bno.enable_feature(feature)
        request = bytearray(17)
        request[0] = _SET_FEATURE_COMMAND
        request[1] = feature
        pack_into("<I", request, 5, _REPORT_INTERVAL_US)
        bno._send_packet(_BNO_CHANNEL_CONTROL, request)
    return bno.bus_device_obj


sensor_loop.run(_init_sensor(), time.monotonic_ns, print, reset=_init_sensor)
