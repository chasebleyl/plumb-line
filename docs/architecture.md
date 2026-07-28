# Architecture

Onion architecture: dependencies point inward only. The core is pure and
knows nothing about hardware; sensors and outputs plug in at the edge via
adapters. This is what makes the system portable across sensors — swapping
the BNO085 for another IMU means writing one new adapter, and no core code
changes.

```
┌─────────────────────────────────────────────────────┐
│ infrastructure/          adapters (hardware, files) │
│   sensors/bno085_serial   sinks/csv_sink            │
│  ┌───────────────────────────────────────────────┐  │
│  │ application/          use cases + ports       │  │
│  │   ports (SampleSource, SampleSink)            │  │
│  │   capture (run_capture)                       │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │ domain/            pure core            │  │  │
│  │  │   models (ImuSample, Swing, ...)        │  │  │
│  │  │   analysis (face_angle, tempo, ...)     │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Layers

**domain** — core models (`ImuSample`, `SwingInterval`, `Swing`) and pure
analysis functions. Stdlib only. Imports nothing from outer layers.
The normalization contract these models obey is documented in the
`plumbline/domain/models.py` module docstring.

**application** — use cases, plus the ports (as `typing.Protocol`) that
outer adapters must satisfy. `SampleSource` is anything that yields
normalized samples (a live sensor, a replay of a recorded CSV);
`SampleSink` is anything that consumes them (CSV file, live plot).
Imports domain only.

**infrastructure** — adapters. The only layer that touches pyserial, file
formats, or sensor-specific details. Each sensor adapter owns its unit
conversion, axis remap, and timestamping so that everything inward is
sensor-agnostic.

## Import rules

| Layer | May import |
|---|---|
| domain | stdlib only |
| application | domain |
| infrastructure | application, domain, third-party libs |

## Firmware is outside the onion

CircuitPython on the Feather lacks `dataclasses`, `typing`, and most of the
stdlib, so the core package cannot run there. The firmware
([firmware/](../firmware/README.md)) is a dumb peripheral: read the BNO085,
print one raw line per reading over USB serial. Normalization happens
laptop-side in the BNO085 adapter. If a later phase moves analysis
on-device, the domain layer's stdlib-only rule keeps a port feasible.

## Typical wiring (phase 1, tethered capture)

```python
source = Bno085SerialSource(port="/dev/tty.usbmodem...")
sink = CsvSink(open("session.csv", "w", newline=""))
run_capture(source, sink)
```
