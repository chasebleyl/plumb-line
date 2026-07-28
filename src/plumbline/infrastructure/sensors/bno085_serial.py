# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""BNO085 adapter: parses the firmware's USB serial stream into ImuSamples.

The Feather firmware (firmware/code.py) prints one raw reading per line.
This adapter owns everything BNO085-specific:
- parsing the line format
- axis remap from chip frame to body frame (depends on enclosure mounting)
- unit conversion (BNO085 already reports SI; quaternion i,j,k,real maps
  directly to x,y,z,w)
"""

from collections.abc import Iterator

from plumbline.domain.models import ImuSample


class Bno085SerialSource:
    """SampleSource over a pyserial connection to the Feather."""

    def __init__(self, port: str, baudrate: int = 115200) -> None:
        self.port = port
        self.baudrate = baudrate

    def samples(self) -> Iterator[ImuSample]:
        raise NotImplementedError("pending: line format + axis remap once enclosure mounting is fixed")
