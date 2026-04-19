#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import gi

gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, Gtk  # noqa: E402

from backend import (
    CONKY_RC,
    OPENBOX_AUTOSTART,
    OPENBOX_RC,
    PARTICLEDE_SESSION_ENV,
    ROFI_RC,
    THEMES_DIR,
    TINT2_RC,
    RunningStatus,
    apply_wallpaper_now,
    list_installed_themes,
    parse_managed_autostart_settings,
    parse_tint2_panel_height,
    parse_tint2_panel_position,
    pgrep_any,
    read_kv_config,
    read_simple_env,
    restart_component,
    set_openbox_keybind_execute,
    set_openbox_theme_name,
    theme_has_openbox,
    update_kv_config,
    upsert_openbox_autostart_block,
    write_particlede_session_env,
    write_text,
    read_text,
)
from i18n import I18n


APP_ID = "org.particlede.ConfigCenter"


class ConfigCenter(Gtk.Application):
    def __init__(self, i18n: I18n) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.t = i18n.t
        self.window: Optional[Gtk.ApplicationWindow] = None

        self.status_specs = [
            RunningStatus(self.t("component.openbox"), ["openbox"]),
            RunningStatus(self.t("component.tint2"), ["tint2"]),
            RunningStatus(self.t("component.rofi"), ["rofi"]),
            RunningStatus(self.t("component.pcmanfm"), ["pcmanfm"]),
            RunningStatus(self.t("component.conky"), ["conky"]),
        ]

    def do_activate(self):  # type: ignore[override]
        if self.window is None:
            self.window = Gtk.ApplicationWindow(application=self)
            self.window.set_title(self.t("app.title"))
            self.window.set_default_size(860, 560)

            header = Gtk.HeaderBar(title=self.t("app.title"))
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

            notebook.append_page(self._build_appearance_tab(), Gtk.Label(label=self.t("tab.appearance")))
            notebook.append_page(self._build_common_tab(), Gtk.Label(label=self.t("tab.common")))
            notebook.append_page(self._build_control_tab(), Gtk.Label(label=self.t("tab.control")))
            notebook.append_page(self._build_editor_tab(), Gtk.Label(label=self.t("tab.files")))

            self.window.show_all()
            self.info_bar.hide()

        self.window.present()

    # -------------------- helpers --------------------

    def _show_message(self, text: str, kind: Gtk.MessageType = Gtk.MessageType.INFO) -> None:
        self.info_bar.set_message_type(kind)
        self.info_label.set_text(text)
        self.info_bar.show()
        GLib.timeout_add(4500, self._hide_info)

    def _hide_info(self) -> bool:
        self.info_bar.hide()
        return False

    def _do_action(self, action: str) -> None:
        ok, msg_key, kwargs = restart_component(action)
        self._show_message(
            self.t(msg_key, **(kwargs or {})),
            Gtk.MessageType.INFO if ok else Gtk.MessageType.ERROR,
        )
        self._refresh_status()

    # -------------------- tabs --------------------

    def _build_appearance_tab(self) -> Gtk.Widget:
        grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        grid.set_border_width(10)

        saved = parse_managed_autostart_settings(OPENBOX_AUTOSTART)
        tint_cfg = read_kv_config(TINT2_RC)

        row = 0

        # Theme
        grid.attach(Gtk.Label(label=self.t("appearance.theme.label"), xalign=0), 0, row, 1, 1)
        self.theme_combo = Gtk.ComboBoxText()

        themes = list_installed_themes(THEMES_DIR)
        for tname in themes:
            self.theme_combo.append_text(tname)

        current_env = read_simple_env(PARTICLEDE_SESSION_ENV)
        current_gtk = current_env.get("GTK_THEME") or "Arc-Dark"

        if current_gtk not in themes:
            self.theme_combo.append_text(current_gtk)
            themes.append(current_gtk)

        if themes:
            try:
                self.theme_combo.set_active(themes.index(current_gtk))
            except ValueError:
                self.theme_combo.set_active(0)

        grid.attach(self.theme_combo, 1, row, 2, 1)

        row += 1
        theme_hint = Gtk.Label(label=self.t("appearance.theme.hint"), xalign=0)
        theme_hint.set_line_wrap(True)
        grid.attach(theme_hint, 0, row, 3, 1)

        # Wallpaper
        row += 1
        grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, row, 3, 1)

        row += 1
        grid.attach(Gtk.Label(label=self.t("appearance.wallpaper.label"), xalign=0), 0, row, 1, 1)
        self.wallpaper_btn = Gtk.FileChooserButton(title=self.t("appearance.wallpaper.label"), action=Gtk.FileChooserAction.OPEN)
        filt = Gtk.FileFilter()
        filt.set_name(self.t("appearance.wallpaper.filter_images"))
        filt.add_mime_type("image/png")
        filt.add_mime_type("image/jpeg")
        filt.add_mime_type("image/webp")
        filt.add_pattern("*.png")
        filt.add_pattern("*.jpg")
        filt.add_pattern("*.jpeg")
        filt.add_pattern("*.webp")
        self.wallpaper_btn.add_filter(filt)
        grid.attach(self.wallpaper_btn, 1, row, 2, 1)

        if saved.get("wallpaper_path"):
            try:
                self.wallpaper_btn.set_filename(saved["wallpaper_path"])  # type: ignore[arg-type]
            except Exception:
                pass

        row += 1
        self.wallpaper_enable = Gtk.CheckButton(label=self.t("appearance.wallpaper.enable"))
        self.wallpaper_enable.set_active(saved.get("wallpaper_enabled") != "0")
        grid.attach(self.wallpaper_enable, 1, row, 2, 1)

        row += 1
        self.conky_enable = Gtk.CheckButton(label=self.t("appearance.conky.enable"))
        self.conky_enable.set_active(saved.get("conky_enabled") == "1")
        grid.attach(self.conky_enable, 1, row, 2, 1)

        # tint2 panel
        row += 1
        grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, row, 3, 1)

        row += 1
        grid.attach(Gtk.Label(label=self.t("appearance.panel.position"), xalign=0), 0, row, 1, 1)
        self.panel_pos = Gtk.ComboBoxText()
        self.panel_pos.append_text(self.t("appearance.panel.position.bottom"))
        self.panel_pos.append_text(self.t("appearance.panel.position.top"))
        pos = parse_tint2_panel_position(tint_cfg.get("panel_position", ""))
        self.panel_pos.set_active(0 if pos != "top" else 1)
        grid.attach(self.panel_pos, 1, row, 1, 1)

        grid.attach(Gtk.Label(label=self.t("appearance.panel.height"), xalign=0), 2, row, 1, 1)
        self.panel_height = Gtk.SpinButton()
        self.panel_height.set_adjustment(Gtk.Adjustment(30, 16, 120, 1, 5, 0))
        current_height = parse_tint2_panel_height(tint_cfg.get("panel_size", ""))
        if current_height is not None:
            self.panel_height.set_value(current_height)
        grid.attach(self.panel_height, 3, row, 1, 1)

        # Buttons
        row += 2
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        apply_btn = Gtk.Button(label=self.t("appearance.apply"))
        apply_btn.connect("clicked", self._on_apply_appearance)
        btn_box.pack_start(apply_btn, False, False, 0)

        reload_btn = Gtk.Button(label=self.t("appearance.reload_openbox"))
        reload_btn.connect("clicked", lambda *_: self._do_action("openbox_reconfigure"))
        btn_box.pack_start(reload_btn, False, False, 0)

        restart_tint2_btn = Gtk.Button(label=self.t("appearance.restart_tint2"))
        restart_tint2_btn.connect("clicked", lambda *_: self._do_action("tint2_restart"))
        btn_box.pack_start(restart_tint2_btn, False, False, 0)

        grid.attach(btn_box, 1, row, 2, 1)

        sc = Gtk.ScrolledWindow()
        sc.set_hexpand(True)
        sc.set_vexpand(True)
        sc.add_with_viewport(grid)
        return sc

    def _build_common_tab(self) -> Gtk.Widget:
        grid = Gtk.Grid(column_spacing=12, row_spacing=10)
        grid.set_border_width(10)
        row = 0

        grid.attach(Gtk.Label(label=self.t("common.launcher.label"), xalign=0), 0, row, 1, 1)
        self.launcher_entry = Gtk.Entry()
        self.launcher_entry.set_text("rofi -show run")
        grid.attach(self.launcher_entry, 1, row, 2, 1)

        row += 1
        grid.attach(Gtk.Label(label=self.t("common.terminal.label"), xalign=0), 0, row, 1, 1)
        self.terminal_entry = Gtk.Entry()
        self.terminal_entry.set_text("xterm")
        grid.attach(self.terminal_entry, 1, row, 2, 1)

        row += 1
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        apply_btn = Gtk.Button(label=self.t("common.apply"))
        apply_btn.connect("clicked", self._on_apply_common)
        btn_box.pack_start(apply_btn, False, False, 0)

        reload_btn = Gtk.Button(label=self.t("appearance.reload_openbox"))
        reload_btn.connect("clicked", lambda *_: self._do_action("openbox_reconfigure"))
        btn_box.pack_start(reload_btn, False, False, 0)

        grid.attach(btn_box, 1, row, 2, 1)

        row += 1
        hint = Gtk.Label(label=self.t("common.hint"), xalign=0)
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
        btn_grid.attach(Gtk.Label(label=self.t("control.tint2"), xalign=0), 0, row, 1, 1)
        btn_grid.attach(self._action_btn(self.t("control.start"), "tint2_start"), 1, row, 1, 1)
        btn_grid.attach(self._action_btn(self.t("control.stop"), "tint2_stop"), 2, row, 1, 1)
        btn_grid.attach(self._action_btn(self.t("control.restart"), "tint2_restart"), 3, row, 1, 1)

        row += 1
        btn_grid.attach(Gtk.Label(label=self.t("control.pcmanfm"), xalign=0), 0, row, 1, 1)
        btn_grid.attach(self._action_btn(self.t("control.start"), "pcmanfm_start"), 1, row, 1, 1)
        btn_grid.attach(self._action_btn(self.t("control.stop"), "pcmanfm_stop"), 2, row, 1, 1)

        row += 1
        btn_grid.attach(Gtk.Label(label=self.t("control.conky"), xalign=0), 0, row, 1, 1)
        btn_grid.attach(self._action_btn(self.t("control.start"), "conky_start"), 1, row, 1, 1)
        btn_grid.attach(self._action_btn(self.t("control.stop"), "conky_stop"), 2, row, 1, 1)

        row += 1
        btn_grid.attach(Gtk.Label(label=self.t("control.openbox"), xalign=0), 0, row, 1, 1)
        btn_grid.attach(self._action_btn(self.t("control.reconfigure"), "openbox_reconfigure"), 1, row, 2, 1)

        refresh = Gtk.Button(label=self.t("control.refresh"))
        refresh.connect("clicked", lambda *_: self._refresh_status())
        box.pack_start(refresh, False, False, 0)

        self._refresh_status()
        return box

    def _build_editor_tab(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        outer.set_border_width(10)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        outer.pack_start(top, False, False, 0)

        top.pack_start(Gtk.Label(label=self.t("files.choose")), False, False, 0)
        self.file_combo = Gtk.ComboBoxText()

        self.known_files: List[Tuple[str, Path]] = [
            (self.t("files.openbox_rc"), OPENBOX_RC),
            (self.t("files.openbox_autostart"), OPENBOX_AUTOSTART),
            (self.t("files.tint2rc"), TINT2_RC),
            (self.t("files.rofi"), ROFI_RC),
            (self.t("files.conky"), CONKY_RC),
        ]
        for label, _ in self.known_files:
            self.file_combo.append_text(label)
        self.file_combo.set_active(0)
        self.file_combo.connect("changed", lambda *_: self._load_selected_file())
        top.pack_start(self.file_combo, False, False, 0)

        load_btn = Gtk.Button(label=self.t("files.reload"))
        load_btn.connect("clicked", lambda *_: self._load_selected_file())
        top.pack_start(load_btn, False, False, 0)

        save_btn = Gtk.Button(label=self.t("files.save"))
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

    # -------------------- actions --------------------

    def _action_btn(self, label: str, action: str) -> Gtk.Button:
        b = Gtk.Button(label=label)
        b.connect("clicked", lambda *_: self._do_action(action))
        return b

    def _refresh_status(self) -> None:
        parts = []
        for spec in self.status_specs:
            running = pgrep_any(spec.process_names)
            parts.append(f"{spec.name}: {self.t('status.running') if running else self.t('status.stopped')}")
        self.status_label.set_text(" | ".join(parts))

    def _on_apply_common(self, *_):
        launcher_cmd = self.launcher_entry.get_text().strip() or "rofi -show run"
        terminal_cmd = self.terminal_entry.get_text().strip() or "xterm"

        try:
            set_openbox_keybind_execute(OPENBOX_RC, "W-space", launcher_cmd)
            set_openbox_keybind_execute(OPENBOX_RC, "W-Return", terminal_cmd)
        except FileNotFoundError:
            self._show_message(self.t("err.missing.openbox_rc", path=str(OPENBOX_RC)), Gtk.MessageType.ERROR)
            return
        except Exception as exc:
            self._show_message(self.t("err.write.openbox_keys", err=str(exc)), Gtk.MessageType.ERROR)
            return

        self._show_message(self.t("msg.saved.keybinds"))

    def _on_apply_appearance(self, *_):
        # theme
        selected_theme = self.theme_combo.get_active_text() if hasattr(self, "theme_combo") else None
        if selected_theme:
            try:
                write_particlede_session_env(gtk_theme=selected_theme)
            except Exception as exc:
                self._show_message(self.t("err.write.session_theme", err=str(exc)), Gtk.MessageType.ERROR)
                return

            if theme_has_openbox(THEMES_DIR, selected_theme):
                try:
                    set_openbox_theme_name(OPENBOX_RC, selected_theme)
                except FileNotFoundError:
                    pass
                except Exception as exc:
                    self._show_message(self.t("err.write.openbox_theme", err=str(exc)), Gtk.MessageType.ERROR)
                    return

        # autostart (wallpaper + conky)
        wp_path = self.wallpaper_btn.get_filename()
        try:
            upsert_openbox_autostart_block(
                OPENBOX_AUTOSTART,
                wallpaper_path=wp_path,
                wallpaper_enabled=self.wallpaper_enable.get_active(),
                conky_enabled=self.conky_enable.get_active(),
            )
        except Exception as exc:
            self._show_message(self.t("err.write.autostart", err=str(exc)), Gtk.MessageType.ERROR)
            return

        if self.wallpaper_enable.get_active() and wp_path:
            ok, msg_key, kwargs = apply_wallpaper_now(wp_path)
            if not ok:
                self._show_message(self.t(msg_key, **(kwargs or {})), Gtk.MessageType.ERROR)
                return

        # tint2
        pos = "bottom center" if self.panel_pos.get_active() == 0 else "top center"
        height = int(self.panel_height.get_value())
        try:
            update_kv_config(TINT2_RC, {"panel_position": pos, "panel_size": f"100% {height}"})
        except FileNotFoundError:
            self._show_message(self.t("err.missing.tint2rc", path=str(TINT2_RC)), Gtk.MessageType.ERROR)
            return
        except Exception as exc:
            self._show_message(self.t("err.write.tint2rc", err=str(exc)), Gtk.MessageType.ERROR)
            return

        # message
        msg = self.t("msg.saved.base")
        if selected_theme:
            msg += self.t("msg.saved.with_theme")
        self._show_message(msg)

    def _selected_file(self) -> Tuple[str, Path]:
        idx = self.file_combo.get_active()
        if idx < 0:
            return self.known_files[0]
        return self.known_files[idx]

    def _load_selected_file(self) -> None:
        label, path = self._selected_file()
        self.file_path_label.set_text(f"{label}: {path}")

        if not path.exists():
            self.textbuffer.set_text(self.t("files.missing", path=str(path)))
            return

        try:
            self.textbuffer.set_text(read_text(path))
        except Exception as exc:
            self.textbuffer.set_text(self.t("files.read_failed", err=str(exc)))

    def _save_selected_file(self) -> None:
        _, path = self._selected_file()
        start, end = self.textbuffer.get_bounds()
        content = self.textbuffer.get_text(start, end, True)

        if path == OPENBOX_RC and not path.exists():
            self._show_message(self.t("files.rcxml_create_blocked"), Gtk.MessageType.ERROR)
            return

        try:
            write_text(path, content)
        except Exception as exc:
            self._show_message(self.t("files.save_failed", err=str(exc)), Gtk.MessageType.ERROR)
            return

        self._show_message(self.t("files.saved", path=str(path)))
