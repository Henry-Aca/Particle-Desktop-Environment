# Particle-Desktop-Environment

这是一个基于X11，集成Openbox, tint2, rofi等组件的轻量级桌面环境开源项目。

## 快速启动

运行安装脚本

```bash
./scripts/setup_env.sh
```

在安装lightdm时选择lightdm为default display manager

重启或登出，点击登录界面的右下角齿轮图标，选择ParticleDE并登录

## 功能检验


检查 tint2 任务栏（应有底部任务栏）、PCManFM 桌面图标是否正常（应有桌面图标）

<img width="1920" height="930" alt="ef5a62aed436a359cb032a3109f0faaf" src="https://github.com/user-attachments/assets/bc7e7028-b783-4f04-a375-75c1a073de48" />


最下端右键选择终端打开

终端运行rofi -show window  检验rofi

<img width="1920" height="930" alt="4e0ecce5861e473ea262006229be632b" src="https://github.com/user-attachments/assets/01bc0a5a-27aa-4638-8ecb-abef04c2ebe6" />
