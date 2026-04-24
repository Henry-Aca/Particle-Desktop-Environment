#!/bin/bash
# ParticleDE 环境设置脚本
# 此脚本用于在干净的Linux系统（Debian/Ubuntu系）上安装和配置ParticleDE桌面环境。
# ParticleDE是一个轻量级桌面环境，基于Openbox窗口管理器，集成tint2面板、rofi启动器、PCManFM文件管理器和conky系统监控。
# 脚本目标：兼容中文环境、统一主题风格（解决Qt/GTK应用风格割裂）、桌面主题与全局GTK主题适配，并尽可能轻量化。
# 重构说明：将不同需求的组件和配置分门别类为函数，每个函数前添加详细注释说明目的，提高可读性和维护性。
# 注意：运行此脚本需要sudo权限，且在干净系统上执行以避免冲突。

set -e  # 遇到错误立即退出脚本，确保安装过程的可靠性

# 函数：更新包列表并安装核心桌面组件
# 目的：安装ParticleDE的基础组件，包括窗口管理器、面板、启动器、文件管理器、系统监控、终端和显示管理器。
# 组件作用：openbox(窗口管理器)、tint2(面板)、rofi(启动器)、pcmanfm(文件管理器)、conky-all(系统监控)、xterm(终端)、lightdm系列(显示管理器)、x11工具(X会话支持)。
function update_and_install_core() {
    echo "[1/9] 更新包列表并安装核心桌面组件..."
    sudo apt update
    sudo apt install -y openbox tint2 rofi pcmanfm conky-all \
        lightdm lightdm-gtk-greeter x11-xserver-utils xinit x11-utils xfce4-terminal
}

# 函数：安装配置中心（Python+GTK3）并创建桌面图标
# 目的：提供一个“桌面上的配置中心图标”，点击即可启动图形化配置中心。
# 安装内容：
# - Python GTK3 依赖：python3-gi gir1.2-gtk-3.0
# - 程序文件：/usr/local/share/particlede/configer/main.py
# - 启动器：/usr/local/bin/particlede-config-center
# - 应用入口：/usr/share/applications/particlede-config-center.desktop
# - 桌面快捷方式：复制一份 .desktop 到用户的 Desktop 目录，并 chmod +x
function install_config_center_and_desktop_icon() {
    echo "[1b/7] 安装配置中心并创建桌面图标..."

    sudo apt install -y python3-gi gir1.2-gtk-3.0

    # 安装程序文件（配置中心已拆分为多个文件）
    sudo mkdir -p /usr/local/share/particlede/configer
    sudo cp configer/*.py /usr/local/share/particlede/configer/
    sudo mkdir -p /usr/local/share/particlede/configer/strings
    sudo cp configer/strings/*.json /usr/local/share/particlede/configer/strings/

    # 安装语言切换脚本及其依赖到用户可写目录（供配置中心调用）
    mkdir -p "$HOME/.local/share/particlede/scripts" "$HOME/.local/share/particlede/config"
    cp scripts/switch_language.sh "$HOME/.local/share/particlede/scripts/switch_language.sh"
    cp scripts/copy_configs.sh "$HOME/.local/share/particlede/scripts/copy_configs.sh"
    chmod +x "$HOME/.local/share/particlede/scripts/switch_language.sh"
    chmod +x "$HOME/.local/share/particlede/scripts/copy_configs.sh"
    cp -r config/* "$HOME/.local/share/particlede/config/" 2>/dev/null || true

    # 安装启动器脚本
    sudo cp scripts/particlede-config-center /usr/local/bin/particlede-config-center
    sudo chmod +x /usr/local/bin/particlede-config-center

    # 安装应用入口
    sudo cp configer/particlede-config-center.desktop /usr/share/applications/particlede-config-center.desktop

    # 复制到“桌面”目录作为桌面图标（兼容中文目录）
    DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
    if [ -z "$DESKTOP_DIR" ]; then
        DESKTOP_DIR="$HOME/Desktop"
    fi
    mkdir -p "$DESKTOP_DIR"
    cp /usr/share/applications/particlede-config-center.desktop "$DESKTOP_DIR/ParticleDE-Config-Center.desktop" || true
    chmod +x "$DESKTOP_DIR/ParticleDE-Config-Center.desktop" || true
}

# 函数：安装中文环境支持包
# 目的：确保系统支持中文显示和输入，包括中文字体和输入法框架。
# 组件作用：fonts-noto-cjk(谷歌Noto CJK字体，覆盖中日韩)、fonts-wqy-microhei(文泉驿微米黑，常用中文字体)、fonts-wqy-zenhei(文泉驿正黑，常用中文字体)、fcitx5(输入法框架)、fcitx5-chinese-addons(中文输入法插件)、fcitx5-frontend-gtk3/gtk2/qt5(输入法前端支持)。
function install_chinese_support() {
    echo "[2/9] 安装中文环境支持包..."
    sudo apt install -y fonts-noto-cjk fonts-noto-cjk-extra fonts-wqy-microhei fonts-wqy-zenhei \
        fcitx5 fcitx5-chinese-addons fcitx5-frontend-gtk3 fcitx5-frontend-gtk2 fcitx5-frontend-qt5
}

# 函数：安装主题和外观相关包
# 目的：安装GTK/Qt主题、图标和相关工具，实现统一主题风格，解决Qt/GTK应用风格割裂。
# 组件作用：arc-theme(流行的GTK主题)、papirus-icon-theme(流行的图标主题)、lxappearance(GTK外观配置工具，可选)、gnome-themes-extra(提供额外的GTK主题，可选)、qt5-style-plugins和qt5ct(Qt应用主题支持)。
# 轻量化考虑：lxappearance和gnome-themes-extra可选（如果不需要GUI配置工具，可注释掉）。
function install_themes_and_appearance() {
    echo "[3/9] 安装主题和外观相关包..."
    sudo apt install -y arc-theme papirus-icon-theme # lxappearance
    # Qt主题支持
    sudo apt install -y qt5-style-plugins qt5ct
    # Nerd Font图标字体支持（尝试多个可能的包名）
    sudo apt install -y fonts-hack-ttf || true
    sudo apt install -y fonts-hack || true
    # 尝试安装 Nerd Font（包名因发行版而异）
    # (sudo apt install -y fonts-nerd-fonts 2>/dev/null || \
    #  sudo apt install -y nerd-fonts 2>/dev/null || \
    #  sudo apt install -y ttf-nerd-fonts 2>/dev/null || \
    #  sudo apt install -y font-awesome 2>/dev/null) && echo "Nerd Font installed successfully" || echo "Note: Nerd Font not available in repos, icons may not display"
    # fc-cache -fv 2>/dev/null || true
}

# 函数：安装桌面快捷方式文件
# 目的：将项目的桌面快捷方式文件安装到用户本地目录，使 tint2 等程序能够识别和使用这些快捷方式。
# 快捷方式内容：logout.desktop(注销)、shutdown.desktop(关机菜单)。
function install_desktop_files() {
    echo "[4/9] 安装桌面快捷方式文件..."
    mkdir -p ~/.local/share/applications
    if [ -d "applications" ]; then
        cp -r applications/*.desktop ~/.local/share/applications/
        update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
        echo "桌面快捷方式已安装"
    fi
}

# 函数：生成本地化配置文件
# 目的：从template文件生成适合当前语言的配置文件。
function generate_localized_files() {
    echo "[5/9] 生成本地化配置文件..."
    if [ -f "./scripts/switch_language.sh" ]; then
        ./scripts/switch_language.sh zh_CN || echo "警告：本地化文件生成失败，但将继续安装..."
    else
        echo "警告：未找到 switch_language.sh，无法生成本地化文件..."
    fi
}

# 函数：复制用户级配置文件
# 目的：将项目的配置文件复制到用户家目录，确保各组件的个性化设置（如窗口管理规则、面板布局、启动器样式）实现开箱即用。
# 配置内容：openbox(rc.xml窗口规则)、tint2(面板配置)、rofi(启动器样式)、pcmanfm(文件管理器设置)、gtkrc-2.0(GTK2配置)、
#          gtk-3.0(GTK3配置)、qt5ct(Qt主题配置)、language.conf(语言配置)。
function copy_user_configs() {
    echo "[6/9] 复制用户级配置文件..."
    # 使用统一的配置部署脚本
    if ! ./scripts/copy_configs.sh; then
        echo "警告：配置文件复制失败，但将继续安装..."
    fi
}

# 函数：配置主题和图标
# 目的：为ParticleDE会话准备主题、图标和字体配置，但不通过 gsettings 修改当前用户的全局 GTK 会话设置。
# 这样可以避免影响 GNOME 会话，同时让ParticleDE在其会话中使用Arc-Dark和Papirus-Dark。
function configure_themes_and_appearance() {
    echo "[7/9] 配置主题和图标..."
    # ParticleDE 会话通过 GTK_THEME=Arc-Dark 指向 Arc-Dark 主题。

    # 设置Openbox主题
    mkdir -p ~/.themes
    cp -r themes/* ~/.themes/ 2>/dev/null || true

    # 设置图标主题
    mkdir -p ~/.icons
    if [ -d "icons/Papirus-Dark" ]; then
        cp -r icons/Papirus-Dark ~/.icons/ 2>/dev/null || true
    elif [ -d "icons/Papyrus" ]; then
        cp -r icons/Papyrus ~/.icons/ 2>/dev/null || true
    elif [ -d "icons/Numix" ]; then
        cp -r icons/Numix ~/.icons/ 2>/dev/null || true
        cp -r icons/Numix-Light ~/.icons/ 2>/dev/null || true
    fi
}

# 函数：安装系统级会话文件
# 目的：将桌面会话脚本和入口文件安装到系统目录，使ParticleDE在LightDM中可用。这是桌面环境集成到系统的关键。
# 配置内容：particlede-session(启动脚本，运行openbox等组件，适配中文环境)、particlede.desktop(会话描述文件)。
function install_system_session_files() {
    echo "[8/9] 安装系统级会话文件..."
    sudo cp scripts/particlede-session /usr/local/bin/
    sudo chmod +x /usr/local/bin/particlede-session
    sudo cp config/particlede.desktop /usr/share/xsessions/
}

# 函数：显示用户提示
# 目的：提供安装完成后的使用指南，帮助用户快速上手ParticleDE。
function show_user_tips() {
    echo "[9/9] 显示用户提示..."
    echo "ParticleDE 环境配置已完成！"
    echo "请注销或重启，在登录界面选择 'ParticleDE' 会话。"
    echo ""
    echo "首次进入桌面后，你可以："
    echo "  - 按 Super键(Windows键) 启动程序"
    echo "  - 按 Ctrl+Space 切换中文输入法"
    echo "  - 使用 Alt+Ctrl+方向键 切换虚拟桌面"
    echo "  - 使用 Win+F1-F4 直接切换到对应桌面"
    echo "  - 在桌面右键打开中文菜单"
    echo "  - 在面板上看到时间和任务栏"
    echo ""
    echo "主题已统一配置，Qt和GTK应用将使用相同的风格。"
}

# 主执行流程：按顺序调用各函数，确保依赖关系（先安装包，再配置）
update_and_install_core
install_config_center_and_desktop_icon
install_chinese_support
install_themes_and_appearance
install_desktop_files
generate_localized_files
copy_user_configs
configure_themes_and_appearance
install_system_session_files
show_user_tips

echo "脚本执行完毕。如有问题，请检查日志或重新运行。"