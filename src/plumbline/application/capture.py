# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Capture use case: stream samples from a source into a sink."""

from plumbline.application.ports import SampleSink, SampleSource


def run_capture(source: SampleSource, sink: SampleSink) -> int:
    """Drain source into sink. Returns the number of samples captured."""
    count = 0
    try:
        for sample in source.samples():
            sink.write(sample)
            count += 1
    finally:
        sink.close()
    return count
