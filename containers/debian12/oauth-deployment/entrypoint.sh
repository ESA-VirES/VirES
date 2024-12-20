#!/bin/bash

FLAG_FILE="$VIRES_ROOT/.intialized"

# -----------------------------------------------------------------------------

create_group_and_user() {
    if grep -q "^$VIRES_GROUP:" /etc/group
    then
        echo "Creating group $VIRES_GROUP${VIRES_GROUP_ID:+(gid=$VIRES_GROUP_ID)} ..."
        groupadd -r ${VIRES_GROUP_ID:+--gid} "$VIRES_GROUP_ID" "$VIRES_GROUP"
    fi

    if grep -q "^$VIRES_USER:" /etc/passwd
    then
        echo "Creating user $VIRES_USER${VIRES_USER_ID:+(uid=$VIRES_USER_ID)} ..."
        useradd -r -M -g "$VIRES_GROUP" -d "$VIRES_HOME" -s /sbin/nologin -c "VirES system user" ${VIRES_USER_ID:+--gid} "$VIRES_USER_ID""$VIRES_USER"
        chown "$VIRES_USER:$VIRES_GROUP" -R "$VIRES_HOME"
    fi
}

instance_exists() {
    test -f "$INSTANCE_DIR/manage.py"
}

create_new_instance() {
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

initialize_instance() {
    echo "Creating log files ..."

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
}

# -----------------------------------------------------------------------------

# one-off initialization
if [ ! -f "$FLAG_FILE" ]
then
    create_group_and_user

    if ! instance_exists
    then
        create_new_instance
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

