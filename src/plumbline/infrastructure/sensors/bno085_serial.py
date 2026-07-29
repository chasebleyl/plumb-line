# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""BNO085 adapter: parses the firmware's USB serial stream into ImuSamples.

The Feather firmware (firmware/code.py) prints one raw reading per line:

    t_ns,qi,qj,qk,qw,gx,gy,gz,ax,ay,az

This adapter owns everything BNO085-specific:
- parsing the line format; console noise (REPL banners, ANSI escapes,
  reload messages) interleaves with data lines and is skipped
- axis remap from chip frame to body frame — currently identity, pending
  the enclosure mounting decision; revisit once mounting is fixed
- unit conversion: BNO085 already reports SI (rad/s, m/s², gravity-removed
  linear acceleration); quaternion i,j,k,real maps directly to x,y,z,w
"""

from collections.abc import Iterator

import serial

from plumbline.domain.models import ImuSample

_FIELDS_PER_LINE = 11  # t_ns + quaternion(4) + gyro(3) + linear accel(3)


def parse_line(line: str) -> ImuSample | None:
    """Parse one firmware output line; None if it isn't a data line."""
    parts = line.split(",")
    if len(parts) != _FIELDS_PER_LINE:
        return None
    try:
        t_ns = int(parts[0])
        qi, qj, qk, qw, gx, gy, gz, ax, ay, az = (float(p) for p in parts[1:])
    except ValueError:
        return None
    if t_ns < 0:
        return None
    return ImuSample(
        timestamp_ns=t_ns,
        q_x=qi,
        q_y=qj,
        q_z=qk,
        q_w=qw,
        gyro_x=gx,
        gyro_y=gy,
        gyro_z=gz,
        accel_x=ax,
        accel_y=ay,
        accel_z=az,
    )


class Bno085SerialSource:
    """SampleSource over a pyserial connection to the Feather.

    The stream is treated as exhausted when the port goes silent for
    read_timeout_s (board unplugged or firmware stopped); the tethered
    firmware otherwise prints continuously.
    """

    def __init__(self, port: str, baudrate: int = 115200, read_timeout_s: float = 5.0) -> None:
        self.port = port
        self.baudrate = baudrate
        self.read_timeout_s = read_timeout_s

    def samples(self) -> Iterator[ImuSample]:
        with serial.Serial(self.port, self.baudrate, timeout=self.read_timeout_s) as ser:
            while True:
                raw = ser.readline()
                if not raw:
                    return
                sample = parse_line(raw.decode("ascii", errors="replace").strip())
                if sample is not None:
                    yield sample
