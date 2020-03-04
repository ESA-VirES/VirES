#-------------------------------------------------------------------------------
#
# Purpose: VirES-Server instance configuration - development customisation
# Author(s): Martin Paces <martin.paces@eox.at>
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH

. `dirname $0`/../lib_logging.sh
. `dirname $0`/../lib_vires.sh

info "Enabling VirES-Server instance debugging mode ... "

set_instance_variables

ex "$SETTINGS" <<END
g/^DEBUG\s*=/s#\(^DEBUG\s*=\s*\).*#\1True#
.
wq
END
