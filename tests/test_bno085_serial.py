# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Parser tests for the BNO085 serial adapter, using real line shapes
captured from the firmware stream (see docs/setup.md)."""

from plumbline.infrastructure.sensors.bno085_serial import parse_line

VALID = "1663843566905,-0.995728,-0.088928,-0.022217,0.011780,-0.003906,-0.003906,0.001953,0.000000,0.003906,0.000000"


def test_valid_line_parses_all_fields():
    s = parse_line(VALID)
    assert s is not None
    assert s.timestamp_ns == 1663843566905
    assert (s.q_x, s.q_y, s.q_z, s.q_w) == (-0.995728, -0.088928, -0.022217, 0.011780)
    assert (s.gyro_x, s.gyro_y, s.gyro_z) == (-0.003906, -0.003906, 0.001953)
    assert (s.accel_x, s.accel_y, s.accel_z) == (0.000000, 0.003906, 0.000000)


def test_console_noise_is_skipped():
    for noise in [
        "",
        "Adafruit CircuitPython 10.2.1 on 2026-05-13; Adafruit Feather ESP32-S3 Reverse TFT with ESP32S3",
        "Auto-reload is on. Simply save files over USB to run them or enter REPL to disable.",
        "code.py output:",
        "Traceback (most recent call last):",
        '  File "code.py", line 38, in <module>',
        "\x1b]0;\U0001f40dWi-Fi: off | BLE:Off | code.py | 10.2.1\x1b\\" + VALID,  # ANSI-prefixed data line
    ]:
        assert parse_line(noise) is None


def test_wrong_field_count_is_skipped():
    # old 8-field format (pre linear-acceleration)
    assert parse_line("916630798352,0.0,0.0,0.0,0.0,0.0,0.0,0.0") is None
    # truncated line (partial read mid-stream)
    assert parse_line(VALID.rsplit(",", 1)[0]) is None


def test_non_numeric_fields_are_skipped():
    assert parse_line("abc," + VALID.split(",", 1)[1]) is None
    assert parse_line(VALID.replace("0.011780", "nope")) is None
