#!/usr/bin/bash

FLAG_FILE="$VIRES_ROOT/.intialized"

# -----------------------------------------------------------------------------

install_deployment_packages() {
    pip3 install -e /usr/local/vires/vires_oauth
}

instance_exists() {
    test -f "$INSTANCE_DIR/manage.py"
}

setup_instance() {
    echo "Creating Django instance ..."
    django-admin startproject "$INSTANCE_NAME" "$INSTANCE_DIR"

    echo "Fixing instance configuration ..."
    render_template "$CONFIGURATION_TEMPLATES_DIR/settings.py" "$VIRES_ROOT/secrets.conf" > "$INSTANCE_DIR/$INSTANCE_NAME/settings.py"
    cp "$CONFIGURATION_TEMPLATES_DIR/urls.py" "$INSTANCE_DIR/$INSTANCE_NAME/urls.py"
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

_fix_home_permissions() {
    chown "$VIRES_USER:$VIRES_GROUP" -R "$VIRES_HOME"
}

initialize_instance() {
    echo "Creating log files ..."

    _fix_home_permissions

    _create_log_file "$INSTANCE_LOG"
    _create_log_file "$ACCESS_LOG"
    _create_log_file "$GUNICORN_ACCESS_LOG"
    _create_log_file "$GUNICORN_ERROR_LOG"

    # collect static files
    echo "Collecting static files ..."
    python3 "$INSTANCE_DIR/manage.py" collectstatic --noinput

    # setup new database
    echo "Migrating database  ..."
    python3 "$INSTANCE_DIR/manage.py" migrate --noinput

    # initialize user permissions
    echo "Importing permissions  ..."
    python3 "$INSTANCE_DIR/manage.py" permission import --default

    # initialize user groups
    echo "Importing groups ..."
    python3 "$INSTANCE_DIR/manage.py" group import --default

    # initialize users
    echo "Importing users ..."
    python3 "$INSTANCE_DIR/manage.py" user import < "$VIRES_ROOT/users.json"

    # initialize OAuth apps
    echo "Configuring OAuth apps ..."
    render_template "$CONFIGURATION_TEMPLATES_DIR/swarm_app.json" "$VIRES_ROOT/vires.conf" "$VIRES_ROOT/options.conf" \
      | python3 "$INSTANCE_DIR/manage.py" app import
}

# -----------------------------------------------------------------------------

# one-off initialization
if [ ! -f "$FLAG_FILE" ]
then
    install_deployment_packages

    if ! instance_exists
    then
        setup_instance
    fi
    initialize_instance

    touch "$FLAG_FILE"
fi

if [ -z "$*" ]
then
    exec gunicorn \
      --bind "[::1]:$SERVER_PORT" \
      --name "$INSTANCE_NAME" \
      --user "$VIRES_USER" \
      --group "$VIRES_GROUP" \
      --env "HOME=$VIRES_HOME" \
      --chdir "$INSTANCE_DIR" \
      --workers $SERVER_NPROC \
      --threads $SERVER_NTHREAD \
      --pid "/run/$INSTANCE_NAME.pid" \
      --access-logfile "$GUNICORN_ACCESS_LOG" \
      --error-logfile "$GUNICORN_ERROR_LOG" \
      --capture-output \
      --preload \
      "$INSTANCE_NAME.wsgi"
else
    exec "$@"
fi
