# Particle-Desktop-Environment

这是一个基于X11，集成Openbox, tint2, rofi等组件的轻量级桌面环境开源项目。

## 快速启动

运行安装脚本

```bash
./scripts/setup_env.sh
```

在安装lightdm时选择lightdm为default display manager

重启或登出，点击登录界面的右下角齿轮图标，选择ParticleDE并登录

## 语言切换

ParticleDE 支持中英文界面切换：

```bash
# 切换到中文
./scripts/switch_language.sh zh_CN

# 切换到英文
./scripts/switch_language.sh en_US

# 查看支持的语言
./scripts/switch_language.sh list

# 显示帮助
./scripts/switch_language.sh --help
```

语言切换会立即生效，并保存到用户配置中。下次登录时会自动应用上次选择的语言。

## 配置部署

ParticleDE 使用统一的配置部署系统确保配置文件正确应用：

```bash
# 手动部署所有配置
./scripts/copy_configs.sh

# 查看配置部署帮助
./scripts/copy_configs.sh --help
```

详细说明请参考 [CONFIG_DEPLOYMENT.md](CONFIG_DEPLOYMENT.md)。
