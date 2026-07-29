# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""CSV sink: writes ImuSamples to a CSV file for pandas analysis.

The session anchor is stored as a single ``#``-prefixed comment line above
the CSV header; read the file with ``pandas.read_csv(path, comment="#")``.
"""

import csv
from typing import IO

from plumbline.domain.models import ImuSample, SessionAnchor


class CsvSink:
    """SampleSink writing one row per sample."""

    def __init__(self, file: IO[str]) -> None:
        self._file = file
        self._writer = csv.DictWriter(file, fieldnames=list(ImuSample.FIELDS))
        self._header_written = False

    def write_anchor(self, anchor: SessionAnchor) -> None:
        self._file.write(
            f"# session_anchor wall_time_ns={anchor.wall_time_ns}"
            f" anchor_timestamp_ns={anchor.anchor_timestamp_ns}\n"
        )

    def write(self, sample: ImuSample) -> None:
        if not self._header_written:
            self._writer.writeheader()
            self._header_written = True
        self._writer.writerow({name: getattr(sample, name) for name in ImuSample.FIELDS})

    def close(self) -> None:
        if not self._header_written:
            self._writer.writeheader()
        self._file.close()
