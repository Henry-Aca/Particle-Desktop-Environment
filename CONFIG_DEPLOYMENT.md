# Particle Desktop Environment - Configuration Deployment

## 概述

ParticleDE 使用统一的配置部署系统来确保项目配置文件正确复制到用户目录。这个系统通过 `scripts/copy_configs.sh` 脚本实现，在安装和语言切换过程中自动调用。

## 配置文件结构

```
Particle-Desktop-Environment/
├── config/                    # 项目配置文件（模板和生成的文件）
│   ├── openbox/
│   │   ├── menu.xml          # 本地化菜单（由语言切换生成）
│   │   └── rc.xml            # 窗口管理器配置
│   ├── rofi/
│   │   ├── config.rasi       # 本地化启动器配置（由语言切换生成）
│   │   ├── colors/           # 颜色主题
│   │   └── shared/           # 共享主题
│   ├── tint2/
│   │   └── tint2rc           # 面板配置
│   ├── pcmanfm/
│   │   ├── default/
│   │   │   └── pcmanfm.conf  # 文件管理器配置
│   │   └── desktop-items-0.conf # 桌面项配置
│   ├── gtkrc-2.0            # GTK 2.0 配置
│   ├── gtk-3.0/             # GTK 3.0 配置
│   └── qt5ct/                # Qt 主题配置
│       └── qt5ct.conf
└── ~/.config/               # 用户配置文件（部署目标）
    ├── openbox/
    ├── rofi/
    ├── tint2/
    ├── pcmanfm/
    └── particlede/
```

## 部署流程

### 1. 安装时部署（setup_env.sh）

在初次安装 ParticleDE 时，`setup_env.sh` 调用 `copy_configs.sh` 将所有配置文件从项目目录复制到用户目录：

```bash
./scripts/setup_env.sh  # 自动调用 copy_configs.sh
```

### 2. 语言切换时部署（switch_language.sh）

语言切换时会先生成本地化配置文件，然后调用 `copy_configs.sh` 部署到用户目录：

```bash
./scripts/switch_language.sh zh_CN  # 生成中文配置并部署
./scripts/switch_language.sh en_US  # 生成英文配置并部署
```

### 3. 手动部署

可以随时手动运行配置部署：

```bash
./scripts/copy_configs.sh              # 部署所有配置
./scripts/copy_configs.sh --help       # 显示帮助信息
```

## 部署内容

`copy_configs.sh` 脚本处理以下配置文件的部署：

- **Openbox**: `menu.xml` (本地化菜单), `rc.xml` (窗口管理器配置)
- **Rofi**: `config.rasi` (本地化启动器配置), `colors/`, `shared/` (主题文件)
- **Tint2**: `tint2rc` (面板配置)
- **PCManFM**: `pcmanfm.conf`, `desktop-items-0.conf` (文件管理器配置)
- **GTK**: `gtkrc-2.0`, `gtk-3.0/` (GTK 主题配置)
- **Qt**: `qt5ct.conf` (Qt 主题配置)

## 故障排除

### 配置未生效

如果配置更改后未生效，请检查：

1. 配置文件是否正确生成了（在 `config/` 目录）
2. 配置文件是否正确部署了（在 `~/.config/` 目录）
3. 应用程序是否重启了（特别是 Openbox 需要 `openbox --restart`）

### 手动重新部署

如果需要手动重新部署所有配置：

```bash
./scripts/copy_configs.sh
```

### 检查部署状态

查看用户配置目录的时间戳：

```bash
ls -la ~/.config/openbox/
ls -la ~/.config/rofi/
```

## 扩展新配置

要添加新的配置文件类型：

1. 在项目 `config/` 目录下添加配置文件
2. 在 `copy_configs.sh` 中添加相应的复制函数
3. 在 `main()` 函数中调用新的复制函数
4. 更新此文档

## 相关脚本

- `scripts/copy_configs.sh` - 配置部署脚本
- `scripts/switch_language.sh` - 语言切换脚本（调用配置部署）
- `scripts/setup_env.sh` - 环境安装脚本（调用配置部署）
- `scripts/particlede-session` - 会话启动脚本（使用已部署的配置）