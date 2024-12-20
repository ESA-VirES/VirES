SOURCE_IMAGE_NAME="debian12-vires-swarm-base"
SOURCE_IMAGE="$REGISTRY/$SOURCE_IMAGE_NAME:$IMAGE_TAG"

IMAGE_NAME="debian12-vires-swarm-dpl"
IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

VIRES_DATA=${VIRES_DATA:-../../data}

BUILD_OPTIONS="\
    --squash \
    --no-cache \
    --build-arg=SOURCE_IMAGE=$SOURCE_IMAGE \
    --build-arg=EOXSERVER_GIT_REFERENCE=${EOXSERVER_GIT_REFERENCE:-master} \
    --build-arg=VIRES_SERVER_GIT_REFERENCE=${VIRES_SERVER_GIT_REFERENCE:-staging} \
    --build-arg=EOXMAGMOD_GIT_REFERENCE=${EOXMAGMOD_GIT_REFERENCE:-staging} \
    --build-arg=WPS_BACKEND_GIT_REFERENCE=${WPS_BACKEND_GIT_REFERENCE:-staging} \
    --build-arg=VIRES_SYNC_GIT_REFERENCE=${VIRES_SYNC_GIT_REFERENCE:-staging} \
    --build-arg=OAUTH_GIT_REFERENCE=${OAUTH_GIT_REFERENCE:-staging} \
"
CONTAINER_NAME="${POD_NAME:-vires-server}--swarm"
CREATE_OPTIONS="\
    --pod $POD_NAME \
    --volume ../../contrib/WebClient-Framework.tar.gz:/srv/vires/sources/WebClient-Framework.tar.gz:ro \
    --volume ./volumes/logs/swarm:/var/log/vires/swarm \
    --volume ./volumes/swarm:/srv/vires/swarm \
    --volume ./volumes/cache/products:/srv/vires/cache/products \
    --volume ./volumes/cache/models:/srv/vires/cache/models \
    --volume ${POD_NAME:-vires-server}--swarm-static:/srv/vires/swarm_static \
    --volume ${POD_NAME:-vires-server}--swarm-upload:/srv/vires/upload \
    --volume ${POD_NAME:-vires-server}--swarm-wps:/srv/vires/wps \
    --volume $VIRES_DATA:/srv/vires/data:ro \
"
EXEC_OPTIONS="--user vires"
RUN_OPTIONS="$CREATE_OPTIONS --entrypoint=/bin/bash"
