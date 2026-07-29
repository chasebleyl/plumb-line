# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Capture use case: stream samples from a source into a sink."""

import time

from plumbline.domain.models import SessionAnchor


def run_capture(source, sink, clock=None) -> int:
    """Drain a SampleSource into a SampleSink. Returns the number of samples captured.

    On the first sample, pairs the wall clock with the sample's board
    timestamp and records it via sink.write_anchor (contract item 4:
    wall-clock is session-level metadata, once per capture file).

    clock is a zero-arg callable returning integer nanoseconds; defaults
    to time.time_ns, resolved lazily because CircuitPython lacks it — the
    on-device composition root must pass its own clock.
    """
    if clock is None:
        clock = time.time_ns
    count = 0
    try:
        samples = iter(source.samples())
        first = next(samples, None)
        if first is not None:
            sink.write_anchor(SessionAnchor(clock(), first.timestamp_ns))
            sink.write(first)
            count = 1
            for sample in samples:
                sink.write(sample)
                count += 1
    finally:
        sink.close()
    return count
