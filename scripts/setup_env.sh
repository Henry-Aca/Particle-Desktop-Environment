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
    echo "[1/8] 更新包列表并安装核心桌面组件..."
    sudo apt update
    sudo apt install -y openbox tint2 rofi pcmanfm conky-all \
        xterm lightdm lightdm-gtk-greeter x11-xserver-utils xinit x11-utils
}

# 函数：安装中文环境支持包
# 目的：确保系统支持中文显示和输入，包括中文字体和输入法框架。
# 组件作用：fonts-noto-cjk(谷歌Noto CJK字体，覆盖中日韩)、fonts-wqy-microhei(文泉驿微米黑，常用中文字体)、fonts-wqy-zenhei(文泉驿正黑，常用中文字体)、fcitx5(输入法框架)、fcitx5-chinese-addons(中文输入法插件)、fcitx5-frontend-gtk3/gtk2/qt5(输入法前端支持)。
function install_chinese_support() {
    echo "[2/8] 安装中文环境支持包..."
    sudo apt install -y fonts-noto-cjk fonts-noto-cjk-extra fonts-wqy-microhei fonts-wqy-zenhei \
        fcitx5 fcitx5-chinese-addons fcitx5-frontend-gtk3 fcitx5-frontend-gtk2 fcitx5-frontend-qt5
}

# 函数：安装主题和外观相关包
# 目的：安装GTK/Qt主题、图标和相关工具，实现统一主题风格，解决Qt/GTK应用风格割裂。
# 组件作用：arc-theme(流行的GTK主题)、papirus-icon-theme(流行的图标主题)、lxappearance(GTK外观配置工具，可选)、gnome-themes-extra(提供额外的GTK主题，可选)、qt5-style-plugins和qt5ct(Qt应用主题支持)。
# 轻量化考虑：lxappearance和gnome-themes-extra可选（如果不需要GUI配置工具，可注释掉）。
function install_themes_and_appearance() {
    echo "[3/8] 安装主题和外观相关包..."
    sudo apt install -y arc-theme papirus-icon-theme # lxappearance gnome-themes-extra
    # Qt主题支持
    sudo apt install -y qt5-style-plugins qt5ct
}

# 函数：复制用户级配置文件
# 目的：将项目的配置文件复制到用户家目录，确保各组件的个性化设置（如窗口管理规则、面板布局、启动器样式）实现开箱。
# 配置内容：openbox(rc.xml窗口规则)、tint2(面板配置)、rofi(启动器样式)、pcmanfm(文件管理器设置)。
function copy_user_configs() {
    echo "[4/8] 复制用户级配置文件..."
    # 创建配置目录
    mkdir -p ~/.config/openbox ~/.config/tint2 ~/.config/rofi ~/.config/pcmanfm/default

    # 复制各组件配置
    cp -r config/openbox/* ~/.config/openbox/ 2>/dev/null || true
    cp -r config/tint2/* ~/.config/tint2/ 2>/dev/null || true
    cp -r config/rofi/* ~/.config/rofi/ 2>/dev/null || true
    cp -r config/pcmanfm/* ~/.config/pcmanfm/ 2>/dev/null || true
}

# 函数：配置主题和外观
# 目的：应用GTK主题、图标、字体和Openbox窗口主题，实现全局统一外观。这是主题适配的核心步骤。
# 配置内容：GTK主题(Arc-Dark)、图标(Papirus-Dark)、字体(Noto Sans)、Openbox窗口主题、Qt主题(qt5ct)。通过gsettings设置GTK主题和图标，复制配置文件确保GTK2/3兼容，安装Openbox和Qt主题。
function configure_themes_and_appearance() {
    echo "[5/8] 配置主题和外观..."
    # 设置GTK主题和图标
    gsettings set org.gnome.desktop.interface gtk-theme "Arc-Dark"
    gsettings set org.gnome.desktop.interface icon-theme "Papirus-Dark"
    mkdir -p ~/.config/gtk-3.0
    cp config/gtk-3.0/settings.ini ~/.config/gtk-3.0/settings.ini 2>/dev/null || true

    # 兼容GTK2
    cp config/gtkrc-2.0 ~/.gtkrc-2.0 2>/dev/null || true

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

    # 配置字体
    gsettings set org.gnome.desktop.interface font-name "Noto Sans 11"
    gsettings set org.gnome.desktop.interface document-font-name "Noto Sans 11"
    gsettings set org.gnome.desktop.interface monospace-font-name "Noto Mono 11"

    # 配置Qt主题
    mkdir -p ~/.config/qt5ct
    cp config/qt5ct/qt5ct.conf ~/.config/qt5ct/
}

# 函数：配置中文环境
# 目的：部署X会话配置文件，确保中文输入法正常工作。这是中文兼容的核心配置。
# 配置内容：将xprofile复制到用户家目录，设置环境变量（如LANG=zh_CN.UTF-8）和输入法相关变量（如GTK_IM_MODULE=fcitx、QT_IM_MODULE=fcitx、XMODIFIERS="@im=fcitx"），确保登录后环境变量生效，中文输入法可用。
function configure_chinese_environment() {
    echo "[6/8] 配置中文环境..."
    # 复制xprofile并设置执行权限
    cp config/xprofile ~/.xprofile
    chmod +x ~/.xprofile
}

# 函数：安装系统级会话文件
# 目的：将桌面会话脚本和入口文件安装到系统目录，使ParticleDE在LightDM中可用。这是桌面环境集成到系统的关键。
# 配置内容：particlede-session(启动脚本，运行openbox等组件)、particlede.desktop(会话描述文件)。
function install_system_session_files() {
    echo "[7/8] 安装系统级会话文件..."
    sudo cp scripts/particlede-session /usr/local/bin/
    sudo chmod +x /usr/local/bin/particlede-session
    sudo cp config/particlede.desktop /usr/share/xsessions/
}

# 函数：显示用户提示
# 目的：提供安装完成后的使用指南，帮助用户快速上手ParticleDE。
function show_user_tips() {
    echo "[8/8] 显示用户提示..."
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
install_chinese_support
install_themes_and_appearance
copy_user_configs
configure_themes_and_appearance
configure_chinese_environment
install_system_session_files
show_user_tips

echo "脚本执行完毕。如有问题，请检查日志或重新运行。"