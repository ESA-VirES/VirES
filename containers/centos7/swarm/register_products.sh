#!/bin/sh
#
# Register VirES-for-Swarm data products
#

search_products () {
    # recursively search for all products in the data folder
    find "$VIRES_DATA_DIR" -type f
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
        if [ "$A" == "register" -o "$A" == "deregister" ]
        then
            echo "$D"
        elif [ "$A" == "update" ]
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

search_products | filter_by_status | register_products
