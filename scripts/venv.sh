#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR/utils.sh"

API_VENV="$API_DIR/venv/$([[ "$OS" == "Windows" ]] && echo "Scripts" || echo "bin")"
FRONT_VENV="$FRONT_DIR/venv/$([[ "$OS" == "Windows" ]] && echo "Scripts" || echo "bin")"

color_echo  "SET UP VIRTUAL ENVIRONMENTS"
python3 -m venv "$API_DIR"/venv
python3 -m venv "$FRONT_DIR"/venv

for venv in "$API_VENV" "$FRONT_VENV"; do
    "$venv"/pip install --upgrade pip
    "$venv"/pip install -r "${venv%/*/*/*}"/requirements.txt
done
"$API_VENV"/pip install python-dotenv

# TODO test connexion to CUDA
