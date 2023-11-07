#!/bin/bash
#
# Source this script to activate the container environment.
#

get_absolute_path() {
    cd "$1"
    pwd
}

extend_path() {
    case ":$PATH:" in
        *":$1:"* ) echo "$PATH" ;;
        *) echo "$1${PATH:+:}$PATH" ;;
    esac
}

if [ "$0" != "$BASH_SOURCE" ]
then
    export VIRES_CONTAINER_ROOT="$( get_absolute_path "$(dirname "$BASH_SOURCE")" )"
    export PATH="$( extend_path "$( get_absolute_path "$VIRES_CONTAINER_ROOT/../bin" )" )"
    export PS1="{$( basename "$VIRES_CONTAINER_ROOT" )} $(echo -n "$PS1" | sed -e 's/{.*} //g')"
else
    echo "ERROR: This script should be sourced from bash!" >&2
fi
