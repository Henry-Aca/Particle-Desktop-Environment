#!/bin/bash
# ParticleDE 环境设置脚本

set -e # 遇到错误就退出

echo "[1] 安装必要的软件包..."
sudo apt update
sudo apt install -y openbox tint2 rofi pcmanfm conky-all \
x11-xserver-utils xinit x11-utils 
# 中文环境相关包
sudo apt install -y fonts-noto-cjk fonts-noto-cjk-extra fonts-wqy-microhei fonts-wqy-zenhei \
fcitx5 fcitx5-chinese-addons fcitx5-frontend-gtk3 fcitx5-frontend-gtk2 fcitx5-frontend-qt5
# Qt主题支持
sudo apt install -y qt5-style-plugins qt5ct

echo "[2] 复制配置文件到用户目录..."
# 创建配置目录
mkdir -p ~/.config/openbox ~/.config/tint2 ~/.config/rofi ~/.config/pcmanfm/default

# 复制Openbox配置
cp -r config/openbox/* ~/.config/openbox/ 2>/dev/null || true
# 复制tint2配置
cp -r config/tint2/* ~/.config/tint2/ 2>/dev/null || true
# 复制rofi配置
cp -r config/rofi/* ~/.config/rofi/ 2>/dev/null || true
# 复制PCManFM配置
cp -r config/pcmanfm/* ~/.config/pcmanfm/ 2>/dev/null || true

echo "[3] 配置主题..."
# 设置GTK主题
gsettings set org.gnome.desktop.interface gtk-theme "Arc"
gsettings set org.gnome.desktop.interface icon-theme "Papyrus"

# 设置Openbox主题
mkdir -p ~/.themes
cp -r themes/* ~/.themes/ 2>/dev/null || true


# 设置图标主题
mkdir -p ~/.icons
# 从本地图标目录复制（如果存在）
if [ -d "icons/Papyrus" ]; then
    cp -r icons/Papyrus ~/.icons/
    cp -r icons/Papyrus-Dark ~/.icons/ 2>/dev/null || true
elif [ -d "icons/Numix" ]; then
    cp -r icons/Numix ~/.icons/
    cp -r icons/Numix-Light ~/.icons/ 2>/dev/null || true
fi

# 配置字体
gsettings set org.gnome.desktop.interface font-name "Noto Sans 11"
gsettings set org.gnome.desktop.interface document-font-name "Noto Sans 11"
gsettings set org.gnome.desktop.interface monospace-font-name "Noto Mono 11"

echo "[4] 配置中文环境..."
# 复制xprofile配置文件
cp config/xprofile ~/.xprofile

# 给文件添加执行权限
chmod +x ~/.xprofile

# 配置Qt主题
mkdir -p ~/.config/qt5ct
# 复制qt5ct配置文件
cp config/qt5ct/qt5ct.conf ~/.config/qt5ct/

echo "[5] 安装桌面会话文件..."
# 复制会话启动脚本到系统目录
sudo cp scripts/particlede-session /usr/local/bin/
sudo chmod +x /usr/local/bin/particlede-session
# 复制桌面入口文件
sudo cp config/particlede.desktop /usr/share/xsessions/

echo "[6] 配置虚拟桌面..."
# 确保Openbox配置文件中有4个虚拟桌面和正确的快捷键绑定
# 配置已在rc.xml中设置

echo "[7] 提示用户..."
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
