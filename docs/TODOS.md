# TODOs

Prioritized backlog.

## CRITICAL

## HIGH

- **Firmware: recover from wedged BNO085 instead of looping silently.**
  Observed live 2026-07-29 during a wiggle test: an I2C glitch (loose
  STEMMA QT connection, `[Errno 5]` reads) left the sensor wedged but
  still ACKing; the raw read loop in `firmware/code.py` then spun forever
  on short/garbage headers with no output, and only a serial Ctrl+C +
  Ctrl+D reload (driver re-init soft-resets the sensor) recovered it.
  After N consecutive errors or empty reads, re-initialize the sensor
  (or hard-reset via the BNO085 soft-reset command) and report the event
  on the stream. The captured failure is snapshotted at
  `tests/fixtures/wiggle_i2c_dropout_raw.txt`.

## MEDIUM

## LOW
