#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


PARTICLEDE_LANGUAGE_CONF = Path.home() / ".config" / "particlede" / "language.conf"


@dataclass(frozen=True)
class I18n:
    strings: Dict[str, str]

    def t(self, key: str, **kwargs: Any) -> str:
        template = self.strings.get(key, key)
        try:
            return template.format(**kwargs)
        except Exception:
            return template


def _read_active_language(conf_path: Path) -> str:
    try:
        if not conf_path.exists():
            return ""
        for raw in conf_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("ACTIVE_LANGUAGE="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                return val
    except Exception:
        return ""
    return ""


def _detect_locale(strings_dir: Path) -> str:
    """Pick a locale code that has a corresponding JSON in strings_dir."""

    active = _read_active_language(PARTICLEDE_LANGUAGE_CONF)
    if active and (strings_dir / f"{active}.json").exists():
        return active

    env = (os.environ.get("LC_ALL") or os.environ.get("LANG") or "").strip()
    if env:
        # Example: en_US.UTF-8 -> en_US
        code = env.split(".", 1)[0]
        if (strings_dir / f"{code}.json").exists():
            return code
        if code.lower().startswith("zh") and (strings_dir / "zh_CN.json").exists():
            return "zh_CN"

    return "zh_CN"


def load_strings(base_dir: Path) -> I18n:
    strings_dir = base_dir / "strings"
    locale = _detect_locale(strings_dir)
    path = strings_dir / f"{locale}.json"
    if not path.exists():
        path = strings_dir / "zh_CN.json"

    data: Dict[str, str] = {}
    try:
        raw = path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            data = {str(k): str(v) for k, v in parsed.items()}
    except Exception:
        data = {}

    return I18n(strings=data)
