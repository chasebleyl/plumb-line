"""Pure analysis functions over core models.

Euler angles (yaw/pitch/roll) are derived here at analysis time — never
stored on models. Handedness is applied here as well: capture is pure
physics; golf vocabulary (open/closed, push/pull) flips sign for
left-handed strokes.
"""

import math

from plumbline.domain.models import ImuSample


def yaw_deg(sample: ImuSample) -> float:
    """Rotation about the vertical (Z) axis, in degrees.

    Positive is counterclockwise viewed from above (right-hand rule).
    """
    x, y, z, w = sample.q_x, sample.q_y, sample.q_z, sample.q_w
    return math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def face_angle_deg(address: ImuSample, sample: ImuSample, right_handed: bool = True) -> float:
    """Face angle relative to address, in degrees. Positive = open."""
    delta = yaw_deg(sample) - yaw_deg(address)
    return -delta if right_handed else delta
