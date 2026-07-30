# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""CSV replay source: replays a capture file written by CsvSink.

Lets detection work run offline against recorded sessions, no hardware
attached. Reads the CsvSink layout: an optional ``#``-prefixed session
anchor comment, a header row naming ImuSample.FIELDS, then one row per
sample. Rows are trusted — the file is our own sink's output — so a
malformed row raises rather than being skipped.
"""

import csv
from collections.abc import Iterator

from plumbline.domain.models import ImuSample


class CsvReplaySource:
    """SampleSource yielding the samples recorded in a CsvSink CSV file."""

    def __init__(self, path: str) -> None:
        self.path = path

    def samples(self) -> Iterator[ImuSample]:
        with open(self.path, newline="") as file:
            rows = csv.DictReader(line for line in file if not line.startswith("#"))
            for row in rows:
                yield ImuSample(
                    int(row["timestamp_ns"]),
                    *(float(row[name]) for name in ImuSample.FIELDS[1:]),
                )
