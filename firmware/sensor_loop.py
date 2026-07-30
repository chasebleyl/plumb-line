# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Steady-state BNO085 raw SHTP read loop, shared by code.py and tests.

Each cycle reads one packet (4-byte header: 15-bit length incl. header,
channel, sequence; then the full packet, whose first 4 bytes are the header
again) and walks the channel-3 cargo, which is a timebase report followed
by fixed-length sensor reports. One CSV line is emitted per fresh
rotation-vector report; gyro/accel fields carry the latest report of each.

Lives in its own module (deployed to CIRCUITPY alongside code.py) so the
loop runs unchanged under CPython, where tests/test_sensor_loop.py replays
the captured I2C-glitch failure against it. Must stay CircuitPython-safe:
struct and plain functions only.
"""

from struct import unpack_from

_Q14 = 2**-14  # rotation vector unit scale
_Q9 = 2**-9  # gyro rad/s
_Q8 = 2**-8  # linear accel m/s²

_MAX_PACKET = 512


def run(dev, monotonic_ns, emit, reset=None, max_consecutive_failures=100):
    """Read SHTP packets off dev forever, emitting one line per fresh quat.

    dev: adafruit_bus_device-style I2CDevice (context manager + readinto).
    monotonic_ns: timestamp source for the emitted lines.
    emit: called with each output line (print on device).
    reset: zero-arg callable that re-initializes a wedged sensor and returns
      a fresh dev. Called after max_consecutive_failures consecutive failed
      reads (OSError, or a short/garbage header), with `# recover:` event
      lines emitted on the stream. None disables recovery.
    """
    hdr = bytearray(4)
    buf = bytearray(_MAX_PACKET)
    qi = qj = qk = qw = gx = gy = gz = ax = ay = az = 0.0
    failures = 0
    while True:
        read_ok = True
        try:
            with dev:
                dev.readinto(hdr)
            length = hdr[0] | ((hdr[1] & 0x7F) << 8)
            if length < 5:
                read_ok = False
            elif length > _MAX_PACKET:
                with dev:
                    dev.readinto(buf)  # drain oversized packet and move on
                continue
            else:
                with dev:
                    dev.readinto(buf, end=length)
        except OSError as exc:
            emit("# err: " + str(exc))
            read_ok = False
        if not read_ok:
            failures += 1
            if reset is not None and failures >= max_consecutive_failures:
                emit("# recover: %d consecutive failed reads, resetting sensor" % failures)
                try:
                    dev = reset()
                    emit("# recover: sensor reset ok")
                except OSError as exc:
                    emit("# recover: reset failed: " + str(exc))
                failures = 0
            continue
        failures = 0
        if buf[2] != 3:  # sensor input reports arrive on channel 3
            continue
        off = 4
        fresh_quat = False
        while off < length:
            rid = buf[off]
            if rid == 0x05:  # rotation vector: id,seq,status,delay + 4×int16 + acc
                i, j, k, r = unpack_from("<hhhh", buf, off + 4)
                qi = i * _Q14
                qj = j * _Q14
                qk = k * _Q14
                qw = r * _Q14
                fresh_quat = True
                off += 14
            elif rid == 0x02:  # calibrated gyro: id,seq,status,delay + 3×int16
                x, y, z = unpack_from("<hhh", buf, off + 4)
                gx = x * _Q9
                gy = y * _Q9
                gz = z * _Q9
                off += 10
            elif rid == 0x04:  # linear accel: id,seq,status,delay + 3×int16
                x, y, z = unpack_from("<hhh", buf, off + 4)
                ax = x * _Q8
                ay = y * _Q8
                az = z * _Q8
                off += 10
            elif rid == 0xFB or rid == 0xFA:  # timebase / timestamp rebase
                off += 5
            else:  # unknown report id: length unknown, skip rest of packet
                break
        if fresh_quat:
            emit(
                "%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f"
                % (monotonic_ns(), qi, qj, qk, qw, gx, gy, gz, ax, ay, az)
            )
