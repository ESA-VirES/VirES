#!/usr/bin/bash

FLAG_FILE="$VIRES_ROOT/.intialized"

# -----------------------------------------------------------------------------

_build_from_sdist() (
    cd "$1"
    rm -fR dist/ build/
    python3 ./setup.py sdist
    SDIST="`ls ./dist/*.tar.gz | tail -n 1`"
    [ -n "$SDIST" ] && pip3 install $PIP_OPTIONS "$SDIST"
)

install_deployment_packages() {
    (
        export CFLAGS="-L${VENV_ROOT}/lib -I${VENV_ROOT}/include -march=${GCC_MARCH} -mtune=${GCC_MTUNE} -ftree-vectorize"
        _build_from_sdist /usr/local/eoxmagmod
    )
    # NOTE: in Python 3.11 imp.find_module('eoxserver') does not work in the development mode.
    #pip3 install -e /usr/local/eoxserver
    #pip3 install /usr/local/eoxserver
    _build_from_sdist /usr/local/eoxserver
    pip3 install -e /usr/local/vires/vires
    pip3 install -e /usr/local/vires/eoxs_allauth
    pip3 install -e /usr/local/vires_sync
    pip3 install -e /usr/local/eoxs_wps_async
}

instance_exists() {
    test -f "$INSTANCE_DIR/manage.py"
}

create_new_instance() {
    export TIMESTAMP=`date -u +'%Y%m%dT%H%M%SZ'`

    echo "Creating Django instance ..."
    eoxserver-instance.py "$INSTANCE_NAME" "$INSTANCE_DIR"
    chmod +x "$INSTANCE_DIR/manage.py"

    echo "Fixing instance configuration ..."
    render_template "$CONFIGURATION_TEMPLATES_DIR/settings.py" "$VIRES_ROOT/secrets.conf" > "$INSTANCE_DIR/$INSTANCE_NAME/settings.py"
    cp "$CONFIGURATION_TEMPLATES_DIR/urls.py" "$INSTANCE_DIR/$INSTANCE_NAME/urls.py"
    render_template "$CONFIGURATION_TEMPLATES_DIR/eoxserver.conf" "$VIRES_ROOT/options.conf" > "$INSTANCE_DIR/$INSTANCE_NAME/conf/eoxserver.conf"
}

_create_log_file() {
    if ! [ -d "`dirname "$1"`" ]
    then
       mkdir -p "`dirname "$1"`"
    fi
    touch "$1"
    chown "$VIRES_USER:$VIRES_GROUP" "$1"
    chmod 0664 "$1"
}

_initialize_wps_dirs() {
    mkdir -m 0755 -p $VIRES_WPS_DIR/workspace
    mkdir -m 0755 -p $VIRES_WPS_DIR/public
    mkdir -m 0755 -p $VIRES_WPS_DIR/tasks
}

_fix_permissions() {
    chown "$VIRES_USER:$VIRES_GROUP" -R "$VIRES_HOME"
    chown "$VIRES_USER:$VIRES_GROUP" -R "$VIRES_PRODUCT_CACHE_DIR"
    chown "$VIRES_USER:$VIRES_GROUP" -R "$VIRES_MODEL_CACHE_DIR"
    chown "$VIRES_USER:$VIRES_GROUP" -R "$VIRES_SOCKET_DIR"
    chown "$VIRES_USER:$VIRES_GROUP" -R "$VIRES_WPS_DIR"
}

initialize_instance() {
    echo "Creating log files ..."

    _initialize_wps_dirs
    _fix_permissions

    _create_log_file "$INSTANCE_LOG"
    _create_log_file "$ACCESS_LOG"
    _create_log_file "$GUNICORN_ACCESS_LOG"
    _create_log_file "$GUNICORN_ERROR_LOG"

    # collect static files
    echo "Collecting static files ..."
    python3 "$INSTANCE_DIR/manage.py" collectstatic --noinput

    # install web client into the static folder
    install_client "$VIRES_ROOT/sources/WebClient-Framework.tar.gz"

    # setup new database
    echo "Migrating database  ..."
    python3 "$INSTANCE_DIR/manage.py" migrate --noinput

    # initialize product types and collections
    echo "Importing product types ..."
    python3 "$INSTANCE_DIR/manage.py" product_type import --default

    # initialize product collections
    echo "Importing product collections ..."
    python3 "$INSTANCE_DIR/manage.py" product_collection import --default

    # initialize identity provider
    render_template "$CONFIGURATION_TEMPLATES_DIR/oauth_idp.json" "$VIRES_ROOT/vires.conf" \
      | python3 "$INSTANCE_DIR/manage.py" social_provider import
}

# -----------------------------------------------------------------------------

# one-off initialization
if [ ! -f "$FLAG_FILE" ]
then
    install_deployment_packages

    if ! instance_exists
    then
        create_new_instance
    fi
    initialize_instance

    touch "$FLAG_FILE"
fi

if [ -z "$*" ]
then
    # start asynchronous WPS daemon
    echo "Starting asynchronous WPS daemon ...."
    [ ! -e "$VIRES_ASYNC_WPS_SOCKET_FILE" ] || rm -fv "$VIRES_ASYNC_WPS_SOCKET_FILE"
    runuser -u vires -g vires -- python3 -EsOm 'eoxs_wps_async.daemon' "$INSTANCE_NAME.settings" "$INSTANCE_DIR" &

    echo "Starting application server ...."
    exec gunicorn \
      --bind "[::1]:$SERVER_PORT" \
      --name "$INSTANCE_NAME" \
      --user "$VIRES_USER" \
      --group "$VIRES_GROUP" \
      --env "HOME=$VIRES_HOME" \
      --chdir "$INSTANCE_DIR" \
      --workers $SERVER_NPROC \
      --threads 1 \
      --pid "/run/$INSTANCE_NAME.pid" \
      --access-logfile "$GUNICORN_ACCESS_LOG" \
      --error-logfile "$GUNICORN_ERROR_LOG" \
      --capture-output \
      --preload \
      "$INSTANCE_NAME.wsgi"
else
    exec "$@"
fi
