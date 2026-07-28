# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Ports — the interfaces infrastructure adapters must satisfy.

Structural typing via Protocol: adapters implement these by shape,
no inheritance required.
"""

from collections.abc import Iterator
from typing import Protocol

from plumbline.domain.models import ImuSample


class SampleSource(Protocol):
    """A source of normalized IMU samples (a sensor, a replay file, ...).

    Adapters own the sensor-specific work: unit conversion to SI,
    axis remap into the body frame, and timestamping. Samples they
    emit must satisfy the normalization contract documented in
    plumbline.domain.models.
    """

    def samples(self) -> Iterator[ImuSample]:
        """Yield samples in timestamp order until the source is exhausted."""
        ...


class SampleSink(Protocol):
    """A destination for normalized IMU samples (CSV file, live plot, ...)."""

    def write(self, sample: ImuSample) -> None: ...

    def close(self) -> None: ...
