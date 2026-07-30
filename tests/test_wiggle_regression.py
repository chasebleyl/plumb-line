# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Wiggle-test regression suite over captured firmware streams.

Replays raw serial captures (tests/fixtures/, recorded 2026-07-29 from the
live sensor assembly per docs/setup.md) through the full laptop-side
pipeline, pinning the acceptance criteria from the hardware wiggle test —
rate, cadence, freshness, quaternion sanity, motion response — without
needing the device attached.

Fixtures:
- wiggle_clean_raw.txt: 18 s of continuous wiggling, healthy stream.
- wiggle_i2c_dropout_raw.txt: capture during which the STEMMA QT connection
  glitched; clean data interleaved with firmware "# err:" lines, then the
  stream cut off when the sensor wedged.
"""

import io
from pathlib import Path

import pytest

from plumbline.application.capture import run_capture
from plumbline.infrastructure.sensors.bno085_serial import _iter_samples
from plumbline.infrastructure.sinks.csv_sink import CsvSink

FIXTURES = Path(__file__).parent / "fixtures"


class FixtureSource:
    """SampleSource replaying a captured raw serial stream from disk."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def samples(self):
        # mirror Bno085SerialSource's decode of the raw byte stream
        with open(self._path, encoding="ascii", errors="replace") as f:
            yield from _iter_samples(line.strip() for line in f)


@pytest.fixture(scope="module")
def clean():
    return list(FixtureSource(FIXTURES / "wiggle_clean_raw.txt").samples())


def _fresh_fraction(samples, attrs):
    """Fraction of consecutive sample pairs where any of attrs changed."""
    vals = [tuple(getattr(s, a) for a in attrs) for s in samples]
    return sum(1 for a, b in zip(vals, vals[1:]) if a != b) / (len(vals) - 1)


def test_clean_rate_and_cadence(clean):
    assert len(clean) == 1801
    ts = [s.timestamp_ns for s in clean]
    assert all(b > a for a, b in zip(ts, ts[1:]))
    duration_s = (ts[-1] - ts[0]) / 1e9
    rate_hz = (len(ts) - 1) / duration_s
    assert 95 < rate_hz < 105
    max_gap_ms = max((b - a) / 1e6 for a, b in zip(ts, ts[1:]))
    assert max_gap_ms < 20


def test_clean_quaternion_normalized(clean):
    for s in clean:
        norm = (s.q_x**2 + s.q_y**2 + s.q_z**2 + s.q_w**2) ** 0.5
        assert abs(norm - 1.0) < 0.001


def test_clean_channels_fresh(clean):
    # one line per fresh rotation vector; gyro rides along at the same
    # 100 Hz, accel reports arrive slightly slower (~96 Hz observed)
    assert _fresh_fraction(clean, ("q_x", "q_y", "q_z", "q_w")) > 0.99
    assert _fresh_fraction(clean, ("gyro_x", "gyro_y", "gyro_z")) > 0.99
    assert _fresh_fraction(clean, ("accel_x", "accel_y", "accel_z")) > 0.90


def test_clean_motion_response(clean):
    gyro_peak = max((s.gyro_x**2 + s.gyro_y**2 + s.gyro_z**2) ** 0.5 for s in clean)
    accel_peak = max((s.accel_x**2 + s.accel_y**2 + s.accel_z**2) ** 0.5 for s in clean)
    assert gyro_peak > 1.0  # rad/s
    assert accel_peak > 2.0  # m/s²
    for attr in ("q_x", "q_y", "q_z", "q_w"):
        vals = [getattr(s, attr) for s in clean]
        assert max(vals) - min(vals) > 0.2


def test_clean_full_pipeline_to_csv():
    contents = []
    buf = io.StringIO()
    buf.close = lambda: contents.append(buf.getvalue())  # capture before close
    count = run_capture(
        FixtureSource(FIXTURES / "wiggle_clean_raw.txt"),
        CsvSink(buf),
        clock=lambda: 1_753_718_400_000_000_000,
    )
    assert count == 1801
    lines = contents[0].splitlines()
    assert lines[0].startswith("# session_anchor wall_time_ns=1753718400000000000")
    assert lines[1] == "timestamp_ns,q_x,q_y,q_z,q_w,gyro_x,gyro_y,gyro_z,accel_x,accel_y,accel_z"
    assert len(lines) == 2 + 1801


def test_dropout_yields_only_valid_samples():
    samples = list(FixtureSource(FIXTURES / "wiggle_i2c_dropout_raw.txt").samples())
    assert len(samples) == 253  # 308 raw lines, 55 of them "# err:" noise
    ts = [s.timestamp_ns for s in samples]
    assert all(b > a for a, b in zip(ts, ts[1:]))
