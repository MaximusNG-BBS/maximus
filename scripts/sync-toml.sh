#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
#
# sync-toml.sh - Sync TOML configs between build/ and resources/install_tree/
#
# Copyright (C) 2025 Kevin Morgan (Limping Ninja)
# https://github.com/LimpingNinja
#
# Default workflow: resources/config is source of truth
#   - resources/config → build/config AND resources/install_tree/config
#
# Reverse workflow: build is source of truth (backpropagation)
#   - build/config → resources/config AND resources/install_tree/config
#
# Usage:
#   scripts/sync-toml.sh              # resources/config → (build + install_tree)
#   scripts/sync-toml.sh --reverse    # build/config → (resources/config + install_tree)
#   scripts/sync-toml.sh --diff       # show differences only
#

set -euo pipefail

# ── Resolve project root ─────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RESOURCES_CONFIG="$PROJECT_ROOT/resources/config"
BUILD_CONFIG="$PROJECT_ROOT/build/config"
TREE_CONFIG="$PROJECT_ROOT/resources/install_tree/config"
BUILD_BIN="$PROJECT_ROOT/build/bin"
TREE_BIN="$PROJECT_ROOT/resources/install_tree/bin"

# ── Colors ────────────────────────────────────────────────────────────────────
CYAN='\033[0;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
WHITE='\033[1;37m'
NC='\033[0m'

log_ok()   { echo -e "  ${GREEN}[SYNC]${NC}  $1"; }
log_new()  { echo -e "  ${CYAN}[ NEW]${NC}  $1"; }
log_skip() { echo -e "  ${YELLOW}[SKIP]${NC}  $1"; }
log_diff() { echo -e "  ${RED}[DIFF]${NC}  $1"; }

# ── Mode parsing ─────────────────────────────────────────────────────────────
MODE="forward"   # resources/config → build + install_tree
while [ $# -gt 0 ]; do
    case "$1" in
        --reverse|-r)  MODE="reverse"; shift ;;
        --diff|-d)     MODE="diff"; shift ;;
        --help|-h)
            echo "Usage: $(basename "$0") [--reverse | --diff | --help]"
            echo ""
            echo "  (default)    Sync resources/config → (build/config + install_tree/config)"
            echo "  --reverse    Sync build/config → (resources/config + install_tree/config)"
            echo "  --diff       Show differences only, no changes"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option:${NC} $1"
            exit 1
            ;;
    esac
done

# ── Set source/dest based on mode ────────────────────────────────────────────
if [ "$MODE" = "reverse" ]; then
    SRC_CONFIG="$BUILD_CONFIG"
    DST1_CONFIG="$RESOURCES_CONFIG"
    DST2_CONFIG="$TREE_CONFIG"
    SRC_BIN="$BUILD_BIN"
    DST_BIN="$TREE_BIN"
    echo -e "${WHITE}Reverse sync: build → (resources/config + install_tree)${NC}"
else
    SRC_CONFIG="$RESOURCES_CONFIG"
    DST1_CONFIG="$BUILD_CONFIG"
    DST2_CONFIG="$TREE_CONFIG"
    SRC_BIN="$BUILD_BIN"  # install.sh only syncs in reverse mode
    DST_BIN="$TREE_BIN"
    echo -e "${WHITE}Default sync: resources/config → (build + install_tree)${NC}"
fi
echo ""

# ── Files that must never overwrite the resources root copy ─────────────────
# english.toml is the post-conversion output; it is generated from the .mad
# conversion + delta_english.toml overlay, so backpropagating it would lose
# the mechanical base.  Add other filenames here as needed.
NEVER_REVERSE_TO_RESOURCES=(
    "lang/english.toml"
)

# ── Deploy-path fixup ────────────────────────────────────────────────────────
# maximus.toml in resources/install_tree must keep sys_path = "/var/max"
# regardless of what the build copy says.  After copying, sed-replace it.
DEPLOY_SYS_PATH="/var/max"

fixup_sys_path() {
    local file="$1"
    if [ -f "$file" ]; then
        sed -i 's|^sys_path = .*|sys_path = "'"$DEPLOY_SYS_PATH"'"|' "$file"
    fi
}

# ── Sync TOML files ──────────────────────────────────────────────────────────
synced=0
created=0
unchanged=0
skipped=0
diffcount=0

sync_file() {
    local src="$1"
    local dst="$2"
    local rel="$3"

    if [ ! -f "$dst" ]; then
        cp "$src" "$dst"
        log_new "$rel"
        created=$((created + 1))
    elif ! cmp -s "$src" "$dst"; then
        cp "$src" "$dst"
        log_ok "$rel"
        synced=$((synced + 1))
    else
        unchanged=$((unchanged + 1))
    fi
}

while IFS= read -r -d '' src_file; do
    rel="${src_file#"$SRC_CONFIG"/}"
    dst1_file="$DST1_CONFIG/$rel"
    dst2_file="$DST2_CONFIG/$rel"

    if [ "$MODE" = "diff" ]; then
        for dst in "$dst1_file" "$dst2_file"; do
            if [ ! -f "$dst" ]; then
                log_new "$rel (only in source)"
                diffcount=$((diffcount + 1))
                break
            elif ! cmp -s "$src_file" "$dst"; then
                log_diff "$rel → ${dst#$PROJECT_ROOT/}"
                diff --color=auto -u "$dst" "$src_file" | head -20
                echo ""
                diffcount=$((diffcount + 1))
            fi
        done
        continue
    fi

    # Ensure destination directories exist
    for dst in "$dst1_file" "$dst2_file"; do
        dst_dir="$(dirname "$dst")"
        [ -d "$dst_dir" ] || mkdir -p "$dst_dir"
    done

    # In reverse mode, skip files that must not overwrite resources root
    skip_dst1=false
    if [ "$MODE" = "reverse" ]; then
        for skip in "${NEVER_REVERSE_TO_RESOURCES[@]}"; do
            if [ "$rel" = "$skip" ]; then
                skip_dst1=true
                log_skip "$rel (never reverse to resources root)"
                skipped=$((skipped + 1))
                break
            fi
        done
    fi

    # Sync to both destinations
    if [ "$skip_dst1" = false ]; then
        sync_file "$src_file" "$dst1_file" "$rel → build"
    fi
    sync_file "$src_file" "$dst2_file" "$rel → install_tree"

    # Fix sys_path in maximus.toml when written to resources or install_tree
    if [ "$(basename "$rel")" = "maximus.toml" ]; then
        [ "$skip_dst1" = false ] && [ "$DST1_CONFIG" != "$BUILD_CONFIG" ] && fixup_sys_path "$dst1_file"
        [ "$DST2_CONFIG" != "$BUILD_CONFIG" ] && fixup_sys_path "$dst2_file"
    fi
done < <(find "$SRC_CONFIG" -type f -name '*.toml' -print0 | sort -z)

# ── Sync install.sh (only in reverse mode) ──────────────────────────────────
if [ "$MODE" = "reverse" ] && [ -f "$SRC_BIN/install.sh" ]; then
    dst_install="$DST_BIN/install.sh"
    [ -d "$DST_BIN" ] || mkdir -p "$DST_BIN"

    if [ "$MODE" = "diff" ]; then
        if [ ! -f "$dst_install" ]; then
            log_new "bin/install.sh (only in source)"
            diffcount=$((diffcount + 1))
        elif ! cmp -s "$SRC_BIN/install.sh" "$dst_install"; then
            log_diff "bin/install.sh"
            diffcount=$((diffcount + 1))
        fi
    else
        if [ ! -f "$dst_install" ]; then
            cp "$SRC_BIN/install.sh" "$dst_install"
            log_new "bin/install.sh"
            created=$((created + 1))
        elif ! cmp -s "$SRC_BIN/install.sh" "$dst_install"; then
            cp "$SRC_BIN/install.sh" "$dst_install"
            log_ok "bin/install.sh"
            synced=$((synced + 1))
        else
            unchanged=$((unchanged + 1))
        fi
    fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
if [ "$MODE" = "diff" ]; then
    if [ "$diffcount" -eq 0 ]; then
        echo -e "${GREEN}All files in sync.${NC}"
    else
        echo -e "${YELLOW}$diffcount file(s) differ.${NC}"
    fi
else
    echo -e "${WHITE}Done:${NC} $synced updated, $created new, $skipped skipped, $unchanged unchanged"
fi
