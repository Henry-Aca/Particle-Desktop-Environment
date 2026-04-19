#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class I18n:
    strings: Dict[str, str]

    def t(self, key: str, **kwargs: Any) -> str:
        template = self.strings.get(key, key)
        try:
            return template.format(**kwargs)
        except Exception:
            return template


def _detect_locale() -> str:
    # Very small locale detection; prefer zh_CN for any zh.*
    lang = (os.environ.get("LC_ALL") or os.environ.get("LANG") or "").lower()
    if lang.startswith("zh"):
        return "zh_CN"
    return "zh_CN"


def load_strings(base_dir: Path) -> I18n:
    locale = _detect_locale()
    path = base_dir / "strings" / f"{locale}.json"
    if not path.exists():
        path = base_dir / "strings" / "zh_CN.json"

    data: Dict[str, str] = {}
    try:
        raw = path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            data = {str(k): str(v) for k, v in parsed.items()}
    except Exception:
        data = {}

    return I18n(strings=data)
