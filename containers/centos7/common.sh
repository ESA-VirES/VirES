# common settings

REGISTRY='registry.gitlab.eox.at/esa/vires-dempo_ops'

absdirpath() {
    [ -d "$1" ] || {
        echo "ERROR: $1 directory does not exist!"
        exit 1
    } 1>&2
    echo "`( cd "$1" ; pwd ; )`"
}

if [ -n "`which podman`" ]
then
    CT_COMMAND="`which podman`"
elif [ -n "`which docker`" ]
then
    CT_COMMAND="`which docker`"
else
    echo "ERROR: Neither podman nor docker container engine installed!" 1>&2
    exit 1
fi

export DOCKER_CONFIG="${DOCKER_CONFIG:-$(dirname "$0")}"
export REGISTRY_AUTH_FILE="${REGISTRY_AUTH_FILE:-$DOCKER_CONFIG/config.json}"

export POD_PORT="8200"
export POD_NAME="vires-server-dev"

. ./tag.conf
