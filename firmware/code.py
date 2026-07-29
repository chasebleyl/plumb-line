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

No normalization here — axis remap, units, and framing are laptop-side
(plumbline.infrastructure.sensors.bno085_serial), per firmware/README.md.
"""

import time

import board
from adafruit_bno08x import (
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_LINEAR_ACCELERATION,
    BNO_REPORT_ROTATION_VECTOR,
)
from adafruit_bno08x.i2c import BNO08X_I2C

i2c = board.STEMMA_I2C()
bno = BNO08X_I2C(i2c)
bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)
bno.enable_feature(BNO_REPORT_GYROSCOPE)
bno.enable_feature(BNO_REPORT_LINEAR_ACCELERATION)

while True:
    qi, qj, qk, qw = bno.quaternion
    gx, gy, gz = bno.gyro
    ax, ay, az = bno.linear_acceleration
    print(
        "%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f"
        % (time.monotonic_ns(), qi, qj, qk, qw, gx, gy, gz, ax, ay, az)
    )
