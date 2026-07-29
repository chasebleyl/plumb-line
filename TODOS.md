# TODOs

Prioritized backlog.

## CRITICAL

## HIGH

- **Raise BNO085 fresh-data rate toward ~100 Hz** — measured only ~7–8 Hz
  of fresh sensor data (2026-07-28 capture; see docs/setup.md). A ~1 s putting
  stroke at 7–8 Hz yields <10 usable points, which long-term caps the
  accuracy of tempo/face-angle/path analysis. Request shorter report
  intervals via `enable_feature`; if I2C + driver overhead still caps the
  rate, evaluate the BNO085's UART-RVC mode.

## MEDIUM

- **Implement session-anchor timestamping in the capture path** — decided
  2026-07-28: pair laptop `time.time_ns()` with the first sample's `t_ns`,
  stored as per-file session metadata, per the models.py contract
  ("wall-clock is session-level metadata recorded once per capture
  file"). Phase 2 (untethered) will instead stamp wall-clock in firmware
  from the Adalogger's PCF8523 RTC. Include hardening: treat `t_ns`
  going backwards (board reset mid-capture) as end-of-stream.

- **Print only fresh reports in `firmware/code.py`** — ~50% of streamed
  lines are stale duplicates and the cadence is bimodal (<10 ms bursts /
  ~110–210 ms stalls) instead of steady. Skip printing when the report
  hasn't updated; this also gives timestamps that reflect true report
  cadence. Interim workaround exists (laptop-side duplicate filtering),
  and this will likely be absorbed into the sample-rate work above.

## LOW
