#!/bin/sh
#-------------------------------------------------------------------------------
#
# Purpose: numpy PLY (Pyhton Lex-Yacc) installation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_python_venv.sh

info "Installing PLY (Pyhton Lex-Yacc) ..."

activate_venv "$VIRES_VENV_ROOT"

pip install $PIP_OPTIONS 'ply<4'
