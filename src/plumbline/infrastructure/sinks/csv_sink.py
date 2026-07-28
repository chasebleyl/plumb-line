# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl

"""CSV sink: writes ImuSamples to a CSV file for pandas analysis."""

import csv
from dataclasses import asdict, fields
from typing import IO

from plumbline.domain.models import ImuSample


class CsvSink:
    """SampleSink writing one row per sample."""

    def __init__(self, file: IO[str]) -> None:
        self._file = file
        self._writer = csv.DictWriter(file, fieldnames=[f.name for f in fields(ImuSample)])
        self._writer.writeheader()

    def write(self, sample: ImuSample) -> None:
        self._writer.writerow(asdict(sample))

    def close(self) -> None:
        self._file.close()
