#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, Gtk, Gdk  # noqa: E402


APP_ID = "org.particlede.ConfigCenter"


OPENBOX_RC = Path.home() / ".config" / "openbox" / "rc.xml"
OPENBOX_AUTOSTART = Path.home() / ".config" / "openbox" / "autostart"
TINT2_RC = Path.home() / ".config" / "tint2" / "tint2rc"
ROFI_RC = Path.home() / ".config" / "rofi" / "config.rasi"
CONKY_RC = Path.home() / ".config" / "conky" / "conky.conf"


AUTOSTART_BEGIN = "### ParticleDE CONFIG CENTER BEGIN"
AUTOSTART_END = "### ParticleDE CONFIG CENTER END"


@dataclass
class RunningStatus:
    name: str
    process_names: List[str]


def _run_shell(command: str) -> Tuple[int, str]:
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


def _spawn(command: List[str]) -> Optional[str]:
    try:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return None
    except FileNotFoundError:
        return f"找不到命令：{command[0]}"
    except Exception as exc:
        return str(exc)


def _pgrep_any(names: List[str]) -> bool:
    for n in names:
        code, _ = _run_shell(f"pgrep -x {shlex.quote(n)} >/dev/null 2>&1")
        if code == 0:
            return True
    return False


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _write_text(path: Path, content: str) -> None:
    _ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def update_kv_config(path: Path, updates: Dict[str, str]) -> None:
    """Update tint2-style key=value config while preserving other lines."""
    if not path.exists():
        raise FileNotFoundError(str(path))

    lines = _read_text(path).splitlines(keepends=True)
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

    _write_text(path, "".join(out))


def upsert_openbox_autostart_block(
    autostart_path: Path,
    *,
    wallpaper_path: Optional[str],
    wallpaper_enabled: bool,
    conky_enabled: bool,
) -> None:
    _ensure_parent(autostart_path)

    existing = _read_text(autostart_path) if autostart_path.exists() else ""
    if existing.strip() == "":
        existing = "#!/bin/sh\n\n"
    elif not existing.startswith("#!"):
        existing = "#!/bin/sh\n\n" + existing

    block_lines: List[str] = [AUTOSTART_BEGIN, "# Managed by ParticleDE Config Center"]

    if wallpaper_enabled and wallpaper_path:
        quoted = shlex.quote(wallpaper_path)
        block_lines.append(f"feh --bg-scale {quoted} &")

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

    _write_text(autostart_path, updated)
    try:
        os.chmod(autostart_path, 0o755)
    except Exception:
        pass


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

    # Clear existing actions
    for a in list(keybind):
        keybind.remove(a)

    action = ET.SubElement(keybind, f"{ns}action", {"name": "Execute"})
    cmd = ET.SubElement(action, f"{ns}command")
    cmd.text = command

    tree.write(rc_xml_path, encoding="UTF-8", xml_declaration=True)


def restart_component(kind: str) -> Tuple[bool, str]:
    if kind == "tint2_restart":
        _run_shell("pkill -x tint2 >/dev/null 2>&1 || true")
        err = _spawn(["tint2"]) 
        if err:
            return False, err
        return True, "tint2 已重启"

    if kind == "tint2_stop":
        _run_shell("pkill -x tint2 >/dev/null 2>&1 || true")
        return True, "tint2 已停止"

    if kind == "tint2_start":
        err = _spawn(["tint2"]) 
        if err:
            return False, err
        return True, "tint2 已启动"

    if kind == "pcmanfm_start":
        err = _spawn(["pcmanfm", "--desktop"]) 
        if err:
            return False, err
        return True, "桌面(PCManFM) 已启动"

    if kind == "pcmanfm_stop":
        _run_shell("pkill -x pcmanfm >/dev/null 2>&1 || true")
        return True, "桌面(PCManFM) 已停止"

    if kind == "conky_start":
        err = _spawn(["conky"]) 
        if err:
            return False, err
        return True, "Conky 已启动"

    if kind == "conky_stop":
        _run_shell("pkill -x conky >/dev/null 2>&1 || true")
        return True, "Conky 已停止"

    if kind == "openbox_reconfigure":
        code, out = _run_shell("openbox --reconfigure 2>&1 || true")
        if code == 0:
            return True, "Openbox 已重载配置"
        return True, (out.strip() or "Openbox 重载命令已执行")

    return False, f"未知操作：{kind}"


class ConfigCenter(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.window: Optional[Gtk.ApplicationWindow] = None

        self.status_specs = [
            RunningStatus("Openbox", ["openbox"]),
            RunningStatus("tint2", ["tint2"]),
            RunningStatus("rofi", ["rofi"]),
            RunningStatus("pcmanfm", ["pcmanfm"]),
            RunningStatus("conky", ["conky"]),
        ]

    def do_activate(self):  # type: ignore[override]
        if self.window is None:
            self.window = Gtk.ApplicationWindow(application=self)
            self.window.set_title("ParticleDE 配置中心")
            self.window.set_default_size(820, 520)

            header = Gtk.HeaderBar(title="ParticleDE 配置中心")
            header.set_show_close_button(True)
            self.window.set_titlebar(header)

            root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            root.set_border_width(10)
            self.window.add(root)

            self.info_bar = Gtk.InfoBar()
            self.info_bar.set_no_show_all(True)
            self.info_label = Gtk.Label(label="")
            content = self.info_bar.get_content_area()
            content.add(self.info_label)
            root.pack_start(self.info_bar, False, False, 0)

            notebook = Gtk.Notebook()
            root.pack_start(notebook, True, True, 0)

            notebook.append_page(self._build_common_tab(), Gtk.Label(label="常用设置"))
            notebook.append_page(self._build_control_tab(), Gtk.Label(label="组件控制"))
            notebook.append_page(self._build_editor_tab(), Gtk.Label(label="配置文件"))

            self.window.show_all()
            self.info_bar.hide()

        self.window.present()

    def _show_message(self, text: str, kind: Gtk.MessageType = Gtk.MessageType.INFO) -> None:
        self.info_bar.set_message_type(kind)
        self.info_label.set_text(text)
        self.info_bar.show()
        GLib.timeout_add(4500, self._hide_info)

    def _hide_info(self) -> bool:
        self.info_bar.hide()
        return False

    def _build_common_tab(self) -> Gtk.Widget:
        grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        grid.set_border_width(10)

        row = 0

        # Wallpaper
        grid.attach(Gtk.Label(label="壁纸：", xalign=0), 0, row, 1, 1)
        self.wallpaper_btn = Gtk.FileChooserButton(title="选择壁纸", action=Gtk.FileChooserAction.OPEN)
        filt = Gtk.FileFilter()
        filt.set_name("Images")
        filt.add_mime_type("image/png")
        filt.add_mime_type("image/jpeg")
        filt.add_mime_type("image/webp")
        filt.add_pattern("*.png")
        filt.add_pattern("*.jpg")
        filt.add_pattern("*.jpeg")
        filt.add_pattern("*.webp")
        self.wallpaper_btn.add_filter(filt)
        grid.attach(self.wallpaper_btn, 1, row, 2, 1)

        row += 1
        self.wallpaper_enable = Gtk.CheckButton(label="登录时自动设置壁纸（写入 Openbox autostart）")
        self.wallpaper_enable.set_active(True)
        grid.attach(self.wallpaper_enable, 1, row, 2, 1)

        row += 1
        self.conky_enable = Gtk.CheckButton(label="登录时自动启动 Conky（写入 Openbox autostart）")
        self.conky_enable.set_active(False)
        grid.attach(self.conky_enable, 1, row, 2, 1)

        # Keybinds
        row += 1
        grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, row, 3, 1)

        row += 1
        grid.attach(Gtk.Label(label="启动器命令（Super+Space）：", xalign=0), 0, row, 1, 1)
        self.launcher_entry = Gtk.Entry()
        self.launcher_entry.set_text("rofi -show run")
        grid.attach(self.launcher_entry, 1, row, 2, 1)

        row += 1
        grid.attach(Gtk.Label(label="终端命令（Super+Enter）：", xalign=0), 0, row, 1, 1)
        self.terminal_entry = Gtk.Entry()
        self.terminal_entry.set_text("xterm")
        grid.attach(self.terminal_entry, 1, row, 2, 1)

        # Tint2 quick settings
        row += 1
        grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, row, 3, 1)

        row += 1
        grid.attach(Gtk.Label(label="面板位置：", xalign=0), 0, row, 1, 1)
        self.panel_pos = Gtk.ComboBoxText()
        self.panel_pos.append_text("底部")
        self.panel_pos.append_text("顶部")
        self.panel_pos.set_active(0)
        grid.attach(self.panel_pos, 1, row, 1, 1)

        grid.attach(Gtk.Label(label="高度：", xalign=0), 2, row, 1, 1)
        self.panel_height = Gtk.SpinButton()
        self.panel_height.set_adjustment(Gtk.Adjustment(30, 16, 120, 1, 5, 0))
        grid.attach(self.panel_height, 3, row, 1, 1)

        row += 2
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.apply_btn = Gtk.Button(label="保存并应用")
        self.apply_btn.connect("clicked", self._on_apply)
        btn_box.pack_start(self.apply_btn, False, False, 0)

        self.reload_btn = Gtk.Button(label="重载 Openbox")
        self.reload_btn.connect("clicked", lambda *_: self._do_action("openbox_reconfigure"))
        btn_box.pack_start(self.reload_btn, False, False, 0)

        self.restart_tint2_btn = Gtk.Button(label="重启 tint2")
        self.restart_tint2_btn.connect("clicked", lambda *_: self._do_action("tint2_restart"))
        btn_box.pack_start(self.restart_tint2_btn, False, False, 0)

        grid.attach(btn_box, 1, row, 2, 1)

        # Hints
        row += 1
        hint = Gtk.Label(
            label=(
                "提示：快捷键写入 ~/.config/openbox/rc.xml 后，需要点击“重载 Openbox”生效。\n"
                "面板修改写入 ~/.config/tint2/tint2rc 后，点击“重启 tint2”生效。"
            ),
            xalign=0,
        )
        hint.set_line_wrap(True)
        grid.attach(hint, 0, row, 3, 1)

        sc = Gtk.ScrolledWindow()
        sc.set_hexpand(True)
        sc.set_vexpand(True)
        sc.add_with_viewport(grid)
        return sc

    def _build_control_tab(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(10)

        self.status_label = Gtk.Label(label="")
        self.status_label.set_xalign(0)
        box.pack_start(self.status_label, False, False, 0)

        btn_grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        box.pack_start(btn_grid, False, False, 0)

        row = 0
        btn_grid.attach(Gtk.Label(label="tint2：", xalign=0), 0, row, 1, 1)
        btn_grid.attach(self._action_btn("启动", "tint2_start"), 1, row, 1, 1)
        btn_grid.attach(self._action_btn("停止", "tint2_stop"), 2, row, 1, 1)
        btn_grid.attach(self._action_btn("重启", "tint2_restart"), 3, row, 1, 1)

        row += 1
        btn_grid.attach(Gtk.Label(label="桌面(PCManFM)：", xalign=0), 0, row, 1, 1)
        btn_grid.attach(self._action_btn("启动", "pcmanfm_start"), 1, row, 1, 1)
        btn_grid.attach(self._action_btn("停止", "pcmanfm_stop"), 2, row, 1, 1)

        row += 1
        btn_grid.attach(Gtk.Label(label="Conky：", xalign=0), 0, row, 1, 1)
        btn_grid.attach(self._action_btn("启动", "conky_start"), 1, row, 1, 1)
        btn_grid.attach(self._action_btn("停止", "conky_stop"), 2, row, 1, 1)

        row += 1
        btn_grid.attach(Gtk.Label(label="Openbox：", xalign=0), 0, row, 1, 1)
        btn_grid.attach(self._action_btn("重载配置", "openbox_reconfigure"), 1, row, 2, 1)

        refresh = Gtk.Button(label="刷新状态")
        refresh.connect("clicked", lambda *_: self._refresh_status())
        box.pack_start(refresh, False, False, 0)

        self._refresh_status()
        return box

    def _build_editor_tab(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        outer.set_border_width(10)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        outer.pack_start(top, False, False, 0)

        top.pack_start(Gtk.Label(label="选择配置文件："), False, False, 0)
        self.file_combo = Gtk.ComboBoxText()

        self.known_files: List[Tuple[str, Path]] = [
            ("Openbox rc.xml", OPENBOX_RC),
            ("Openbox autostart", OPENBOX_AUTOSTART),
            ("tint2rc", TINT2_RC),
            ("rofi config.rasi (如果存在)", ROFI_RC),
            ("conky.conf (如果存在)", CONKY_RC),
        ]
        for label, _ in self.known_files:
            self.file_combo.append_text(label)
        self.file_combo.set_active(0)
        self.file_combo.connect("changed", lambda *_: self._load_selected_file())
        top.pack_start(self.file_combo, False, False, 0)

        load_btn = Gtk.Button(label="重新加载")
        load_btn.connect("clicked", lambda *_: self._load_selected_file())
        top.pack_start(load_btn, False, False, 0)

        save_btn = Gtk.Button(label="保存")
        save_btn.connect("clicked", lambda *_: self._save_selected_file())
        top.pack_start(save_btn, False, False, 0)

        self.file_path_label = Gtk.Label(label="")
        self.file_path_label.set_xalign(0)
        outer.pack_start(self.file_path_label, False, False, 0)

        self.textview = Gtk.TextView()
        self.textview.set_monospace(True)
        self.textbuffer = self.textview.get_buffer()

        sc = Gtk.ScrolledWindow()
        sc.set_hexpand(True)
        sc.set_vexpand(True)
        sc.add(self.textview)
        outer.pack_start(sc, True, True, 0)

        self._load_selected_file()
        return outer

    def _action_btn(self, label: str, action: str) -> Gtk.Button:
        b = Gtk.Button(label=label)
        b.connect("clicked", lambda *_: self._do_action(action))
        return b

    def _do_action(self, action: str) -> None:
        ok, msg = restart_component(action)
        self._show_message(msg, Gtk.MessageType.INFO if ok else Gtk.MessageType.ERROR)
        self._refresh_status()

    def _refresh_status(self) -> None:
        parts = []
        for spec in self.status_specs:
            running = _pgrep_any(spec.process_names)
            parts.append(f"{spec.name}: {'运行中' if running else '未运行'}")
        self.status_label.set_text(" | ".join(parts))

    def _on_apply(self, *_):
        # 1) Openbox keybinds
        launcher_cmd = self.launcher_entry.get_text().strip() or "rofi -show run"
        terminal_cmd = self.terminal_entry.get_text().strip() or "xterm"

        try:
            set_openbox_keybind_execute(OPENBOX_RC, "W-space", launcher_cmd)
            set_openbox_keybind_execute(OPENBOX_RC, "W-Return", terminal_cmd)
        except FileNotFoundError:
            self._show_message(
                f"找不到 Openbox 配置文件：{OPENBOX_RC}（请先运行安装脚本复制配置）",
                Gtk.MessageType.ERROR,
            )
            return
        except Exception as exc:
            self._show_message(f"写入 Openbox 快捷键失败：{exc}", Gtk.MessageType.ERROR)
            return

        # 2) Openbox autostart (wallpaper + conky)
        wp_path = self.wallpaper_btn.get_filename()
        try:
            upsert_openbox_autostart_block(
                OPENBOX_AUTOSTART,
                wallpaper_path=wp_path,
                wallpaper_enabled=self.wallpaper_enable.get_active(),
                conky_enabled=self.conky_enable.get_active(),
            )
        except Exception as exc:
            self._show_message(f"写入 Openbox autostart 失败：{exc}", Gtk.MessageType.ERROR)
            return

        # 3) Tint2 quick settings
        pos = "bottom center" if self.panel_pos.get_active() == 0 else "top center"
        height = int(self.panel_height.get_value())
        try:
            # Keep width at 100%, only change height
            update_kv_config(TINT2_RC, {"panel_position": pos, "panel_size": f"100% {height}"})
        except FileNotFoundError:
            self._show_message(
                f"找不到 tint2 配置文件：{TINT2_RC}（请先运行安装脚本复制配置）",
                Gtk.MessageType.ERROR,
            )
            return
        except Exception as exc:
            self._show_message(f"写入 tint2rc 失败：{exc}", Gtk.MessageType.ERROR)
            return

        self._show_message("已保存：快捷键 / autostart / 面板设置")

    def _selected_file(self) -> Tuple[str, Path]:
        idx = self.file_combo.get_active()
        if idx < 0:
            return self.known_files[0]
        return self.known_files[idx]

    def _load_selected_file(self) -> None:
        label, path = self._selected_file()
        self.file_path_label.set_text(f"{label}: {path}")

        if not path.exists():
            self.textbuffer.set_text(f"# 文件不存在：{path}\n")
            return

        try:
            self.textbuffer.set_text(_read_text(path))
        except Exception as exc:
            self.textbuffer.set_text(f"# 读取失败：{exc}\n")

    def _save_selected_file(self) -> None:
        label, path = self._selected_file()
        start, end = self.textbuffer.get_bounds()
        content = self.textbuffer.get_text(start, end, True)

        # Avoid accidentally creating rc.xml from scratch via editor; guide users.
        if path == OPENBOX_RC and not path.exists():
            self._show_message("rc.xml 不存在时不建议在此创建，请先用安装脚本复制默认配置", Gtk.MessageType.ERROR)
            return

        try:
            _write_text(path, content)
        except Exception as exc:
            self._show_message(f"保存失败：{exc}", Gtk.MessageType.ERROR)
            return

        self._show_message(f"已保存：{path}")


def main() -> int:
    app = ConfigCenter()
    return app.run([])


if __name__ == "__main__":
    raise SystemExit(main())
