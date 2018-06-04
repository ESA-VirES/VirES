#!/bin/bash

. `dirname $0`/lib_common.sh
. `dirname $0`/lib_virtualenv.sh

info() { true ; }
error() { echo "ERROR: $1" ; exit 1; }

activate_virtualenv
"$@"
