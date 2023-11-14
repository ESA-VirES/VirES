# common settings

export POD_PORT="8300"
export POD_NAME="vires-server-debian12-dev"

list_images() {
    cat - << END
debian12
ingress
database
django-base
oauth-base
oauth
swarm-base
swarm
END
}

start_containers() {
    $BIN_DIR/container database start \
      && $BIN_DIR/container database exec /bin/sh -c 'while ! pg_isready ; do sleep 1 ; done' \
      && $BIN_DIR/container database exec -i create_db < $VIRES_CONTAINER_ROOT/volumes/secrets/oauth.conf \
      && $BIN_DIR/container database exec -i create_db < $VIRES_CONTAINER_ROOT/volumes/secrets/swarm.conf \
      && $BIN_DIR/container oauth start \
      && $BIN_DIR/container swarm start \
      && $BIN_DIR/container ingress start
}

VIRES_CONTAINER_ROOT="${VIRES_CONTAINER_ROOT:-.}"
[ -f "$VIRES_CONTAINER_ROOT/tag.conf" ] && . "$VIRES_CONTAINER_ROOT/tag.conf"
