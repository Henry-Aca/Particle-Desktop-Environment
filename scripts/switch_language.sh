#!/bin/bash

################################################################################
# Particle Desktop Environment - Language Switcher
# 
# Usage:
#   switch_language.sh [LANGUAGE]  - Switch to specified language
#   switch_language.sh list        - List supported languages
#   switch_language.sh --help      - Show this help message
#
# Supported Languages: zh_CN (中文), en_US (English)
#
# This script:
#   1. Immediately updates current session environment variables
#   2. Saves language choice to ~/.config/particlede/language.conf
#   3. Generates localized menu.xml and rofi config
#   4. Manages input method (fcitx5) activation/deactivation
#
# Authors: Zhao Hengyi (zhao_84@tju.edu.cn)
# License: See LICENSE file in project root
################################################################################

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="${PROJECT_ROOT}/config"
GLOBAL_LANG_CONF="${CONFIG_DIR}/particlede/language.conf"
USER_CONFIG_DIR="${HOME}/.config/particlede"
USER_LANG_CONF="${USER_CONFIG_DIR}/language.conf"

# ============================================================================
# LOAD GLOBAL CONFIGURATION
# ============================================================================

# Load language configuration at script startup (for commands that need it)
if [[ -f "$GLOBAL_LANG_CONF" ]]; then
    source "$GLOBAL_LANG_CONF"
fi

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

# Load language configuration from global config file
load_language_config() {
    if [[ ! -f "$GLOBAL_LANG_CONF" ]]; then
        log_error "Language configuration file not found: $GLOBAL_LANG_CONF"
        return 1
    fi
    
    # Re-source the global language configuration (in case it was modified)
    source "$GLOBAL_LANG_CONF"
}

# Check if a language is supported
is_supported() {
    local lang="$1"
    for supported in "${SUPPORTED_LANGUAGES[@]}"; do
        if [[ "$lang" == "$supported" ]]; then
            return 0
        fi
    done
    return 1
}

# Show help message
show_help() {
    cat << 'HELP'
Usage: switch_language.sh [COMMAND|LANGUAGE]

COMMANDS:
  list              List all supported languages
  --help, -h        Show this help message

LANGUAGES:
  zh_CN             Simplified Chinese (简体中文)
  en_US             English (United States)

EXAMPLES:
  switch_language.sh zh_CN        Switch to Simplified Chinese
  switch_language.sh en_US        Switch to English
  switch_language.sh list         Show all supported languages
  switch_language.sh --help       Show this help message

FEATURES:
  • Immediately updates current session environment
  • Saves preference to ~/.config/particlede/language.conf
  • Generates localized UI configuration files
  • Manages input method (fcitx5) settings

EXTENDING TO NEW LANGUAGES:
  Edit config/particlede/language.conf to:
  1. Add language code to SUPPORTED_LANGUAGES array
  2. Add LOCALE_MAP entry for language code
  3. Add UI_TEXT_* entries for all menu items
  4. Add INPUT_METHOD_FOR_LANGUAGE entry

EXAMPLES FOR FUTURE LANGUAGES:
  - zh_TW (Traditional Chinese - Taiwan)
  - ja_JP (Japanese)
  - fr_FR (French)
  - de_DE (German)
HELP
}

# List all supported languages
list_languages() {
    log_info "Supported languages:"
    echo ""
    for lang in "${SUPPORTED_LANGUAGES[@]}"; do
        local name="${LANGUAGE_NAMES[$lang]}"
        printf "  %-10s %s\n" "$lang" "$name"
    done
    echo ""
}

# Get locale string for a language
get_locale() {
    local lang="$1"
    echo "${LOCALE_MAP[$lang]}"
}

# Get input method for a language  
get_input_method() {
    local lang="$1"
    echo "${INPUT_METHOD_FOR_LANGUAGE[$lang]}"
}

# Generate Openbox menu.xml with localized text
generate_openbox_menu() {
    local lang="$1"
    local source_menu="${CONFIG_DIR}/openbox/menu.xml.template"
    local target_menu="${CONFIG_DIR}/openbox/menu.xml"
    
    if [[ ! -f "$source_menu" ]]; then
        log_error "Openbox menu template not found: $source_menu"
        return 1
    fi
    
    log_info "Generating localized Openbox menu for language: $lang"
    
    local launcher_text="${UI_TEXT_LAUNCHER[$lang]}"
    local filemgr_text="${UI_TEXT_FILE_MANAGER[$lang]}"
    local terminal_text="${UI_TEXT_TERMINAL[$lang]}"
    local restart_text="${UI_TEXT_RESTART_OPENBOX[$lang]}"
    local logout_text="${UI_TEXT_LOGOUT[$lang]}"
    
    # Use sed to replace placeholders in template
    sed -e "s|{{LAUNCHER}}|${launcher_text}|g" \
        -e "s|{{FILE_MANAGER}}|${filemgr_text}|g" \
        -e "s|{{TERMINAL}}|${terminal_text}|g" \
        -e "s|{{RESTART_OPENBOX}}|${restart_text}|g" \
        -e "s|{{LOGOUT}}|${logout_text}|g" \
        "$source_menu" > "$target_menu"
    
    log_success "Openbox menu generated: $target_menu"
}

# Generate Rofi config.rasi with localized text
generate_rofi_config() {
    local lang="$1"
    local source_config="${CONFIG_DIR}/rofi/config.rasi.template"
    local target_config="${CONFIG_DIR}/rofi/config.rasi"
    
    if [[ ! -f "$source_config" ]]; then
        log_error "Rofi config template not found: $source_config"
        return 1
    fi
    
    log_info "Generating localized Rofi config for language: $lang"
    
    local drun_text="${UI_TEXT_ROFI_DRUN[$lang]}"
    local run_text="${UI_TEXT_ROFI_RUN[$lang]}"
    local file_text="${UI_TEXT_ROFI_FILEBROWSER[$lang]}"
    local window_text="${UI_TEXT_ROFI_WINDOW[$lang]}"
    local search_text="${UI_TEXT_ROFI_SEARCH[$lang]}"
    
    # Use sed to replace placeholders in template
    sed -e "s|{{ROFI_DRUN}}|${drun_text}|g" \
        -e "s|{{ROFI_RUN}}|${run_text}|g" \
        -e "s|{{ROFI_FILE}}|${file_text}|g" \
        -e "s|{{ROFI_WINDOW}}|${window_text}|g" \
        -e "s|{{ROFI_SEARCH}}|${search_text}|g" \
        "$source_config" > "$target_config"
    
    log_success "Rofi config generated: $target_config"
}

# Generate Rofi powermenu.sh with localized text
generate_powermenu() {
    local lang="$1"
    local source_menu="${CONFIG_DIR}/rofi/powermenu.sh.template"
    local target_menu="${CONFIG_DIR}/rofi/powermenu.sh"
    
    if [[ ! -f "$source_menu" ]]; then
        log_error "Powermenu template not found: $source_menu"
        return 1
    fi
    
    log_info "Generating localized powermenu for language: $lang"
    
    local uptime_text="${UI_TEXT_POWER_UPTIME[$lang]}"
    local lock_text="${UI_TEXT_POWER_LOCK[$lang]}"
    local logout_text="${UI_TEXT_POWER_LOGOUT[$lang]}"
    local suspend_text="${UI_TEXT_POWER_SUSPEND[$lang]}"
    local reboot_text="${UI_TEXT_POWER_REBOOT[$lang]}"
    local shutdown_text="${UI_TEXT_POWER_SHUTDOWN[$lang]}"
    
    # Use sed to replace placeholders in template
    sed -e "s|{{UPTIME}}|${uptime_text}|g" \
        -e "s|{{LOCK}}|${lock_text}|g" \
        -e "s|{{LOGOUT}}|${logout_text}|g" \
        -e "s|{{SUSPEND}}|${suspend_text}|g" \
        -e "s|{{REBOOT}}|${reboot_text}|g" \
        -e "s|{{SHUTDOWN}}|${shutdown_text}|g" \
        "$source_menu" > "$target_menu"
    
    # Make it executable
    chmod +x "$target_menu"
    
    log_success "Powermenu generated: $target_menu"
}

# Generate Openbox rc.xml with localized desktop names
generate_openbox_desktop_names() {
    local lang="$1"
    local source_rc="${CONFIG_DIR}/openbox/rc.xml.template"
    local target_rc="${CONFIG_DIR}/openbox/rc.xml"
    
    if [[ ! -f "$source_rc" ]]; then
        log_error "Openbox rc.xml.template not found: $source_rc"
        return 1
    fi
    
    log_info "Generating localized Openbox rc.xml with desktop names for language: $lang"
    
    local desktop1_text="${UI_TEXT_DESKTOP1[$lang]}"
    local desktop2_text="${UI_TEXT_DESKTOP2[$lang]}"
    local desktop3_text="${UI_TEXT_DESKTOP3[$lang]}"
    local desktop4_text="${UI_TEXT_DESKTOP4[$lang]}"
    
    # Use sed to replace placeholders in template
    sed -e "s|{{DESKTOP1}}|${desktop1_text}|g" \
        -e "s|{{DESKTOP2}}|${desktop2_text}|g" \
        -e "s|{{DESKTOP3}}|${desktop3_text}|g" \
        -e "s|{{DESKTOP4}}|${desktop4_text}|g" \
        "$source_rc" > "$target_rc"
    
    log_success "Openbox rc.xml generated: $target_rc"
}

# Configure input method based on language
configure_input_method() {
    local lang="$1"
    local input_method=$(get_input_method "$lang")
    
    log_info "Configuring input method for language: $lang"
    
    case "$input_method" in
        fcitx5)
            log_info "Activating fcitx5 input method"
            
            # Check if fcitx5 is running
            if ! pgrep -x "fcitx5" > /dev/null 2>&1; then
                log_info "Starting fcitx5..."
                fcitx5 -d 2>/dev/null || log_error "Failed to start fcitx5"
            fi
            
            # Enable fcitx5 input method
            if command -v fcitx5-remote &> /dev/null; then
                fcitx5-remote -r 2>/dev/null || true
            fi
            
            log_success "fcitx5 input method enabled"
            ;;
        none)
            log_info "Disabling input method for English"
            
            # Disable fcitx5 if running
            if command -v fcitx5-remote &> /dev/null; then
                fcitx5-remote -d 2>/dev/null || true
            fi
            
            log_success "Input method disabled"
            ;;
        *)
            log_error "Unknown input method: $input_method"
            return 1
            ;;
    esac
}

# Update project language.conf and save to user config
update_language_config() {
    local lang="$1"

    log_info "Updating project language configuration: ${CONFIG_DIR}/particlede/language.conf"

    if [[ ! -f "${CONFIG_DIR}/particlede/language.conf" ]]; then
        log_error "Project language configuration not found: ${CONFIG_DIR}/particlede/language.conf"
        return 1
    fi

    sed -i "s/^ACTIVE_LANGUAGE=.*/ACTIVE_LANGUAGE=\"${lang}\"/" "${CONFIG_DIR}/particlede/language.conf"

    log_success "Project language configuration updated: $lang"
}

# Save language choice to user config directory
save_user_config() {
    local lang="$1"
    
    log_info "Saving language preference to: $USER_LANG_CONF"
    
    # Create user config directory if it doesn't exist
    mkdir -p "$USER_CONFIG_DIR"
    
    # Create user language configuration file - only save ACTIVE_LANGUAGE
    cat > "$USER_LANG_CONF" << USER_CONF_EOF
# User language configuration for Particle Desktop Environment
# This file is auto-generated by switch_language.sh
# Do not edit manually (changes will be overwritten)

# Active language preference
ACTIVE_LANGUAGE="$lang"
USER_CONF_EOF
    
    log_success "User language preference saved: $lang"
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

main() {
    # Parse command line arguments
    if [[ $# -eq 0 ]]; then
        log_error "No command or language specified"
        echo ""
        show_help
        return 1
    fi
    
    local command="$1"
    
    # Handle special commands that don't require config loading
    case "$command" in
        --help|-h)
            show_help
            return 0
            ;;
        list)
            list_languages
            return 0
            ;;
    esac
    
    # Check if the specified language is supported
    if ! is_supported "$command"; then
        log_error "Unsupported language: $command"
        echo ""
        list_languages
        return 1
    fi
    
    local target_lang="$command"
    
    # Execute language switching steps
    log_info "Starting language switch to: $target_lang"
    echo ""

    # 1. Update project language.conf first
    if ! update_language_config "$target_lang"; then
        log_error "Failed to update project language configuration"
        return 1
    fi

    # 2. Generate localized configuration files
    if ! generate_openbox_menu "$target_lang"; then
        log_error "Failed to generate Openbox menu"
        return 1
    fi
    
    if ! generate_openbox_desktop_names "$target_lang"; then
        log_error "Failed to generate Openbox desktop names"
        return 1
    fi
    
    if ! generate_rofi_config "$target_lang"; then
        log_error "Failed to generate Rofi config"
        return 1
    fi

    if ! generate_powermenu "$target_lang"; then
        log_error "Failed to generate powermenu"
        return 1
    fi

    # 3. Deploy configurations to user directories (excluding language.conf to avoid overwriting user setting)
    if ! "${SCRIPT_DIR}/copy_configs.sh" --skip-language; then
        log_error "Failed to deploy configurations"
        return 1
    fi
    
    # Now save user language config (after copy_configs, so it won't be overwritten)
    if ! save_user_config "$target_lang"; then
        log_error "Failed to save user language config"
        return 1
    fi

    # 4. Configure input method
    if ! configure_input_method "$target_lang"; then
        log_error "Failed to configure input method"
        return 1
    fi
    
    echo ""
    log_success "Language successfully switched to: $target_lang"
    echo ""
    log_info "New locale: $(get_locale "$target_lang")"
    log_info "Changes will take effect on next login or after restarting the session."
    
    return 0
}

# Run main function
main "$@"
