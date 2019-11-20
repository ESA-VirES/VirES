#!/bin/bash

. `dirname $0`/lib_common.sh
. `dirname $0`/lib_python3_venv.sh

info() { true ; }
error() { echo "ERROR: $1" ; exit 1; }

export P3_VENV_ROOT="$VIRES_ROOT/python3_jhub"
activate_venv
"$@"
