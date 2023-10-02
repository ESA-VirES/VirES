#!/bin/sh

DIR="$(cd "$(dirname $0)" ; pwd )"
. $DIR/common.sh

if ! podman pod exists "$POD_NAME"
then
    podman pod create -n "$POD_NAME" -p "$POD_PORT:80"
    echo "SERVICE_URL=http://localhost:$POD_PORT" > $DIR/volumes/options.conf
fi


# NOTE: it takes some time to initialize the components
# TODO: implement check that DB is up and running

$DIR/start.sh database \
  && sleep 30 \
  && $DIR/exec.sh database -i create_db < $DIR/volumes/secrets/oauth.conf \
  && $DIR/exec.sh database -i create_db < $DIR/volumes/secrets/swarm.conf \
  && $DIR/start.sh oauth \
  && $DIR/start.sh swarm \
  && $DIR/start.sh ingress
