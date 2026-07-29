# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Tests for CsvSink: anchor preamble, deferred header, and file layout."""

import io

from plumbline.domain.models import ImuSample, SessionAnchor
from plumbline.infrastructure.sinks.csv_sink import CsvSink

HEADER = "timestamp_ns,q_x,q_y,q_z,q_w,gyro_x,gyro_y,gyro_z,accel_x,accel_y,accel_z"


def _sample(t_ns: int) -> ImuSample:
    return ImuSample(t_ns, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


def test_anchor_then_samples_produces_preamble_header_rows():
    buf = io.StringIO()
    sink = CsvSink(buf)
    sink.write_anchor(SessionAnchor(wall_time_ns=1_753_718_400_000_000_000, anchor_timestamp_ns=500))
    sink.write(_sample(500))
    sink.write(_sample(600))
    lines = buf.getvalue().splitlines()
    assert lines[0] == "# session_anchor wall_time_ns=1753718400000000000 anchor_timestamp_ns=500"
    assert lines[1] == HEADER
    assert lines[2].startswith("500,")
    assert lines[3].startswith("600,")


def test_write_without_anchor_still_writes_header_first():
    buf = io.StringIO()
    sink = CsvSink(buf)
    sink.write(_sample(500))
    lines = buf.getvalue().splitlines()
    assert lines[0] == HEADER
    assert lines[1].startswith("500,")


def test_close_with_no_writes_produces_header_only_file():
    contents = []
    buf = io.StringIO()
    buf.close = lambda: contents.append(buf.getvalue())  # capture before close
    CsvSink(buf).close()
    assert contents[0].splitlines() == [HEADER]
