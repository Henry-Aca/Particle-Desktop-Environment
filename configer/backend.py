#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


OPENBOX_RC = Path.home() / ".config" / "openbox" / "rc.xml"
OPENBOX_MENU = Path.home() / ".config" / "openbox" / "menu.xml"
OPENBOX_AUTOSTART = Path.home() / ".config" / "openbox" / "autostart"
TINT2_RC = Path.home() / ".config" / "tint2" / "tint2rc"
ROFI_RC = Path.home() / ".config" / "rofi" / "config.rasi"
ROFI_POWERMENU_SH = Path.home() / ".config" / "rofi" / "powermenu.sh"
ROFI_POWERMENU_RASI = Path.home() / ".config" / "rofi" / "powermenu.rasi"
ROFI_COLORS_DIR = Path.home() / ".config" / "rofi" / "colors"
ROFI_SHARED_DIR = Path.home() / ".config" / "rofi" / "shared"
CONKY_RC = Path.home() / ".config" / "conky" / "conky.conf"

PCMANFM_CONF = Path.home() / ".config" / "pcmanfm" / "default" / "pcmanfm.conf"
PCMANFM_DESKTOP_ITEMS = Path.home() / ".config" / "pcmanfm" / "desktop-items-0.conf"

PARTICLEDE_GTKRC_2 = Path.home() / ".config" / "particlede" / "gtkrc-2.0"
PARTICLEDE_GTK3_DIR = Path.home() / ".config" / "particlede" / "gtk-3.0"
PARTICLEDE_LANGUAGE_CONF = Path.home() / ".config" / "particlede" / "language.conf"

QT5CT_CONF = Path.home() / ".config" / "qt5ct" / "qt5ct.conf"


def run_capture(args: List[str]) -> Tuple[int, str, str]:
    """Run a command and capture stdout/stderr."""
    try:
        completed = subprocess.run(
            args,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except FileNotFoundError:
        return 127, "", f"cmd_not_found:{args[0]}"
    except Exception as exc:
        return 1, "", f"exception:{exc}"

THEMES_DIR = Path.home() / ".themes"
PARTICLEDE_SESSION_ENV = Path.home() / ".config" / "particlede" / "session.env"

AUTOSTART_BEGIN = "### ParticleDE CONFIG CENTER BEGIN"
AUTOSTART_END = "### ParticleDE CONFIG CENTER END"

WALLPAPER_MODE = "stretch"


@dataclass
class RunningStatus:
    name: str
    process_names: List[str]


def run_shell(command: str) -> Tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return completed.returncode, completed.stdout
    except Exception as exc:
        return 1, str(exc)


def spawn(command: List[str]) -> Optional[str]:
    try:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return None
    except FileNotFoundError:
        return f"cmd_not_found:{command[0]}"
    except Exception as exc:
        return f"exception:{exc}"


def pgrep_any(names: List[str]) -> bool:
    for n in names:
        code, _ = run_shell(f"pgrep -x {shlex.quote(n)} >/dev/null 2>&1")
        if code == 0:
            return True
    return False


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")


# -------------------- tint2 --------------------

def update_kv_config(path: Path, updates: Dict[str, str]) -> None:
    """Update tint2-style key=value config while preserving other lines."""
    if not path.exists():
        raise FileNotFoundError(str(path))

    lines = read_text(path).splitlines(keepends=True)
    key_re = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$")

    seen = set()
    out: List[str] = []
    for line in lines:
        m = key_re.match(line.rstrip("\n"))
        if not m:
            out.append(line)
            continue

        key = m.group(1)
        if key in updates:
            out.append(f"{key} = {updates[key]}\n")
            seen.add(key)
        else:
            out.append(line)

    missing = [k for k in updates.keys() if k not in seen]
    if missing:
        out.append("\n# Added by ParticleDE Config Center\n")
        for k in missing:
            out.append(f"{k} = {updates[k]}\n")

    write_text(path, "".join(out))


def read_kv_config(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    key_re = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$")
    out: Dict[str, str] = {}
    for line in read_text(path).splitlines():
        m = key_re.match(line)
        if not m:
            continue
        out[m.group(1)] = m.group(2)
    return out


def parse_tint2_panel_height(panel_size_value: str) -> Optional[int]:
    if not panel_size_value:
        return None
    parts = panel_size_value.strip().split()
    if len(parts) < 2:
        return None
    try:
        return int(float(parts[1]))
    except Exception:
        return None


def parse_tint2_panel_position(panel_position_value: str) -> Optional[str]:
    if not panel_position_value:
        return None
    first = panel_position_value.strip().split()[0].lower()
    if first in ("top", "bottom"):
        return first
    return None


# -------------------- Openbox autostart (wallpaper/conky) --------------------

def upsert_openbox_autostart_block(
    autostart_path: Path,
    *,
    wallpaper_path: Optional[str],
    wallpaper_enabled: bool,
    conky_enabled: bool,
) -> None:
    ensure_parent(autostart_path)

    existing = read_text(autostart_path) if autostart_path.exists() else ""
    if existing.strip() == "":
        existing = "#!/bin/sh\n\n"
    elif not existing.startswith("#!"):
        existing = "#!/bin/sh\n\n" + existing

    block_lines: List[str] = [AUTOSTART_BEGIN, "# Managed by ParticleDE Config Center"]

    if wallpaper_enabled and wallpaper_path:
        quoted = shlex.quote(wallpaper_path)
        block_lines.append(f"pcmanfm -w {quoted} --wallpaper-mode={WALLPAPER_MODE} &")

    if conky_enabled:
        block_lines.append("conky &")

    block_lines.append(AUTOSTART_END)
    block = "\n".join(block_lines) + "\n"

    pattern = re.compile(
        rf"{re.escape(AUTOSTART_BEGIN)}[\s\S]*?{re.escape(AUTOSTART_END)}\n?",
        re.MULTILINE,
    )

    if pattern.search(existing):
        updated = pattern.sub(block, existing)
    else:
        updated = existing
        if not updated.endswith("\n"):
            updated += "\n"
        updated += "\n" + block

    write_text(autostart_path, updated)
    try:
        os.chmod(autostart_path, 0o755)
    except Exception:
        pass


def parse_managed_autostart_settings(autostart_path: Path) -> Dict[str, Optional[str]]:
    if not autostart_path.exists():
        return {"wallpaper_path": None, "wallpaper_enabled": None, "conky_enabled": None}

    text = read_text(autostart_path)
    m = re.search(
        rf"{re.escape(AUTOSTART_BEGIN)}([\s\S]*?){re.escape(AUTOSTART_END)}",
        text,
        flags=re.MULTILINE,
    )
    if not m:
        return {"wallpaper_path": None, "wallpaper_enabled": None, "conky_enabled": None}

    block = m.group(1)
    wallpaper_path: Optional[str] = None
    wallpaper_enabled: Optional[str] = "0"
    conky_enabled: Optional[str] = "0"

    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if re.match(r"^conky\b", line):
            conky_enabled = "1"
            continue

        if line.startswith("pcmanfm"):
            try:
                parts = shlex.split(line)
            except Exception:
                parts = line.split()

            for i, p in enumerate(parts):
                if p.startswith("--set-wallpaper="):
                    wallpaper_path = p.split("=", 1)[1]
                    wallpaper_enabled = "1"
                    break
                if p in ("-w", "--set-wallpaper") and i + 1 < len(parts):
                    wallpaper_path = parts[i + 1]
                    wallpaper_enabled = "1"
                    break
            continue

        if line.startswith("feh"):
            try:
                parts = shlex.split(line)
            except Exception:
                parts = line.split()
            if "--bg-scale" in parts:
                idx = parts.index("--bg-scale")
                if idx + 1 < len(parts):
                    wallpaper_path = parts[idx + 1]
                    wallpaper_enabled = "1"

    return {
        "wallpaper_path": wallpaper_path,
        "wallpaper_enabled": wallpaper_enabled,
        "conky_enabled": conky_enabled,
    }


def apply_wallpaper_now(wallpaper_path: str) -> Tuple[bool, str, Dict[str, Any]]:
    if not wallpaper_path:
        return False, "err.wallpaper.no_file", {}
    p = Path(wallpaper_path)
    if not p.exists():
        return False, "err.wallpaper.missing", {"path": wallpaper_path}

    err = spawn(["pcmanfm", f"--set-wallpaper={wallpaper_path}", f"--wallpaper-mode={WALLPAPER_MODE}"])
    if not err:
        return True, "msg.wallpaper.applied_pcmanfm", {}

    err2 = spawn(["feh", "--bg-scale", wallpaper_path])
    if not err2:
        return True, "msg.wallpaper.applied_feh", {}

    return False, "err.wallpaper.failed", {"detail": f"{err}; {err2}"}


# -------------------- Theme (GTK/Openbox) --------------------

def list_installed_themes(themes_dir: Path) -> List[str]:
    if not themes_dir.exists():
        return []
    names: List[str] = []
    for p in themes_dir.iterdir():
        if not p.is_dir():
            continue
        if p.name.startswith("."):
            continue
        names.append(p.name)
    return sorted(names, key=lambda s: s.lower())


def theme_has_openbox(themes_dir: Path, theme_name: str) -> bool:
    return (themes_dir / theme_name / "openbox-3").is_dir()


def _theme_tint2_source_file(themes_dir: Path, theme_name: str) -> Optional[Path]:
    p = themes_dir / theme_name / "tint2rc"
    return p if p.exists() and p.is_file() else None


def _theme_rofi_source_dir(themes_dir: Path, theme_name: str) -> Optional[Path]:
    p = themes_dir / theme_name / "rofi"
    return p if p.exists() and p.is_dir() else None


def apply_theme_tint2(themes_dir: Path, theme_name: str, dest_tint2rc: Path = TINT2_RC) -> None:
    """Apply theme-provided tint2rc if present.

    This overwrites the destination tint2rc. Callers may re-apply panel geometry
    (panel_size/panel_position) afterwards.
    """

    src = _theme_tint2_source_file(themes_dir, theme_name)
    if not src:
        return
    ensure_parent(dest_tint2rc)
    shutil.copy2(str(src), str(dest_tint2rc))


def apply_theme_rofi(themes_dir: Path, theme_name: str, dest_rofi_dir: Path = ROFI_RC.parent) -> None:
    """Apply theme-provided rofi configuration directory if present.

    Copies files under <theme>/rofi/ into ~/.config/rofi/ (overwriting existing).
    """

    src_dir = _theme_rofi_source_dir(themes_dir, theme_name)
    if not src_dir:
        return
    dest_rofi_dir.mkdir(parents=True, exist_ok=True)
    for item in src_dir.iterdir():
        target = dest_rofi_dir / item.name
        if item.is_dir():
            shutil.copytree(str(item), str(target), dirs_exist_ok=True)
        else:
            shutil.copy2(str(item), str(target))


def read_simple_env(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    out: Dict[str, str] = {}
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
            v = v[1:-1]
        if k:
            out[k] = v
    return out


def write_particlede_session_env(*, gtk_theme: str, icon_theme: str = "Papirus-Dark") -> None:
    ensure_parent(PARTICLEDE_SESSION_ENV)
    content = (
        "# Generated by ParticleDE Config Center\n"
        "# Sourced by particlede-session on login\n"
        f"GTK_THEME={shlex.quote(gtk_theme)}\n"
        f"GTK_ICON_THEME={shlex.quote(icon_theme)}\n"
    )
    write_text(PARTICLEDE_SESSION_ENV, content)


def set_openbox_theme_name(rc_xml_path: Path, theme_name: str) -> None:
    if not rc_xml_path.exists():
        raise FileNotFoundError(str(rc_xml_path))

    import xml.etree.ElementTree as ET

    ET.register_namespace("", "http://openbox.org/3.4/rc")
    ET.register_namespace("xi", "http://www.w3.org/2001/XInclude")

    tree = ET.parse(rc_xml_path)
    root = tree.getroot()
    ns = "{http://openbox.org/3.4/rc}"

    theme = root.find(f"{ns}theme")
    if theme is None:
        theme = ET.SubElement(root, f"{ns}theme")
    name = theme.find(f"{ns}name")
    if name is None:
        name = ET.SubElement(theme, f"{ns}name")
    name.text = theme_name
    tree.write(rc_xml_path, encoding="UTF-8", xml_declaration=True)


def set_openbox_keybind_execute(rc_xml_path: Path, key: str, command: str) -> None:
    if not rc_xml_path.exists():
        raise FileNotFoundError(str(rc_xml_path))

    import xml.etree.ElementTree as ET

    ET.register_namespace("", "http://openbox.org/3.4/rc")
    ET.register_namespace("xi", "http://www.w3.org/2001/XInclude")

    tree = ET.parse(rc_xml_path)
    root = tree.getroot()
    ns = "{http://openbox.org/3.4/rc}"

    keyboard = root.find(f"{ns}keyboard")
    if keyboard is None:
        keyboard = ET.SubElement(root, f"{ns}keyboard")

    def keybind_matches(elem: ET.Element) -> bool:
        return elem.tag == f"{ns}keybind" and elem.get("key") == key

    keybind = None
    for child in keyboard:
        if keybind_matches(child):
            keybind = child
            break

    if keybind is None:
        keybind = ET.SubElement(keyboard, f"{ns}keybind", {"key": key})

    for a in list(keybind):
        keybind.remove(a)

    action = ET.SubElement(keybind, f"{ns}action", {"name": "Execute"})
    cmd = ET.SubElement(action, f"{ns}command")
    cmd.text = command

    tree.write(rc_xml_path, encoding="UTF-8", xml_declaration=True)


# -------------------- Runtime control --------------------

def restart_component(kind: str) -> Tuple[bool, str, Dict[str, Any]]:
    if kind == "tint2_restart":
        run_shell("pkill -x tint2 >/dev/null 2>&1 || true")
        err = spawn(["tint2"])
        if err:
            return _spawn_err(err)
        return True, "msg.tint2.restarted", {}

    if kind == "tint2_stop":
        run_shell("pkill -x tint2 >/dev/null 2>&1 || true")
        return True, "msg.tint2.stopped", {}

    if kind == "tint2_start":
        err = spawn(["tint2"])
        if err:
            return _spawn_err(err)
        return True, "msg.tint2.started", {}

    if kind == "pcmanfm_start":
        err = spawn(["pcmanfm", "--desktop"])
        if err:
            return _spawn_err(err)
        return True, "msg.pcmanfm.started", {}

    if kind == "pcmanfm_stop":
        run_shell("pkill -x pcmanfm >/dev/null 2>&1 || true")
        return True, "msg.pcmanfm.stopped", {}

    if kind == "pcmanfm_settings":
        err = spawn(["pcmanfm", "--desktop-pref"])
        if err:
            return _spawn_err(err)
        return True, "msg.control.settings_opened", {"component": "pcmanfm"}

    if kind == "rofi_start":
        # rofi is typically invoked on-demand; start here means "open once".
        err = spawn(["rofi", "-show", "run"])
        if err:
            return _spawn_err(err)
        return True, "msg.rofi.opened", {}

    if kind == "rofi_stop":
        run_shell("pkill -x rofi >/dev/null 2>&1 || true")
        return True, "msg.rofi.stopped", {}

    if kind == "tint2_settings":
        err = spawn(["tint2conf"])
        if err:
            return _spawn_err(err)
        return True, "msg.control.settings_opened", {"component": "tint2"}

    if kind == "conky_start":
        err = spawn(["conky"])
        if err:
            return _spawn_err(err)
        return True, "msg.conky.started", {}

    if kind == "conky_stop":
        run_shell("pkill -x conky >/dev/null 2>&1 || true")
        return True, "msg.conky.stopped", {}

    if kind == "openbox_reconfigure":
        code, out = run_shell("openbox --reconfigure 2>&1 || true")
        if code == 0:
            return True, "msg.openbox.reconfigured", {}
        if out.strip():
            return True, "msg.openbox.reconfigure_ran", {"detail": out.strip()}
        return True, "msg.openbox.reconfigure_ran", {}

    if kind == "openbox_settings":
        err = spawn(["obconf"])
        if err:
            return _spawn_err(err)
        return True, "msg.control.settings_opened", {"component": "openbox"}

    return False, "err.action_unknown", {"action": kind}


# -------------------- External system settings --------------------

def launch_system_settings(kind: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Launch external GUI tools for system settings.

    Returns (ok, msg_key, kwargs).
    """

    commands: Dict[str, List[str]] = {
        "center": ["gnome-control-center"],
    }

    cmd = commands.get(kind)
    if not cmd:
        return False, "err.action_unknown", {"action": kind}

    err = spawn(cmd)
    if err:
        return _spawn_err(err)

    return True, "msg.system.launched", {"target": kind}


def _spawn_err(err: str) -> Tuple[bool, str, Dict[str, Any]]:
    if err.startswith("cmd_not_found:"):
        return False, "err.cmd_not_found", {"cmd": err.split(":", 1)[1]}
    if err.startswith("exception:"):
        return False, "err.runtime", {"err": err.split(":", 1)[1]}
    return False, "err.runtime", {"err": err}


def open_in_file_manager(path: Path) -> Tuple[bool, str, Dict[str, Any]]:
    """Open a file or directory in the user's file manager."""

    if path.exists() and path.is_dir():
        target = path
    else:
        # If it's a file (or even missing), open its containing directory.
        target = path.parent

    err = spawn(["xdg-open", str(target)])
    if not err:
        return True, "msg.files.open_dir_ok", {"path": str(target)}

    # Fallback for some minimal systems
    err2 = spawn(["gio", "open", str(target)])
    if not err2:
        return True, "msg.files.open_dir_ok", {"path": str(target)}

    if err.startswith("cmd_not_found:") and err2.startswith("cmd_not_found:"):
        return False, "err.cmd_not_found", {"cmd": "xdg-open"}

    return False, "err.files.open_dir_failed", {"err": f"{err}; {err2}"}


_LANG_LINE_RE = re.compile(r"^\s*([a-z]{2}_[A-Z]{2})\s+(.+?)\s*$")


def read_active_language(conf_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
    """Read ACTIVE_LANGUAGE from language.conf."""
    try:
        if not conf_path.exists():
            return True, "msg.language.current", {"lang": "zh_CN"}

        for raw in read_text(conf_path).splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("ACTIVE_LANGUAGE="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return True, "msg.language.current", {"lang": val}
        return True, "msg.language.current", {"lang": "zh_CN"}
    except Exception as exc:
        return False, "err.language.read_conf_failed", {"err": str(exc)}


def list_supported_languages(script_path: Path) -> Tuple[bool, str, Dict[str, Any]]:
    """Return languages as a compact 'code\tname\n...' string in kwargs['items']."""

    if not script_path.exists():
        return False, "err.language.script_missing", {"path": str(script_path)}

    code, out, err = run_capture([str(script_path), "list"])
    if code != 0:
        detail = (out + "\n" + err).strip()
        return False, "err.language.list_failed", {"detail": detail}

    items: List[str] = []
    for line in out.splitlines():
        m = _LANG_LINE_RE.match(line)
        if not m:
            continue
        items.append(f"{m.group(1)}\t{m.group(2)}")

    if not items:
        return False, "err.language.parse_failed", {"detail": out.strip()}

    return True, "msg.language.list_loaded", {"items": "\n".join(items)}


def switch_language(script_path: Path, lang: str) -> Tuple[bool, str, Dict[str, Any]]:
    if not script_path.exists():
        return False, "err.language.script_missing", {"path": str(script_path)}

    code, out, err = run_capture([str(script_path), lang])
    if code != 0:
        detail = (out + "\n" + err).strip()
        return False, "err.language.switch_failed", {"detail": detail}

    return True, "msg.language.switched", {"lang": lang}
