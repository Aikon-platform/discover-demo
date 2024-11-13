#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR/utils.sh"

color_echo yellow "\nSystem packages..."

if [[ "$OS" == "Mac" ]]; then
    command -v brew &> /dev/null || {
        color_echo "yellow" "Installing brew"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    }
elif [[ "$OS" == "Windows" ]]; then
    command -v winget &> /dev/null || {
        color_echo "red" "Winget is required to install system package" >&2;
        exit 1;
    }
fi

if ! command -v python3 &> /dev/null; then
    color_echo "red" "Python is not installed. Please install python3.10 python3.10-venv python3.10-dev"
    exit 1
fi
if ! command -v python3.10 &> /dev/null; then
    color_echo "red" "Python 3.10 is not installed. Please install python3.10 python3.10-venv python3.10-dev"
    exit 1
fi

if [[ "$OS" == "Linux" ]]; then
    : # Placeholder
    # sudo apt install software-properties-common
    # sudo add-apt-repository ppa:deadsnakes/ppa
    # sudo apt-get update && sudo apt-get install -y python3.10 python3.10-venv python3.10-dev
elif [[ "$OS" == "Mac" ]]; then
    : # Placeholder
    # brew install python@3.10
elif [[ "$OS" == "Windows" ]]; then
    : # Placeholder
    # winget install -e --id Python.Python.3.10
    # pip3 install virtualenv
fi

if [[ "$OS" == "Linux" ]]; then
    sudo apt-get update && sudo apt-get install -y redis-server curl
elif [[ "$OS" == "Mac" ]]; then
    brew install redis curl
elif [[ "$OS" == "Windows" ]]; then
    winget install -e --id Redis.Redis cURL.cURL
fi
