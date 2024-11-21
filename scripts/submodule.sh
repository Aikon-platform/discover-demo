#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR/utils.sh"

if ! command -v git &> /dev/null; then
    color_echo "red" "Git is not installed. Please install git."
    exit 1
fi

echo_title "DOWNLOADING API SUBMODULE"
if ! (git submodule init && git submodule update); then
    # If failed, remove api directory and clone it
    rm -rf "$API_DIR"
    git clone https://github.com/Aikon-platform/discover-api.git "$API_DIR"
else
    echo_title "UPDATING API SUB-SUBMODULES"
    cd "$API_DIR" && git submodule init && git submodule update && cd "$ROOT_DIR"
fi
