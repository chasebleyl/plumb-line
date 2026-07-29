# Hardware Setup

Phase 1 (tethered capture): BNO085 readings streaming from the ESP32-S3
Reverse TFT Feather to a Windows machine over USB-C serial, landing in
normalized `ImuSample` CSVs.

## Components

| Product | Qty | Description | Role |
|---------|-----|-------------|------|
| [#5691](https://www.adafruit.com/product/5691) | 1 | Feather ESP32-S3 Reverse TFT | Compute + display (CircuitPython) |
| [#4754](https://www.adafruit.com/product/4754) | 1 | BNO085 9-DOF IMU Fusion Breakout | Stroke sensing |
| [#4399](https://www.adafruit.com/product/4399) | 2 | STEMMA QT cable, 50 mm | Feather ↔ BNO085 I2C, solderless |
| [#4210](https://www.adafruit.com/product/4210) | 2 | STEMMA QT cable, 100 mm | Longer-run alternative |
| [#2922](https://www.adafruit.com/product/2922) | 1 | Adalogger FeatherWing | Phase 2: SD logging + RTC |
| [#5249](https://www.adafruit.com/product/5249) | 1 | microSD card 64 MB | Phase 2: Adalogger storage |
| [#1578](https://www.adafruit.com/product/1578) | 1 | LiPo battery 3.7 V 500 mAh | Phase 2: untethered power |
| [#2830](https://www.adafruit.com/product/2830) | 1 | Feather Stacking Headers | Phase 2: stacking FeatherWings |
| [#2884](https://www.adafruit.com/product/2884) | 1 | FeatherWing Proto | Prototyping / mounting |

Phase 1 uses only the first three rows; everything else stays boxed.

## Setup

1. **Update the bootloader.** The factory TinyUF2 is too old for
   CircuitPython 10.x on 4 MB-flash boards (needs ≥ 0.33.0; firmware
   won't load and the board falls back to the bootloader screen).
   On the [circuitpython.org board page](https://circuitpython.org/board/adafruit_feather_esp32s3_reverse_tft/):
   "Open Installer" → "Install Bootloader Only".
2. **Flash CircuitPython.** Double-tap reset (`FTHRS3BOOT` drive
   appears), drag on the board's CircuitPython 10.x UF2 from the same
   page. Board reboots as `CIRCUITPY` (D: here). Running: 10.2.1.
3. **Install libraries.** From the matching 10.x
   [library bundle](https://circuitpython.org/libraries), copy
   `adafruit_bno08x/` and `adafruit_bus_device/` into `CIRCUITPY/lib/`.
4. **Connect the BNO085.** 50 mm STEMMA QT cable from the Feather's port
   to either sensor port (the two are parallel; pick whichever routes
   better). Green LED = power. I2C address 0x4A.
5. **Deploy firmware.** Copy [firmware/code.py](../firmware/code.py) to
   `CIRCUITPY/code.py`; it auto-runs and prints one CSV reading per line
   (`t_ns,qi,qj,qk,qw,gx,gy,gz,ax,ay,az` — quaternion, gyro rad/s,
   gravity-removed linear accel m/s²).
6. **Laptop side.** `python -m venv .venv`, then
   `pip install -e .[capture,dev]`. The board enumerates as a USB Serial
   Device (COM7 here, 115200 baud).

## Verify

- Quick look: open the COM port with any serial terminal
  (`python -m serial.tools.miniterm COM7 115200`) — 11-field CSV lines
  should scroll.
- Full pipeline: `Bno085SerialSource("COM7") → run_capture → CsvSink`
  yields `ImuSample` CSVs. Parser tests: `python -m pytest tests`.
- No firmware needed for a wiring check: from the REPL,
  `board.STEMMA_I2C()` scan should show `0x4a` (BNO085) alongside `0x36`
  (the Feather's onboard fuel gauge). Tip when scripting the REPL over
  pyserial: single-line statements only — multi-line blocks hang in
  `...` continuation mode.

## Current Status

**Full pipeline working** (validated 2026-07-28): all channels stream
over COM7 at ~10–11 Hz and land in normalized CSVs; quaternion norm
1.0, monotonic timestamps, gyro/accel respond to motion and settle at
rest.

## Open Items

- **Sample rate** — ~10–11 Hz print rate and only ~7–8 Hz fresh data vs
  ~100 Hz wanted for stroke capture; details and candidates in
  [TODOS.md](../TODOS.md).
- **Axis remap** — identity in the adapter until enclosure mounting is
  decided.
