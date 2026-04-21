#!/bin/bash

################################################################################
# Particle Desktop Environment - Configuration Deployer
#
# Usage:
#   copy_configs.sh          - Copy all configs from project to user directories
#   copy_configs.sh --help   - Show this help message
#
# This script copies configuration files from the project directory to user
# configuration directories. It ensures that generated localized configs
# are properly deployed to the locations where applications read them.
#
# Authors: Zhao Hengyi (zhao_84@tju.edu.cn)
# License: See LICENSE file in project root
################################################################################

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="${PROJECT_ROOT}/config"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

log_info() {
    echo "[INFO] $*" >&2
}

log_error() {
    echo "[ERROR] $*" >&2
}

log_success() {
    echo "[SUCCESS] $*" >&2
}

# Show help message
show_help() {
    cat << 'HELP'
Usage: copy_configs.sh [OPTIONS]

OPTIONS:
  --help, -h        Show this help message

DESCRIPTION:
  This script copies configuration files from the project config/ directory
  to the user's ~/.config/ directory. 

  The script handles:
  • Openbox window manager configuration
  • Tint2 panel configuration
  • Rofi launcher configuration
  • PCManFM file manager configuration
  • GTK 2.0 and 3.0 theme configuration
  • Qt5ct theme configuration
  • ParticleDE language configuration

  This script is called by both setup_env.sh and switch_language.sh to
  ensure configurations are properly deployed after changes.

EXAMPLES:
  copy_configs.sh              Copy all configurations
  copy_configs.sh --help       Show this help message
HELP
}

# Copy Openbox configuration
copy_openbox_config() {
    log_info "Copying Openbox configuration..."
    mkdir -p ~/.config/openbox
    if [[ -f "${CONFIG_DIR}/openbox/menu.xml" ]]; then
        cp "${CONFIG_DIR}/openbox/menu.xml" ~/.config/openbox/
        log_success "Openbox menu.xml copied"
    else
        log_error "Openbox menu.xml not found in project config"
        return 1
    fi

    if [[ -f "${CONFIG_DIR}/openbox/rc.xml" ]]; then
        cp "${CONFIG_DIR}/openbox/rc.xml" ~/.config/openbox/
        log_success "Openbox rc.xml copied"
    else
        log_error "Openbox rc.xml not found in project config"
        return 1
    fi
}

# Copy Tint2 configuration
copy_tint2_config() {
    log_info "Copying Tint2 configuration..."
    mkdir -p ~/.config/tint2
    if [[ -f "${CONFIG_DIR}/tint2/tint2rc" ]]; then
        cp "${CONFIG_DIR}/tint2/tint2rc" ~/.config/tint2/
        log_success "Tint2 configuration copied"
    else
        log_error "Tint2 config not found in project config"
        return 1
    fi
}

# Copy Rofi configuration
copy_rofi_config() {
    log_info "Copying Rofi configuration..."
    mkdir -p ~/.config/rofi
    if [[ -f "${CONFIG_DIR}/rofi/config.rasi" ]]; then
        cp "${CONFIG_DIR}/rofi/config.rasi" ~/.config/rofi/
        log_success "Rofi config.rasi copied"
    else
        log_error "Rofi config.rasi not found in project config"
        return 1
    fi

    # Copy powermenu.sh with executable permissions
    if [[ -f "${CONFIG_DIR}/rofi/powermenu.sh" ]]; then
        cp "${CONFIG_DIR}/rofi/powermenu.sh" ~/.config/rofi/
        chmod +x ~/.config/rofi/powermenu.sh
        log_success "Rofi powermenu.sh copied with executable permissions"
    fi

    # Copy Rofi colors and themes if they exist
    if [[ -d "${CONFIG_DIR}/rofi/colors" ]]; then
        cp -r "${CONFIG_DIR}/rofi/colors" ~/.config/rofi/ 2>/dev/null || true
        log_success "Rofi colors copied"
    fi

    if [[ -d "${CONFIG_DIR}/rofi/shared" ]]; then
        cp -r "${CONFIG_DIR}/rofi/shared" ~/.config/rofi/ 2>/dev/null || true
        log_success "Rofi shared themes copied"
    fi
}

# Copy PCManFM configuration
copy_pcmanfm_config() {
    log_info "Copying PCManFM configuration..."
    mkdir -p ~/.config/pcmanfm/default
    if [[ -f "${CONFIG_DIR}/pcmanfm/default/pcmanfm.conf" ]]; then
        cp "${CONFIG_DIR}/pcmanfm/default/pcmanfm.conf" ~/.config/pcmanfm/default/
        log_success "PCManFM configuration copied"
    else
        log_error "PCManFM config not found in project config"
        return 1
    fi

    if [[ -f "${CONFIG_DIR}/pcmanfm/desktop-items-0.conf" ]]; then
        cp "${CONFIG_DIR}/pcmanfm/desktop-items-0.conf" ~/.config/pcmanfm/
        log_success "PCManFM desktop items config copied"
    fi
}

# Copy GTK configuration
# 不将 GTK 配置写入用户配置路径 ~/.config/，以避免影响其他会话
copy_gtk_config() {
    log_info "Copying GTK configuration..."
    mkdir -p ~/.config/particlede
    if [[ -f "${CONFIG_DIR}/particlede/gtkrc-2.0" ]]; then
        cp "${CONFIG_DIR}/particlede/gtkrc-2.0" ~/.config/particlede/
        log_success "GTK configuration copied"
    else
        log_error "GTK-2.0 config not found in project config"
        return 1
    fi

    if [[ -d "${CONFIG_DIR}/particlede/gtk-3.0" ]]; then
        mkdir -p ~/.config/particlede/gtk-3.0
        cp -r "${CONFIG_DIR}/particlede/gtk-3.0/"* ~/.config/particlede/gtk-3.0/ 2>/dev/null || true
        log_success "GTK 3.0 configuration copied"
    else
        log_error "GTK-3.0 config not found in project config"
        return 1
    fi
}

# Copy Qt5ct configuration
copy_qt5ct_config() {
    log_info "Copying Qt5ct configuration..."
    mkdir -p ~/.config/qt5ct
    if [[ -f "${CONFIG_DIR}/qt5ct/qt5ct.conf" ]]; then
        cp "${CONFIG_DIR}/qt5ct/qt5ct.conf" ~/.config/qt5ct/
        log_success "Qt5ct configuration copied"
    else
        log_error "Qt5ct config not found in project config"
        return 1
    fi
}

# Copy particlede language configuration
copy_language_config() {
    log_info "Copying ParticleDE language configuration..."
    mkdir -p ~/.config/particlede
    if [[ -f "${CONFIG_DIR}/particlede/language.conf" ]]; then
        cp "${CONFIG_DIR}/particlede/language.conf" ~/.config/particlede/
        log_success "ParticleDE language configuration copied"
    else
        log_error "ParticleDE language.conf not found in project config"
        return 1
    fi
}


# Copy all configurations
copy_all_configs() {
    local success=true

    if ! copy_openbox_config; then
        success=false
    fi

    if ! copy_tint2_config; then
        success=false
    fi

    if ! copy_rofi_config; then
        success=false
    fi

    if ! copy_pcmanfm_config; then
        success=false
    fi

    if ! copy_gtk_config; then
        success=false
    fi

    if ! copy_qt5ct_config; then
        success=false
    fi

    if ! copy_language_config; then
        success=false
    fi

    if [[ "$success" == true ]]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

main() {
    # Parse command line arguments
    case "${1:-}" in
        --help|-h)
            show_help
            return 0
            ;;
        "")
            # No arguments, proceed with copying
            ;;
        *)
            log_error "Unknown option: $1"
            echo ""
            show_help
            return 1
            ;;
    esac

    log_info "Starting configuration deployment..."
    echo ""

    if copy_all_configs; then
        log_success "All configurations deployed successfully"
        log_info "Configurations copied from: $CONFIG_DIR"
        log_info "Configurations deployed to: ~/.config/"
        return 0
    else
        log_error "Some configurations failed to deploy"
        return 1
    fi
}

# Run main function
main "$@"