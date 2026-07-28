---
paths:
  - "**/*.py"
  - "**/*.{c,h,cpp,ino}"
---

# SPDX License Headers

Every source code file (`.py`, and any future firmware sources: `.c`, `.h`, `.cpp`, `.ino`, CircuitPython `.py`) must begin with the SPDX header, before any docstring or code:

```python
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Chase Bleyl
```

- Use the year the file was first created; extend to a range (e.g. `2026-2027`) only when the file is modified in a later year.
- Adapt the comment syntax to the language (`//` for C/C++).
- Applies to new files you create and to existing files missing the header.
- Does not apply to: Markdown docs, JSON/TOML/YAML config, generated files, test fixtures/data.
