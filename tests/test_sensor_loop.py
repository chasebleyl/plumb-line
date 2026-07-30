# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Firmware SHTP loop tests, including the wedged-sensor recovery regression.

Drives firmware/sensor_loop.py under CPython with a scripted fake I2C
device. The failure script mirrors the live 2026-07-29 wiggle-test capture
(tests/fixtures/wiggle_i2c_dropout_raw.txt): healthy stream, then a storm
of [Errno 5] reads while the STEMMA QT connection glitched, then a wedged
sensor that still ACKs but returns only garbage/short headers — which the
original firmware spun on silently forever.
"""

import itertools
import sys
from pathlib import Path
from struct import pack

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "firmware"))

from sensor_loop import run  # noqa: E402  (needs the firmware dir on sys.path)

from plumbline.infrastructure.sensors.bno085_serial import parse_line

# fixture shape: 55 consecutive "# err: [Errno 5]" lines, then silence
ERRNO5_STORM_LEN = 55

WEDGE = "wedge"  # sensor ACKs but every header read returns zeros, forever


class ScriptDone(Exception):
    """Fake device ran out of scripted events; ends the (infinite) loop."""


class StillWedged(Exception):
    """Loop kept reading a wedged sensor far past any recovery threshold."""


def _channel3_packet(reports: bytes, seq: int = 0) -> bytes:
    length = 4 + 5 + len(reports)
    header = bytes([length & 0xFF, length >> 8, 3, seq])
    timebase = b"\xfb\x00\x00\x00\x00"
    return header + timebase + reports


def _rv_packet(i: int, j: int, k: int, r: int, seq: int = 0) -> bytes:
    """Rotation-vector packet; args are raw Q14 int16s."""
    report = b"\x05\x00\x03\x00" + pack("<hhhh", i, j, k, r) + b"\x00\x00"
    return _channel3_packet(report, seq)


class FakeI2cDevice:
    """adafruit_bus_device-style I2CDevice replaying a scripted event list.

    Events: a bytes packet (served as a 4-byte header read, then the full
    body read), an OSError (raised on the read), or WEDGE (never consumed:
    every subsequent header read returns zeros, until recover()).
    """

    def __init__(self, events, wedge_limit=10_000):
        self._events = list(events)
        self._pending_body = None
        self._wedge_reads = 0
        self._wedge_limit = wedge_limit
        self.resets = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def readinto(self, buf, end=None):
        if self._pending_body is not None:
            n = end if end is not None else len(buf)
            buf[:n] = self._pending_body[:n]
            self._pending_body = None
            return
        if not self._events:
            raise ScriptDone
        event = self._events[0]
        if event is WEDGE:
            self._wedge_reads += 1
            if self._wedge_reads > self._wedge_limit:
                raise StillWedged(
                    f"{self._wedge_reads} header reads off a wedged sensor "
                    "with no recovery attempt"
                )
            buf[0:4] = b"\x00\x00\x00\x00"
            return
        self._events.pop(0)
        if isinstance(event, OSError):
            raise event
        buf[0:4] = event[:4]
        if len(event) == 4:  # bare header (empty read), no body follows
            return
        self._pending_body = event

    def recover(self, events):
        """What a sensor soft-reset does: wedge clears, stream resumes."""
        self._events = list(events)
        self._wedge_reads = 0
        self.resets += 1


def _mono_ns():
    counter = itertools.count(1)
    return lambda: next(counter) * 10_000_000


def _run_to_script_end(dev, reset=None, **kwargs):
    lines = []
    with pytest.raises(ScriptDone):
        run(dev, _mono_ns(), lines.append, reset=reset, **kwargs)
    return lines


def _data_lines(lines):
    return [line for line in lines if parse_line(line) is not None]


def test_healthy_packet_emits_parseable_line():
    reports = (
        b"\x02\x00\x03\x00" + pack("<hhh", -512, 1024, 256)  # gyro, Q9
        + b"\x04\x00\x03\x00" + pack("<hhh", 128, -256, 64)  # accel, Q8
        + b"\x05\x00\x03\x00" + pack("<hhhh", 8192, -4096, 2048, 16384) + b"\x00\x00"
    )
    lines = _run_to_script_end(FakeI2cDevice([_channel3_packet(reports)]))
    assert len(lines) == 1
    sample = parse_line(lines[0])
    assert sample is not None
    assert (sample.q_x, sample.q_y, sample.q_z, sample.q_w) == (0.5, -0.25, 0.125, 1.0)
    assert (sample.gyro_x, sample.gyro_y, sample.gyro_z) == (-1.0, 2.0, 0.5)
    assert (sample.accel_x, sample.accel_y, sample.accel_z) == (0.5, -1.0, 0.25)


def test_wedged_sensor_resets_and_stream_resumes():
    # the captured failure: clean data, an [Errno 5] storm, then wedged
    dev = FakeI2cDevice(
        [_rv_packet(16384, 0, 0, 0, seq=n) for n in range(3)]
        + [OSError(5, "Input/output error")] * ERRNO5_STORM_LEN
        + [WEDGE]
    )
    post_reset = [_rv_packet(0, 16384, 0, 0, seq=n) for n in range(5)]

    def reset():
        dev.recover(post_reset)
        return dev

    lines = _run_to_script_end(dev, reset=reset)

    assert dev.resets == 1
    recover_at = next(i for i, line in enumerate(lines) if line.startswith("# recover"))
    assert len(_data_lines(lines[:recover_at])) == 3  # pre-glitch stream intact
    assert len(_data_lines(lines[recover_at:])) == 5  # stream resumed after reset
    errs = [line for line in lines if line.startswith("# err:")]
    assert len(errs) == ERRNO5_STORM_LEN
    assert errs[0] == "# err: [Errno 5] Input/output error"


def test_transient_noise_below_threshold_does_not_reset():
    empty_read = b"\x00\x00\x00\x00"
    dev = FakeI2cDevice(
        [_rv_packet(16384, 0, 0, 0)]
        + [empty_read] * 99
        + [_rv_packet(16384, 0, 0, 0)]
        + [OSError(5, "Input/output error")] * 99
        + [_rv_packet(16384, 0, 0, 0)]
    )
    lines = _run_to_script_end(dev, reset=lambda: dev, max_consecutive_failures=100)
    assert dev.resets == 0
    assert not [line for line in lines if line.startswith("# recover")]
    assert len(_data_lines(lines)) == 3


def test_reset_failure_retries_instead_of_crashing():
    # bus still glitched when the threshold hits: first reset raises, the
    # loop must keep going and succeed on a later attempt
    dev = FakeI2cDevice([WEDGE])
    post_reset = [_rv_packet(0, 16384, 0, 0)]
    attempts = []

    def reset():
        attempts.append(True)
        if len(attempts) == 1:
            raise OSError(5, "Input/output error")
        dev.recover(post_reset)
        return dev

    lines = _run_to_script_end(dev, reset=reset, max_consecutive_failures=100)
    assert len(attempts) == 2
    assert len(_data_lines(lines)) == 1
