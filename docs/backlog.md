# Backlog

Project-management tracker for POC milestone work: what's done, what's
outstanding, and what's deliberately deferred. Bug/debt prioritization lives
separately in [TODOS.md](TODOS.md).

Legend: `[ ]` open · `[x]` done · `[?]` blocked on an open question below

## POC 1 — Tethered capture (current)

Goal: USB serial streaming to a laptop; pyserial → CSV, with
pandas/matplotlib analysis to prototype detection logic against recorded
data.

### Done

- [x] Firmware: BNO085 → one raw CSV line per fresh rotation vector at
      100 Hz over USB serial (raw SHTP loop, 400 kHz I2C)
- [x] Laptop pipeline: `Bno085SerialSource` → `run_capture` → `CsvSink`,
      normalized `ImuSample` CSVs with session anchor
- [x] Normalization contract documented and modeled (`domain/models.py`)
- [x] Measurement formulas researched and verified
      ([formulas.md](formulas.md)): tempo, face angle at impact, stroke path
- [x] Parser/capture/sink unit tests
- [x] End-to-end validation at 100 Hz (2026-07-28 wiggle test)
- [x] Portability refactor — `domain/` and `application/` comply with the
      portability rule (architecture.md): plain classes, no `dataclasses`
      or runtime `typing`/`Protocol` imports in the inner layers; same
      source runs under CPython and CircuitPython
- [x] CSV replay source — `CsvReplaySource` replays a recorded capture
      CSV as a `SampleSource`, so detection work runs offline without
      hardware

### Outstanding

Ordered by priority: items unblock the ones below them.

- [ ] **Temporary capture jig** — repeatable mount on the putter grip so
      captured data has a stable chip-to-body frame (decided 2026-07-29:
      jig now, final enclosure mounting deferred). Gates the reference
      dataset: captures without a stable frame can't be developed against
- [ ] **Reference dataset** — capture real putting strokes (labeled
      sessions: known handedness, deliberate open/closed/square strokes,
      varied tempo) to develop detection against. Needs the jig
- [ ] **Analysis notebook/scripts** — pandas/matplotlib exploration of
      recorded CSVs to prototype and sanity-check detection logic before
      it hardens into `domain/analysis.py`
- [ ] **Stroke segmentation** — detect a stroke in a sample stream and
      populate `Swing`/`SwingInterval` (address → backstroke → forward
      stroke → impact → follow-through). Phase-event definitions in
      formulas.md §1; impact detection likely accel-spike based
- [ ] **Tempo analysis** — backswing/downswing durations and ratio from
      segmented intervals (formulas.md §1)
- [ ] **Stroke path analysis** — path direction at impact (formulas.md §3)
- [ ] Face angle at impact — `face_angle_deg` exists; wire it to the
      detected impact sample rather than a hand-picked one
- [ ] Capture CLI entry point (port/outfile args) replacing the manual
      wiring snippet in architecture.md — convenience, any time
- [ ] Axis remap in the BNO085 adapter — deliberately last: stays
      identity until enclosure mounting is final; face-angle sign
      convention verified against the jig frame in the meantime

## POC 2 — On-device compute + display

Goal: crude rendering on the Feather's integrated TFT; prove computation
and display happen entirely on-device, no dev machine in the loop.

- [ ] Deploy `domain/` + `application/` to the device — same source, no
      port (the POC 1 portability refactor makes this a copy of files,
      not a re-implementation)
- [ ] **On-device BNO085 sensor adapter** — lift the firmware's raw SHTP
      loop into `infrastructure/sensors/` as an on-device `SampleSource`;
      `code.py` shrinks to the board-specific composition root. Axis
      remap expressed as data (permutation/sign table) shared with the
      laptop serial adapter, never two code paths
- [ ] On-device stroke segmentation + metrics (tempo, face angle, path)
      within CircuitPython performance limits at 100 Hz
- [ ] **Address/zero reference workflow on-device** (how the user marks
      address orientation before a stroke) — needed for face angle delta.
      Do this before TFT rendering: the device must recognize when it is
      "zeroed" so the ready-state visualization has a clear signal to
      fire on
- [ ] **Results-side display port** — define the port a display adapter
      consumes (per-stroke metrics + readiness states, not the raw sample
      stream; architecture.md "Component interchange"). The Feather TFT
      renderer below is its first adapter, in `infrastructure/displays/`
- [ ] TFT rendering: readiness states + per-stroke summary screen (tempo,
      face angle, path). Readiness states — "calibrating" while the
      zero reference is being established, "ready for swing" once zeroed —
      driven by the address/zero workflow above
- [ ] Display update strategy that doesn't stall sampling (TFT writes cost
      ~100 ms; render only between strokes / when stationary)
- [ ] Dual-output validation mode — keep USB streaming alive alongside
      on-device compute; cross-check device metrics against the laptop
      pipeline on the same strokes (decided 2026-07-29: POC 2 exit
      criterion)
- [ ] Button interaction if needed (Feather has D0/D1/D2) — e.g.
      re-zero, next screen

## POC 3 — Untethered capture

Goal: SD-card logging on a real practice green; shareable data dumps from
longer sessions.

- [ ] Solder stacking headers; stack Adalogger FeatherWing (SD + RTC)
- [ ] Firmware: log raw sample lines to SD instead of / alongside USB
      serial; verify 100 Hz write cadence holds with SD latency (buffered
      writes)
- [ ] RTC integration: wall-clock session anchor on-device (replaces the
      laptop-side anchor), session file naming
- [ ] Session lifecycle: start/stop/rotate files (button or
      motion-triggered), safe unmount/flush on power loss
- [ ] LiPo power: battery life measurement for a practice-session duration
- [ ] SD-card ingest path laptop-side: reuse the CSV replay source against
      dumped files
- [ ] Physical attachment good enough for a real green (butt-of-grip mount,
      cable-free)

## Scope decisions (2026-07-29)

- **Mounting/axis remap:** capture POC 1 data with a temporary jig +
  identity remap; final enclosure mounting and remap deferred.
- **POC 2 code reuse (amended 2026-07-29):** single shared
  implementation — `domain/` and `application/` must satisfy the
  portability rule (architecture.md) so POC 2 deploys the same source
  rather than porting or re-implementing. The POC 1 portability
  refactor closed that gap (2026-07-30).
- **Chip abstraction:** all chips targeted through MVP run
  CircuitPython — the runtime is the chip-portability layer; per-board
  differences live only in the `code.py` composition root
  (architecture.md "Component interchange").
- **POC metric scope:** tempo, face angle at impact, stroke path. Putter
  speed deferred to MVP (lever-arm/hosel caveats per formulas.md).
- **POC 2 validation:** dual-output cross-check — device metrics vs
  laptop pipeline on the same strokes.
- **Handedness:** POC assumes right-handed (`face_angle_deg` default);
  handedness configuration is an MVP concern.
- **Impact spot:** out of scope for both POC and MVP — not measurable
  with a grip-mounted IMU alone. Referenced in formulas.md only as
  context (fourth MacKenzie variable, ~3% of direction variance); no
  measurement section exists or is planned.

## Deferred to MVP

- Putter speed at impact (gyro + lever arm; accuracy caveats in
  formulas.md)
- Handedness configuration (POC hardcodes right-handed)

- Component selection for purpose-built housing (POC parts expected to be
  swapped, including the integrated-display Feather). Selection is
  constrained to CircuitPython-capable chips (chip-abstraction decision
  above); revisit the runtime choice only if performance or power forces
  it — that would reopen the single-implementation question
- Additional component adapters as selection demands (e.g. BNO055 sensor
  source, SSD1306 OLED display) — one new `infrastructure/` module each,
  no core changes (architecture.md "Component interchange")
- Housing/enclosure industrial design (2" cube target)
- Refined display metrics/visualizations for final hardware
- Algorithm fine-tuning (accuracy targets in formulas.md §2/§3)
- Calibration/compensation beyond basic zeroing (shaft lever-arm geometry,
  hosel offset per formulas.md caveats)
