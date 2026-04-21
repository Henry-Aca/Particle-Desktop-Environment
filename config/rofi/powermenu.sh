#!/bin/bash
# Rofi Power Menu Script - Particle Desktop Environment
# 由 switch_language.sh 自动生成，请勿手动编辑

# 主程序
main() {
    local options="{{POWER_LOCK}}\n{{POWER_LOGOUT}}\n{{POWER_SUSPEND}}\n{{POWER_REBOOT}}\n{{POWER_SHUTDOWN}}"
    
    # 显示 Rofi 菜单并获取选择
    local selected=$(echo -e "$options" | rofi -dmenu -p "电源" -location 3 -xoffset 10 -yoffset -50)
    
    # 执行相应操作
    case "$selected" in
        "锁定")
            if command -v slock &> /dev/null; then
                slock
            elif command -v xtrlock &> /dev/null; then
                xtrlock
            fi
            ;;
        "注销")
            openbox --exit
            ;;
        "挂起")
            systemctl suspend
            ;;
        "重启") 
            systemctl reboot
            ;;
        "关机")
            systemctl poweroff
            ;;
    esac
}

main "$@"