#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR/utils.sh"

echo_title "SETUP WEBPACK"

setup_npm() {
    if ! command -v npm &> /dev/null; then
        color_echo yellow "\nInstalling NPM and Node..."
        if [[ "$OS" == "Linux" ]]; then
            sudo apt-get install -y npm
        elif [[ "$OS" == "Mac" ]]; then
            brew install npm
        elif [[ "$OS" == "Windows" ]]; then
            winget install -e --id OpenJS.NodeJS
        fi
    fi
}

setup_node() {
    if ! command -v nvm &> /dev/null; then
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        \. "$NVM_DIR/nvm.sh"
        # [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
        # [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
    fi
    nvm install node
}

setup_webpack() {
    cd "$FRONT_DIR"/webpack || exit 1
    npm install
    npm run production
}

# setup_npm
# setup_node
# setup_webpack
