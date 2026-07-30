# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Tests for CsvReplaySource: round-trip with CsvSink, anchor skipping, empty files."""

from plumbline.domain.models import ImuSample, SessionAnchor
from plumbline.infrastructure.sinks.csv_sink import CsvSink
from plumbline.infrastructure.sources.csv_replay import CsvReplaySource


def _sample(t_ns: int) -> ImuSample:
    return ImuSample(t_ns, 0.1, 0.2, 0.3, 0.9, 1.5, -2.5, 0.0, 9.0, -0.25, 0.125)


def test_round_trips_samples_written_by_csv_sink(tmp_path):
    path = tmp_path / "capture.csv"
    written = [_sample(500), _sample(600), _sample(700)]
    with open(path, "w", newline="") as file:
        sink = CsvSink(file)
        sink.write_anchor(SessionAnchor(wall_time_ns=1_753_718_400_000_000_000, anchor_timestamp_ns=500))
        for sample in written:
            sink.write(sample)

    assert list(CsvReplaySource(str(path)).samples()) == written


def test_replays_file_without_anchor_comment(tmp_path):
    path = tmp_path / "capture.csv"
    with open(path, "w", newline="") as file:
        sink = CsvSink(file)
        sink.write(_sample(500))

    replayed = list(CsvReplaySource(str(path)).samples())
    assert replayed == [_sample(500)]


def test_header_only_file_yields_nothing(tmp_path):
    path = tmp_path / "capture.csv"
    with open(path, "w", newline="") as file:
        CsvSink(file).close()

    assert list(CsvReplaySource(str(path)).samples()) == []
