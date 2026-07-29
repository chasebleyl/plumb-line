# TODOs

Prioritized backlog.

## CRITICAL

## HIGH

## MEDIUM

- **Implement session-anchor timestamping in the capture path** — decided
  2026-07-28: pair laptop `time.time_ns()` with the first sample's `t_ns`,
  stored as per-file session metadata, per the models.py contract
  ("wall-clock is session-level metadata recorded once per capture
  file"). Phase 2 (untethered) will instead stamp wall-clock in firmware
  from the Adalogger's PCF8523 RTC. Include hardening: treat `t_ns`
  going backwards (board reset mid-capture) as end-of-stream.

## LOW
