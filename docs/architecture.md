# Architecture

Onion architecture: dependencies point inward only. The core is pure and
knows nothing about hardware; sensors and outputs plug in at the edge via
adapters.

The target (MVP and beyond) is a self-contained device: the sensor feeds
the chip, the chip runs the full onion — capture, analysis, display — and
no external computer is involved. The `plumbline` package *is* what gets
installed on the chip. The laptop never disappears entirely, but its role
shrinks to a development harness (see "Development topology" below).

```
┌─────────────────────────────────────────────────────────┐
│ infrastructure/            adapters (hardware, files)   │
│   sensors/  bno085_*  (bno055_*, ...)                   │
│   displays/ (feather_tft, ssd1306, ...)                 │
│   sinks/    csv_sink  (sd_sink, ...)                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │ application/            use cases + ports         │  │
│  │   ports (SampleSource, SampleSink, ...)           │  │
│  │   capture (run_capture)                           │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │ domain/              pure core              │  │  │
│  │  │   models (ImuSample, Swing, ...)            │  │  │
│  │  │   analysis (face_angle, tempo, ...)         │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Component interchange

The device has three hardware variation points — sensor, chip, display.
Each maps to the architecture differently, and supporting a new component
means implementing its integration inside `plumbline` without touching the
core:

| Component | How it's swapped | Example (POC → alternative) |
|---|---|---|
| Sensor | New `SampleSource` adapter in `infrastructure/sensors/` | Adafruit BNO085 breakout → Bosch BNO055 |
| Display | New display adapter in `infrastructure/displays/` | Feather's integrated TFT → SSD1306 128×64 I2C OLED |
| Chip | No adapter — CircuitPython is the chip abstraction | Feather ESP32-S3 Reverse TFT → Seeed XIAO ESP32-S3 |

**Sensor.** Each sensor adapter owns everything sensor-specific: unit
conversion to SI, axis remap from chip frame to body frame, and
timestamping. It emits `ImuSample` values obeying the normalization
contract (documented in the `plumbline/domain/models.py` module
docstring). Everything inward is sensor-agnostic. Sensors differ in real
ways — the BNO085 does sensor fusion and gravity removal on-chip, a
BNO055 has different report formats and calibration behavior — and all of
that difference is absorbed in the adapter.

**Display.** A display adapter renders analysis results — per-stroke
metrics and readiness states, not the raw sample stream — so it hangs off
a results-side port rather than `SampleSink`. That port's exact shape gets
defined when on-device rendering lands (POC 2); the commitment here is
architectural: rendering is an outer-layer adapter, and swapping the
Feather TFT for an SSD1306 means one new module in
`infrastructure/displays/`.

**Chip.** The chip is not an adapter — it's the runtime the whole onion
runs on. Chip portability comes from two decisions: (1) all supported
chips run CircuitPython, so the same source deploys unchanged; (2) the
board-specific bits (pin names, I2C bus setup, display initialization,
buttons) live only in the composition root — the top-level `code.py` that
instantiates adapters and wires them together. Supporting a new board
means a new wiring file, not new architecture.

## Layers

**domain** — core models (`ImuSample`, `SwingInterval`, `Swing`) and pure
analysis functions. Imports nothing from outer layers. Must run under
both CPython and CircuitPython (see "Portability rule").

**application** — use cases, plus the ports that outer adapters must
satisfy. `SampleSource` is anything that yields normalized samples (a
live sensor, a replay of a recorded CSV); `SampleSink` is anything that
consumes them (CSV file, SD card, live plot). Imports domain only.

**infrastructure** — adapters. The only layer that touches buses, file
formats, display libraries, or sensor-specific details. Adapters may be
platform-specific (a pyserial source only works on the laptop; an I2C
display driver only works on-device) — that's fine, because they're
leaves. Which adapters get wired is the composition root's decision.

## Import rules

| Layer | May import |
|---|---|
| domain | CircuitPython-safe stdlib subset only (e.g. `math`) |
| application | domain (same CircuitPython-safe constraint) |
| infrastructure | application, domain, third-party / platform libs |

## Portability rule

The inner layers (domain, application) must run unchanged under CPython
*and* CircuitPython. That means no `dataclasses`, no runtime `typing`, no
stdlib modules absent from CircuitPython — plain classes, plain functions,
`math`. CPython-only conveniences belong in infrastructure or the laptop
composition root.

This is the rule that keeps the codebase a single implementation instead
of a laptop version and a device port drifting apart.

> Status: `domain/models.py` currently uses `dataclasses` and
> `application/ports.py` uses `typing.Protocol`; bringing them into
> compliance is tracked in the backlog (pre-POC 2).

## Development topology (POC 1, tethered)

During tethered capture the onion runs on the laptop and the device acts
as a dumb peripheral: [firmware/code.py](../firmware/README.md) reads the
BNO085 and prints one raw line per reading over USB serial; the laptop's
`Bno085SerialSource` adapter normalizes it. This is a scaffold, not the
destination — from POC 2 onward the onion moves onto the chip, and the
firmware's sensor loop becomes the guts of the on-device BNO085 adapter.

The laptop pipeline outlives the scaffold as a permanent development
harness: CSV replay (`SampleSource` over recorded files) for developing
detection logic offline, and the reference implementation for
dual-output validation — cross-checking on-device metrics against the
laptop pipeline on the same strokes.

The axis remap deserves care across this transition: the chip→body-frame
remap currently lives in the laptop adapter, and on-device it must happen
in the device's sensor adapter. Keep the remap expressed as data (an axis
permutation/sign table) shared by both, never two hand-maintained code
paths.

## Typical wiring

Laptop, tethered capture (POC 1):

```python
source = Bno085SerialSource(port="/dev/tty.usbmodem...")
sink = CsvSink(open("session.csv", "w", newline=""))
run_capture(source, sink)
```

On-device (target shape — adapters land in POC 2/3):

```python
# code.py — composition root; the only board-specific file
i2c = busio.I2C(board.SCL, board.SDA, frequency=400_000)
source = Bno085I2cSource(i2c)          # infrastructure/sensors/
display = FeatherTftDisplay(board.DISPLAY)  # infrastructure/displays/
run_session(source, display)           # application use case (POC 2)
```
