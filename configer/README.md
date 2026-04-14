# ParticleDE 配置中心

这是一个用于 ParticleDE 的**简易图形化配置中心**，基于 Python + GTK3（PyGObject）。

## 依赖

在 Ubuntu 上安装：

```bash
sudo apt update
sudo apt install -y python3-gi gir1.2-gtk-3.0
```

（可选）为了让“一键应用/重启组件”更完整，建议确保这些组件已安装：`openbox`、`tint2`、`rofi`、`pcmanfm`、`feh`、`conky`。

## 运行

在 ParticleDE 会话内运行：

```bash
python3 configer/main.py
```

## 会修改哪些文件

- `~/.config/openbox/rc.xml`：写入/更新常用快捷键（默认：`Super+Space` 启动 rofi，`Super+Enter` 启动终端）
- `~/.config/openbox/autostart`：写入一个带标记的 ParticleDE 区块（用于壁纸/Conky 自启动等）
- `~/.config/tint2/tint2rc`：修改 `panel_position` 与 `panel_size`（高度）

说明：对 `autostart` 只会更新 `### ParticleDE CONFIG CENTER BEGIN/END` 标记中的内容，不会覆盖你已有的其它自定义。
