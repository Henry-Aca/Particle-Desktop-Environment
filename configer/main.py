#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

import gi

# Pin Gtk3 early to avoid accidental Gtk4/Gdk4 preloading.
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")

from config_center import ConfigCenter  # noqa: E402
from i18n import load_strings  # noqa: E402


def main(argv: list[str]) -> int:
    base_dir = Path(__file__).resolve().parent
    i18n = load_strings(base_dir)
    app = ConfigCenter(i18n)
    return int(app.run(argv))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
