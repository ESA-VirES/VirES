#!/bin/bash

DIR="$(cd "$(dirname $0)" ; pwd )"
. $DIR/common.sh
. $DIR/database/common.sh
POSTGRE_IMAGE=$IMAGE
. $DIR/django-base/common.sh
DJANGO_IMAGE=$IMAGE

_cleanup() {
    [ -n "$TEMP" -a -f "$TEMP" ] && rm -f "$TEMP"
}
trap _cleanup EXIT


_save_secrets() {
    TARGET="$1"
    rm -fv $TARGET
    if [ -f "$TARGET" ]
    then
        echo "$TARGET already exists"
        return
    fi
    TEMP="$TARGET.tmp"
    touch $TEMP
    chmod 0600 $TEMP
    cat >> "$TEMP"
    mv "$TEMP" "$TARGET"
    echo "$TARGET created"
} 


_generate_instance_secrets() {
    TARGET="$1"
    shift
    { 
        podman run --entrypoint /bin/bash --rm "$POSTGRE_IMAGE" get_random_db_creadentials "$@"
        podman run --rm "$DJANGO_IMAGE" python -c "from django.core.management.utils import get_random_secret_key; print(f'SECRET_KEY={get_random_secret_key()}')"
    } | _save_secrets "$TARGET"
}

_generate_oauth_secrets() {
    TARGET="$1"
    { 
        echo "CLIENT_ID=` base64 /dev/urandom | tr -d '+/\n' | head -c 40 `"
        echo "CLIENT_SECRET=` base64 /dev/urandom | tr -d '+/\n' | head -c 128 `"
    } | _save_secrets "$TARGET"
}


_generate_instance_secrets ./volumes/secrets/oauth.conf oauth oauth_user
_generate_instance_secrets ./volumes/secrets/swarm.conf swarm swarm_user postgis
_generate_oauth_secrets ./volumes/secrets/vires.conf