# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Tests for the capture use case: session-anchor pairing and drain semantics."""

from plumbline.application.capture import run_capture
from plumbline.domain.models import ImuSample, SessionAnchor

FIXED_WALL_NS = 1_753_718_400_000_000_000


def _sample(t_ns: int) -> ImuSample:
    return ImuSample(t_ns, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


class FakeSource:
    def __init__(self, samples):
        self._samples = samples

    def samples(self):
        return iter(self._samples)


class RecordingSink:
    def __init__(self):
        self.calls = []
        self.closed = False

    def write_anchor(self, anchor):
        self.calls.append(("anchor", anchor))

    def write(self, sample):
        self.calls.append(("write", sample))

    def close(self):
        self.closed = True


def test_anchor_pairs_clock_with_first_sample_timestamp():
    sink = RecordingSink()
    count = run_capture(FakeSource([_sample(500), _sample(600)]), sink, clock=lambda: FIXED_WALL_NS)
    assert count == 2
    anchors = [c for c in sink.calls if c[0] == "anchor"]
    assert anchors == [("anchor", SessionAnchor(FIXED_WALL_NS, 500))]
    assert sink.calls[0][0] == "anchor"  # anchor precedes all writes
    assert [c[1].timestamp_ns for c in sink.calls[1:]] == [500, 600]
    assert sink.closed


def test_empty_source_writes_no_anchor_but_closes_sink():
    sink = RecordingSink()
    count = run_capture(FakeSource([]), sink, clock=lambda: FIXED_WALL_NS)
    assert count == 0
    assert sink.calls == []
    assert sink.closed
