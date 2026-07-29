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
feature enablement); the steady-state loop reads SHTP packets straight off
the I2C bus and parses the three report types inline. The driver's own
packet processing tops out near 150 reports/s and collapses above that,
which is why it can't be used for the 300 reports/s this firmware requests.
"""

import time
from struct import pack_into, unpack_from

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

bno = BNO08X_I2C(i2c)

# adafruit_bno08x hardcodes a 50 ms (20 Hz) report interval in
# enable_feature, inlined into the .mpy, so after each enable we re-send the
# SH-2 Set Feature Command ourselves with the interval we actually want.
_SET_FEATURE_COMMAND = 0xFD
_BNO_CHANNEL_CONTROL = 2

for _feature in _FEATURES:
    bno.enable_feature(_feature)
    _request = bytearray(17)
    _request[0] = _SET_FEATURE_COMMAND
    _request[1] = _feature
    pack_into("<I", _request, 5, _REPORT_INTERVAL_US)
    bno._send_packet(_BNO_CHANNEL_CONTROL, _request)

# Steady-state raw SHTP loop. Each cycle reads one packet (4-byte header:
# 15-bit length incl. header, channel, sequence; then the full packet, whose
# first 4 bytes are the header again) and walks the channel-3 cargo, which
# is a timebase report followed by fixed-length sensor reports.
_dev = bno.bus_device_obj
_hdr = bytearray(4)
_buf = bytearray(512)

_Q14 = 2**-14  # rotation vector unit scale
_Q9 = 2**-9  # gyro rad/s
_Q8 = 2**-8  # linear accel m/s²

qi = qj = qk = qw = gx = gy = gz = ax = ay = az = 0.0
_mono_ns = time.monotonic_ns
while True:
    try:
        with _dev:
            _dev.readinto(_hdr)
        length = _hdr[0] | ((_hdr[1] & 0x7F) << 8)
        if length < 5:
            continue
        if length > 512:
            with _dev:
                _dev.readinto(_buf)  # drain oversized packet and move on
            continue
        with _dev:
            _dev.readinto(_buf, end=length)
    except OSError as exc:
        print("# err:", exc)
        continue
    if _buf[2] != 3:  # sensor input reports arrive on channel 3
        continue
    off = 4
    fresh_quat = False
    while off < length:
        rid = _buf[off]
        if rid == 0x05:  # rotation vector: id,seq,status,delay + 4×int16 + acc
            i, j, k, r = unpack_from("<hhhh", _buf, off + 4)
            qi = i * _Q14
            qj = j * _Q14
            qk = k * _Q14
            qw = r * _Q14
            fresh_quat = True
            off += 14
        elif rid == 0x02:  # calibrated gyro: id,seq,status,delay + 3×int16
            x, y, z = unpack_from("<hhh", _buf, off + 4)
            gx = x * _Q9
            gy = y * _Q9
            gz = z * _Q9
            off += 10
        elif rid == 0x04:  # linear accel: id,seq,status,delay + 3×int16
            x, y, z = unpack_from("<hhh", _buf, off + 4)
            ax = x * _Q8
            ay = y * _Q8
            az = z * _Q8
            off += 10
        elif rid == 0xFB or rid == 0xFA:  # timebase / timestamp rebase
            off += 5
        else:  # unknown report id: length unknown, skip rest of packet
            break
    if fresh_quat:
        print(
            "%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f"
            % (_mono_ns(), qi, qj, qk, qw, gx, gy, gz, ax, ay, az)
        )
