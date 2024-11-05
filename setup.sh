#!/bin/bash
set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
API_DIR="$SCRIPT_DIR/api"
FRONT_DIR="$SCRIPT_DIR/front"

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

get_env_value() {
    param=$1
    env_file=$2
    value=$(awk -F= -v param="$param" '/^[^#]/ && $1 == param {gsub(/"/, "", $2); print $2}' "$env_file")
    echo "$value"
}

#SED_CMD="sed -i -e"
# SED_CMD=$(case $(get_os) in Linux) echo "sed -i" ;; Mac) echo "sed -i ''" ;; *) echo "Unsupported OS"; exit 1 ;; esac)

update_env() {
    env_file=$1
    IFS=$'\n' read -d '' -r -a lines < "$env_file"  # Read file into array
    for line in "${lines[@]}"; do
        if [[ $line =~ ^[^#]*= ]]; then
            param=$(echo "$line" | cut -d'=' -f1)
            current_val=$(get_env_value "$param" "$env_file")

            # Extract description from previous line if it exists
            desc=""
            if [[ $prev_line =~ ^# ]]; then
                desc=$(echo "$prev_line" | sed 's/^#\s*//')
            fi

            case $param in
                *PASSWORD*)
                    default_val="$(generate_random_string)"
                    ;;
                *SECRET*)
                    default_val="$(generate_random_string)"
                    ;;
                *)
                    default_val="$current_val"
                    ;;
            esac

            new_value=$(prompt_user "$param" "$default_val" "$current_val" "$desc")
            sed -i -e "s~^$param=.*~$param=\"$new_value\"~" "$env_file"
        fi
        prev_line="$line"
    done
}

copy_env_values() {
    source_env=$1
    target_env=$2

    IFS=$'\n' read -d '' -r -a lines < "$source_env"

    for line in "${lines[@]}"; do
        if [[ $line =~ ^[^#]*= ]]; then
            param=$(echo "$line" | cut -d'=' -f1)
            current_val=$(get_env_value "$param" "$target_env")
            default_val=$(echo "$line" | cut -d'=' -f2-)
            if [[ -n "$current_val" ]]; then
                sed -i -e "s~^$param=.*~$param=\"$default_val\"~" "$target_env"
            else
                echo "$param=\"$default_val\"" >> "$target_env"
            fi
        fi
    done
}

set_redis() {
    redis_psw="$1"
    REDIS_CONF=$(redis-cli INFO | grep config_file | awk -F: '{print $2}' | tr -d '[:space:]')
    color_echo yellow "\n\nModifying Redis configuration file $REDIS_CONF..."

    # use the same redis password for api and front
    sed -i '' -e "s~^REDIS_PASSWORD=.*~REDIS_PASSWORD=\"$redis_psw\"~" "$FRONT_ENV"

    sudo sed -i -e "s/\nrequirepass [^ ]*/requirepass $redis_psw/" "$REDIS_CONF"
    sudo sed -i -e "s/# requirepass [^ ]*/requirepass $redis_psw/" "$REDIS_CONF"

    case $OS in
        Linux)   sudo systemctl restart redis ;;
        Mac)     brew services restart redis ;;
        Windows) net start redis ;;
    esac
}

echo_title "DOWNLOADING API SUBMODULE"
if ! (git submodule init && git submodule update); then
    # If failed, remove api directory and clone it
    rm -rf api
    git clone https://github.com/Aikon-platform/discover-api.git api
else
    echo_title "UPDATING API SUB-SUBMODULES"
    cd api && git submodule init && git submodule update && cd ..
fi

echo_title "REQUIREMENTS INSTALL"
color_echo yellow "\nSystem packages..."

install_packages() {
    if [[ "$OS" == "Linux" ]]; then
        # sudo apt install software-properties-common
        # sudo add-apt-repository ppa:deadsnakes/ppa
        # sudo apt-get update && sudo apt-get install -y python3.10 python3.10-venv python3.10-dev
        # sudo apt-get install -y npm
        sudo apt-get update && sudo apt-get install -y redis-server curl
    elif [[ "$OS" == "Mac" ]]; then
        command -v brew &> /dev/null || {
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        }
        # brew install python@3.10
        # brew install npm
        brew install redis curl npm
    elif [[ "$OS" == "Windows" ]]; then
        command -v winget &> /dev/null || { echo "Winget required" >&2; exit 1; }
        # winget install -e --id Python.Python.3.10
        # winget install -e --id OpenJS.NodeJS
        winget install -e --id Redis.Redis cURL.cURL
        pip3 install virtualenv
    fi
}
install_packages

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

# test connexion to CUDA

echo_title "SET UP ENVIRONMENT VARIABLES"
API_ENV="$SCRIPT_DIR"/api/.env
API_DEV_ENV="$SCRIPT_DIR"/api/.env.dev
FRONT_ENV="$SCRIPT_DIR"/front/.env
DEV_ENV="$SCRIPT_DIR"/.env.dev

for env in "$API_ENV" "$API_DEV_ENV" "$FRONT_ENV" "$DEV_ENV"; do
    cp "$env".template "$env"
done

color_echo yellow "\nSetting $API_ENV..."
update_env "$API_ENV"
. "$API_ENV"
if [ "$TARGET" == "dev" ]; then
    echo_title "PRE-COMMIT INSTALL"
    api/venv/bin/pip install pre-commit
    pre-commit install
fi

color_echo yellow "\nSetting $DEV_ENV file & $API_DEV_ENV..."
update_env "$DEV_ENV"
copy_env_values "$DEV_ENV" "$API_DEV_ENV"

color_echo yellow "\nSetting $FRONT_ENV file..."
update_env "$FRONT_ENV"

# NOTE uncomment to use Redis password
# color_echo yellow "\nSetting Redis password..."
# set_redis $REDIS_PASSWORD

echo_title "INITIALIZE DJANGO"
. "$FRONT_ENV"
"$FRONT_VENV"/python manage.py migrate

create_superuser() {
    echo "from django.contrib.auth import get_user_model; \
    User = get_user_model(); \
    User.objects.filter(username='$ADMIN_NAME').exists() or \
    User.objects.create_superuser('$ADMIN_NAME', '$ADMIN_EMAIL', '$DB_PASSWORD')" | \
    "$FRONT_VENV"/python manage.py shell
}

color_echo yellow "\nCreating superuser\nusername: $ADMIN_NAME\nemail: $ADMIN_EMAIL\npassword: <same-as-db-password>..."
create_superuser

echo_title "SETUP WEBPACK"
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# BUG not working from there
setup_node() {
    if ! command -v nvm &> /dev/null; then
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        \. "$NVM_DIR/nvm.sh"
    fi
    nvm install node
}

setup_webpack() {
    cd "$FRONT_DIR"/webpack || exit 1
    npm install
    npm run production
}

# setup_node
# setup_webpack

# nvm install node
# npm install -g webpack
# npm install -g sass
# npm install -D webpack-cli
# cd "$FRONT_DIR"/webpack
#
# color_echo yellow "\nInit npm project inside $(pwd)..."
# npm init
# npm install
# npm run start
# npm run production
