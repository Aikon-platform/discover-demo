#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source "$SCRIPT_DIR/utils.sh"

get_env_value() {
    param=$1
    env_file=$2
    value=$(awk -F= -v param="$param" '/^[^#]/ && $1 == param {gsub(/"/, "", $2); print $2}' "$env_file")
    echo "$value"
}

SED_CMD="sed -i -e"

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
            $SED_CMD "s~^$param=.*~$param=\"$new_value\"~" "$env_file"
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
                $SED_CMD "s~^$param=.*~$param=$default_val~" "$target_env"
            else
                echo "$param=$default_val" >> "$target_env"
            fi
        fi
    done
}

echo_title "SET UP ENVIRONMENT VARIABLES"
for env in "$API_DIR"/.env "$FRONT_DIR"/.env "$SCRIPT_DIR"/.env.dev "$API_DIR"/.env.dev; do
    color_echo yellow "\nCopying up $env..."
    cp "$env".template "$env"
done

for env in "$API_DIR"/.env "$FRONT_DIR"/.env "$SCRIPT_DIR"/.env.dev; do
    color_echo yellow "\nSetting up $env..."
    update_env "$env"
done
copy_env_values "$SCRIPT_DIR"/.env.dev "$API_DIR"/.env.dev
