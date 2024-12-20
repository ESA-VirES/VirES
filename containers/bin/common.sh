#!/bin/sh
#
# common shared code
#

info() {
    echo "$*" >&2
}

error() {
    echo "ERROR: $*" >&2
}

if [ -z "$VIRES_CONTAINER_ROOT" ]
then
    error "Missing the mandatory VIRES_CONTAINER_ROOT environment variable!"
    error "Have you activated the VirES container environment?"
    exit 1
fi

REGISTRY='registry.gitlab.eox.at/esa/vires-dempo_ops'

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

export DOCKER_CONFIG="${DOCKER_CONFIG:-$( cd "$(dirname "$0")"/.. ; pwd ;)}"
export REGISTRY_AUTH_FILE="${REGISTRY_AUTH_FILE:-$DOCKER_CONFIG/config.json}"
