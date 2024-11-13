#!/bin/bash

source scripts/utils.sh

run_script() {
    local script_name="$1"
    local description="$2"

    echo -e "\n"
    read -p "Do you want to run $description? (y/n): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if bash "$SCRIPT_DIR/$script_name"; then
            color_echo green "$description completed successfully"
        else
            color_echo red "$description failed with exit code. Continuing..."
        fi
    else
        color_echo blue "Skipping $description"
    fi
}

run_script "submodule.sh" "Submodule initialization"
run_script "system-package.sh" "System packages installation"
run_script "venv.sh" "Virtual environment setup"
run_script "var_env.sh" "Environment variables configuration"
# run_script "redis.sh" "Redis installation and setup"
run_script "django.sh" "Django configuration"
# run_script "webpack.sh" "Webpack setup"

echo_title "SUCCESSFUL INSTALL"
