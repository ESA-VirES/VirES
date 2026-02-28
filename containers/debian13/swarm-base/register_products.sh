#!/bin/sh
#
# Register VirES-for-Swarm data products
#
# USAGE:
#
#    register_products.sh
#        register all applicable products found in the data directory
#
#    register_products.sh <directory> [<directory> ...]
#        register all applicable products found in one or more given
#        directories
#
#    register_products.sh <file> [<file> ...]
#        register one or more products passed as the CLI arguments
#
#    register_products.sh -
#        register products passed via standard input
#

search_products () {
    # recursively search for all products in the data folder
    find "$1" -type f
}

filter_by_status () {
    # This subroutine filters files read from the standard input and based
    # on the their registration status decided whether it should be passed
    # forward for further processing or not.
    # Namely, it prints to standard output products to be registered,
    # deregistered or updated (cached products).
    # It skips conflict reports and dumps them to standard output.
    # It skips silently already registered products which do not need any
    # action.
    vires_sync_status_check -m "$INSTANCE_NAME.settings" -p "$INSTANCE_DIR" \
      | while read A B C D
    do
        if [ "$A" = "register" -o "$A" = "deregister" ]
        then
            echo "$D"
        elif [ "$A" = "update" ]
        then
            echo "$C"
        else
            # fallback - just print the whole line to stderr
            echo "$A $B $C $D" 1>&2
        fi
    done
}

register_products() {
    # process incoming products read from the standard input
    # files not recognized as valid products are skipped
    vires_sync_watch stdin vires -m "$INSTANCE_NAME.settings" -p "$INSTANCE_DIR" --fix-logging --unique
}


{
    _STDIN=
    if [ "$#" -eq 0 ]
    then
        # by default search the mounted data volume
        search_products "$VIRES_DATA_DIR"
    else
        # for each argument
        for ARG
        do
            if [ "$ARG" = "-" ]
            then
                # pass trough standard input, but not more than once
                [ -z "$_STDIN" ] && cat
                _STDIN="1"
            elif [ -d "$ARG" ]
            then
                # recursively search files in a directory
                search_products "$ARG"
            elif [ -f "$ARG" ]
            then
                # pass files directly
                echo "$ARG"
            else
                # or just ignore the invalid argument
                echo "$ARG is ignored." >&2
            fi
        done
    fi
} | filter_by_status | register_products
