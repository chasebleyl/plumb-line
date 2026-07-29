# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Ports — the interfaces infrastructure adapters must satisfy.

Duck-typed: adapters implement these by shape, no inheritance required.
The classes here document the contract (plain classes, not
typing.Protocol, per the portability rule in architecture.md — this
module must run unchanged under CircuitPython).
"""


class SampleSource:
    """A source of normalized IMU samples (a sensor, a replay file, ...).

    Adapters own the sensor-specific work: unit conversion to SI,
    axis remap into the body frame, and timestamping. Samples they
    emit must satisfy the normalization contract documented in
    plumbline.domain.models.
    """

    def samples(self):
        """Yield ImuSample values in timestamp order until the source is exhausted."""
        raise NotImplementedError


class SampleSink:
    """A destination for normalized IMU samples (CSV file, live plot, ...)."""

    def write_anchor(self, anchor):
        """Record the session's wall-clock anchor; called at most once, before any write."""
        raise NotImplementedError

    def write(self, sample):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
