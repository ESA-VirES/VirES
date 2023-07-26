#!/bin/sh

DIR="$(cd "$(dirname $0)" ; pwd )"
. $DIR/common.sh

if ! podman pod exists "$POD_NAME"
then
    podman pod create -n "$POD_NAME" -p 8200:80
fi

$DIR/start.sh database \
  && $DIR/exec.sh database -i create_db < $DIR/volumes/secrets/oauth.conf \
  && $DIR/exec.sh database -i create_db < $DIR/volumes/secrets/swarm.conf \
  && $DIR/start.sh oauth \
  && $DIR/start.sh swarm \
  && $DIR/start.sh ingress

