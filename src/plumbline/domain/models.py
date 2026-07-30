# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""Core data types and the normalization contract they obey.

Measurements are normalized from the sensor into these core types so the
same swing-analysis logic can be reused across many distinct sensors.
Sensor-specific code lives only in a thin adapter; everything downstream
consumes the core types::

    BNO085 ────→ Bno085Adapter ─┐
    FutureSensor → OtherAdapter ─┼─→ ImuSample stream → swing detection / analysis
                                 ┘

ImuSample is modeled on ROS ``sensor_msgs/Imu``, the de facto
industry-standard sensor-agnostic IMU record (see REP 103,
http://docs.ros.org/en/independent/api/rep/html/rep-0103.html).

Normalization contract — every adapter must emit ImuSample values obeying:

1. SI units only — angular velocity in rad/s, acceleration in m/s²,
   timestamps in nanoseconds. Sensors reporting deg/s or g are converted
   in the adapter.
2. Quaternion order is (x, y, z, w) — Hamilton convention, matching ROS.
   The BNO085's (i, j, k, real) output already maps directly.
3. Fixed body frame — right-handed, X forward (toward the target line),
   Y left, Z up (per REP 103). Each adapter owns the axis remap from its
   sensor's mounting orientation to this frame; core logic never knows
   how the sensor was mounted.
4. Timestamps are monotonic nanosecond integers, not datetime. Swing
   analysis only needs deltas; wall-clock time is session-level metadata
   recorded once per capture file.
5. Acceleration is gravity-removed (linear acceleration). If a sensor
   only provides raw acceleration, its adapter subtracts gravity using
   the orientation quaternion.

Orientation is stored ONLY as a quaternion. Yaw/pitch/roll (Euler angles)
are derived at analysis/display time (see analysis.py) — never stored,
because Euler angles have 24 ambiguous conventions and hit gimbal lock
near ±90° pitch (a putter shaft pointed upward sits exactly there).

Plain classes, not dataclasses: this module must run unchanged under
CircuitPython (architecture.md "Portability rule").
"""


class SessionAnchor:
    """Session-level wall-clock metadata (contract item 4), one per capture file.

    Pairs the laptop wall clock with the board's monotonic clock at the
    moment the first sample of a session arrives, so any sample's wall-clock
    time can be recovered as wall_time_ns + (timestamp_ns - anchor_timestamp_ns).
    """

    def __init__(self, wall_time_ns: int, anchor_timestamp_ns: int):
        self.wall_time_ns = wall_time_ns  # laptop time.time_ns() at first-sample receipt
        self.anchor_timestamp_ns = anchor_timestamp_ns  # that sample's board-monotonic timestamp_ns

    def __eq__(self, other):
        return (
            isinstance(other, SessionAnchor)
            and self.wall_time_ns == other.wall_time_ns
            and self.anchor_timestamp_ns == other.anchor_timestamp_ns
        )

    def __repr__(self):
        return f"SessionAnchor(wall_time_ns={self.wall_time_ns}, anchor_timestamp_ns={self.anchor_timestamp_ns})"


class ImuSample:
    """One normalized IMU reading. Sensor-agnostic.

    Contract (module docstring):
    - SI units: rad/s, m/s², nanosecond timestamps
    - Quaternion stored (x, y, z, w), Hamilton convention
    - Body frame: X toward target, Y left, Z up (right-handed)
    - Acceleration is gravity-removed (linear acceleration)
    """

    # Attribute names in constructor order; sinks rely on this for row layout.
    FIELDS = (
        "timestamp_ns",
        "q_x",
        "q_y",
        "q_z",
        "q_w",
        "gyro_x",
        "gyro_y",
        "gyro_z",
        "accel_x",
        "accel_y",
        "accel_z",
    )

    def __init__(
        self,
        timestamp_ns: int,
        q_x: float,
        q_y: float,
        q_z: float,
        q_w: float,
        gyro_x: float,
        gyro_y: float,
        gyro_z: float,
        accel_x: float,
        accel_y: float,
        accel_z: float,
    ):
        self.timestamp_ns = timestamp_ns
        self.q_x = q_x
        self.q_y = q_y
        self.q_z = q_z
        self.q_w = q_w
        self.gyro_x = gyro_x
        self.gyro_y = gyro_y
        self.gyro_z = gyro_z
        self.accel_x = accel_x
        self.accel_y = accel_y
        self.accel_z = accel_z

    def __eq__(self, other):
        if not isinstance(other, ImuSample):
            return NotImplemented
        return all(getattr(self, name) == getattr(other, name) for name in self.FIELDS)

    def __repr__(self):
        args = ", ".join(f"{name}={getattr(self, name)!r}" for name in self.FIELDS)
        return f"ImuSample({args})"


class SwingInterval:
    """Starting & ending data over a time segment."""

    def __init__(
        self,
        start_sample: ImuSample,
        end_sample: ImuSample,
        elapsed_time_ms: float,
        intermediary_samples=None,
    ):
        self.start_sample = start_sample
        self.end_sample = end_sample
        self.elapsed_time_ms = elapsed_time_ms
        self.intermediary_samples = [] if intermediary_samples is None else intermediary_samples

    def __repr__(self):
        return (
            f"SwingInterval(start_sample={self.start_sample!r}, end_sample={self.end_sample!r}, "
            f"elapsed_time_ms={self.elapsed_time_ms!r}, "
            f"intermediary_samples={self.intermediary_samples!r})"
        )


class Swing:
    """Encapsulation of all data pertaining to a single Swing motion."""

    def __init__(
        self,
        start_sample: ImuSample,
        interval_stationary: SwingInterval,
        interval_backstroke: SwingInterval,
        interval_forwardstroke: SwingInterval,
        interval_impact: SwingInterval,
        interval_follow_through: SwingInterval,
        end_sample: ImuSample,
    ):
        self.start_sample = start_sample
        self.interval_stationary = interval_stationary
        self.interval_backstroke = interval_backstroke
        self.interval_forwardstroke = interval_forwardstroke
        self.interval_impact = interval_impact
        self.interval_follow_through = interval_follow_through
        self.end_sample = end_sample
