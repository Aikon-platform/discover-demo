#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
API_DIR="$ROOT_DIR/api"
FRONT_DIR="$ROOT_DIR/front"

get_os() {
    unameOut="$(uname -s)"
    case "${unameOut}" in
        Linux*)     os=Linux;;
        Darwin*)    os=Mac;;
        CYGWIN*)    os=Windows;;
        MINGW*)     os=Windows;;
        MSYS_NT*)   os=Git;;
        *)          os="UNKNOWN:${unameOut}"
    esac
    echo "${os}"
}

OS=$(get_os)

color_echo() {
    Color_Off="\033[0m"
    Red="\033[1;91m"
    Green="\033[1;92m"
    Yellow="\033[1;93m"
    Blue="\033[1;94m"
    Purple="\033[1;95m"
    Cyan="\033[1;96m"

    case "$1" in
        "green") echo -e "$Green$2$Color_Off";;
        "red") echo -e "$Red$2$Color_Off";;
        "blue") echo -e "$Blue$2$Color_Off";;
        "yellow") echo -e "$Yellow$2$Color_Off";;
        "purple") echo -e "$Purple$2$Color_Off";;
        "cyan") echo -e "$Cyan$2$Color_Off";;
        *) echo "$2";;
    esac
}

echo_title(){
    sep_line="========================================"
    len_title=${#1}

    if [ "$len_title" -gt 40 ]; then
        sep_line=$(printf "%0.s=" $(seq 1 $len_title))
        title="$1"
    else
        diff=$((38 - len_title))
        half_diff=$((diff / 2))
        sep=$(printf "%0.s=" $(seq 1 $half_diff))

        if [ $((diff % 2)) -ne 0 ]; then
            title="$sep $1 $sep="
        else
            title="$sep $1 $sep"
        fi
    fi

    color_echo purple "\n\n$sep_line\n$title\n$sep_line"
}

generate_random_string() {
    echo "$(openssl rand -base64 32 | tr -d '/\n')"
}

prompt_user() {
    env_var=$(color_echo 'red' "$1")
    default_val="$2"
    current_val="$3"
    desc="$4"

    if [ "$2" != "$3" ]; then
        default="Press enter for $(color_echo 'cyan' "$default_val")"
    elif [ -n "$current_val" ]; then
        default="Press enter to keep $(color_echo 'cyan' "$current_val")"
        default_val=$current_val
    fi

    read -p "$env_var $desc"$'\n'"$default: " value
    echo "${value:-$default_val}"
}
