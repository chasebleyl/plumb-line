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
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SessionAnchor:
    """Session-level wall-clock metadata (contract item 4), one per capture file.

    Pairs the laptop wall clock with the board's monotonic clock at the
    moment the first sample of a session arrives, so any sample's wall-clock
    time can be recovered as wall_time_ns + (timestamp_ns - anchor_timestamp_ns).
    """

    wall_time_ns: int  # laptop time.time_ns() at first-sample receipt
    anchor_timestamp_ns: int  # that first sample's board-monotonic timestamp_ns


@dataclass(frozen=True)
class ImuSample:
    """One normalized IMU reading. Sensor-agnostic.

    Contract (module docstring):
    - SI units: rad/s, m/s², nanosecond timestamps
    - Quaternion stored (x, y, z, w), Hamilton convention
    - Body frame: X toward target, Y left, Z up (right-handed)
    - Acceleration is gravity-removed (linear acceleration)
    """

    timestamp_ns: int
    q_x: float
    q_y: float
    q_z: float
    q_w: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    accel_x: float
    accel_y: float
    accel_z: float


@dataclass
class SwingInterval:
    """Starting & ending data over a time segment."""

    start_sample: ImuSample
    end_sample: ImuSample
    elapsed_time_ms: float
    intermediary_samples: list[ImuSample] = field(default_factory=list)


@dataclass
class Swing:
    """Encapsulation of all data pertaining to a single Swing motion."""

    start_sample: ImuSample
    interval_stationary: SwingInterval
    interval_backstroke: SwingInterval
    interval_forwardstroke: SwingInterval
    interval_impact: SwingInterval
    interval_follow_through: SwingInterval
    end_sample: ImuSample
