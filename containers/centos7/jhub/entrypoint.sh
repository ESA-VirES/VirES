#!/usr/bin/bash

SOURCE_PATH="/usr/local/vires/vires_jhub"
FLAG_FILE="$VIRES_ROOT/.intialized"
START_SCRIPT="/usr/local/bin/vires-jupyterhub-singleuser"

PID_FILE="/bin/run/jhub.pid"

install_deployment_packages() {
    pip3 install -e "$SOURCE_PATH"

    # link VirES custom static assets
    ln -sf "$SOURCE_PATH/share/vires_jhub/static" "$VENV_ROOT/share/jupyterhub/static/vires"
}

# -----------------------------------------------------------------------------

# one-off initialization
if [ ! -f "$FLAG_FILE" ]
then
    install_deployment_packages

    # fix PATH variable overwritten by the /etc/profile script
    {
        echo "# Preserve JupyterLab shell search path ..."
        echo "export PATH=\"\${JLAB_PATH:-\$PATH}\""
    } > /etc/profile.d/jlab.sh

    # generate start-up script
    cat >"$START_SCRIPT" <<END
#!/usr/bin/bash
$USER_VENV_ROOT/bin/viresclient init_configuration
exec $VENV_ROOT/bin/jupyterhub-singleuser "\$@"
END
    chmod +x "$START_SCRIPT"

    touch "$FLAG_FILE"
fi

# load configuration options
source <(render_template "$CONFIGURATION_TEMPLATES_DIR/server_conf.sh" "$VIRES_ROOT/secrets.conf" "$VIRES_ROOT/oauth.conf")


if [ -z "$*" ]
then
    [ ! -f "$PID_FILE" ] || rm -fv "$PID_FILE"
    cd "${DATA_DIR:-.}"
    exec jupyterhub \
      --JupyterHub.logo_file="$VENV_ROOT/share/jupyterhub/static/vires/images/vre_logo.svg" \
      --JupyterHub.template_paths="['$SOURCE_PATH/share/vires_jhub/templates']" \
      --JupyterHub.template_vars="{'vires_url':''}" \
      --JupyterHub.pid_file="/run/jhub.pid" \
      --JupyterHub.authenticator_class="vires_jhub.authenticator.ViresOAuthenticator" \
      --JupyterHub.spawner_class="jupyterhub.spawner.SimpleLocalProcessSpawner" \
      --JupyterHub.bind_url="http://:$SERVER_PORT" \
      --JupyterHub.base_url="/jhub" \
      --JupyterHub.db_url="sqlite:///${DATA_DIR:-.}/jupyterhub.sqlite" \
      --Spawner.default_url="/lab" \
      --Spawner.cmd="['$START_SCRIPT']" \
      --Spawner.args="['--allow-root']" \
      --Spawner.environment="{'PATH':'$USER_VENV_ROOT/bin:$_PATH','JLAB_PATH':'$USER_VENV_ROOT/bin:$_PATH'}" \
      --SimpleLocalProcessSpawner.home_dir_template="$USERS_DIR/{username}" \
      --ViresOAuthenticator.enable_auth_state=True \
      --ViresOAuthenticator.server_url="/oauth/" \
      --ViresOAuthenticator.direct_server_url="http://[::1]:$OAUTH_SERVER_PORT" \
      --ViresOAuthenticator.client_id="$CLIENT_ID" \
      --ViresOAuthenticator.client_secret="$CLIENT_SECRET" \
      --ViresOAuthenticator.admin_permission="admin" \
      --ViresOAuthenticator.instance_name="Vagrant JupyterHub" \
      --ViresOAuthenticator.default_data_server="http://[::1]:$SWARM_SERVER_PORT" \
      --ViresOAuthenticator.data_servers="{'swarm':'http://[::1]:$SWARM_SERVER_PORT'}" \
      --ViresOAuthenticator.user_permission="swarm_vre" \
      &>> "$LOG_DIR/jhub/server.log"
else
    exec "$@"
fi
