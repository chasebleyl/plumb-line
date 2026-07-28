# Plumb Line

A DIY putter-mounted stroke sensor: a device that mounts on the butt end of a
putter grip and measures face angle, tempo, and stroke path. Target form
factor is a 2" cube, 3D-printed enclosure with a display on one face.

The device is deliberately a **capture-log-and-analyze** tool, *not* a
biofeedback system — that distinction keeps it clear of Blast Motion's
US 12,370,427 patent, which requires a real-time feedback signal generator
this project intentionally does not build. It is framed as a practice/training
aid (avoiding USGA tournament-use concerns).

## Hardware

- Sensor: Adafruit BNO085 9-DOF Orientation IMU Fusion Breakout (#4754)
- Compute + display: Adafruit ESP32-S3 Reverse TFT Feather (#5691), CircuitPython
- Adalogger FeatherWing for SD logging + RTC
- 500 mAh LiPo, STEMMA QT cables (solderless), stacking headers, proto board

## Repo layout

```
src/plumbline/        Laptop-side package (onion architecture; see docs/architecture.md)
  domain/             Pure core: models + analysis. The normalization contract
                      lives in the models.py module docstring. Stdlib only.
  application/        Use cases + ports (SampleSource, SampleSink)
  infrastructure/     Adapters: BNO085 serial source, CSV sink
firmware/             CircuitPython for the Feather — dumb peripheral, prints
                      one raw reading per line over USB serial
docs/                 Design + research notes
```

## Docs

- [architecture.md](docs/architecture.md) — onion layers, import rules, wiring
- [formulas.md](docs/formulas.md) — measurement formulas for tempo, face angle
  at impact, and stroke path, with citations; each section independently
  verified against primary sources
- [metrics.md](docs/metrics.md) — survey of the putting-metric space (six
  categories) with research quotes
- [direction.md](docs/direction.md), [speed.md](docs/speed.md) — candidate
  metric lists per outcome dimension

## Development approach

Phased:

1. **Tethered capture (current)** — USB-C serial streaming to a laptop;
   pyserial → CSV, with pandas/matplotlib analysis to prototype detection
   logic against recorded data. Blocked in part on finalizing enclosure
   mounting (the BNO085 adapter's axis remap depends on it).
2. **Untethered** — SD-card logging on a real practice green.

## Research grounding

Built on non-vendor academic sources, primarily Sasho MacKenzie's published
work: the four deterministic impact variables (face angle, stroke path, putter
speed, impact spot), the ~83/17 face-angle/path split for start direction, and
measurement-accuracy caveats (shaft lever-arm geometry, hosel offset,
zero-torque putter designs). Tempo grounding comes from Marquardt's SAM
PuttLab PGA Tour data and Grober's resonance model, which independently
converge on a ~2:1 backswing:downswing ratio. See
[docs/formulas.md](docs/formulas.md) for the full, verified reference.

## Commercialization vision

Hobby-scale, explicitly not a serious venture — modeled on comma.ai's
openpilot: the algorithm is open source, with pre-assembled plug-and-play
hardware units sold just-in-time for people who don't want to source, print,
and assemble their own. The moat is convenience and support, not IP. The repo
is public from the start as defensive publication.

## Name

"Plumb line": the thematic tie between green-reading (the plumb-bob method)
and gravity-referenced IMU sensing.

## License

Plumb Line is released under the [GNU General Public License v3.0 only](COPYING)
(GPL-3.0-only).

Copyright (C) 2026 Chase Bleyl

Hardware assembly and manufacturing documentation is not part of this
repository and is not covered by this license.
