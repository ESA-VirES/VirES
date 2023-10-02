SOURCE_IMAGE_NAME="centos7-vires-swarm-base"
SOURCE_IMAGE="$REGISTRY/$SOURCE_IMAGE_NAME:$IMAGE_TAG"

IMAGE_NAME="centos7-vires-swarm-dev"
IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

VIRES_DATA=${VIRES_DATA:-../../data}

BUILD_OPTIONS="--squash --no-cache --build-arg=SOURCE_IMAGE=$SOURCE_IMAGE"
CONTAINER_NAME="swarm"
CREATE_OPTIONS="\
    --pod $POD_NAME \
    --volume ../../../VirES-Server:/usr/local/vires \
    --volume ../../../eoxserver:/usr/local/eoxserver \
    --volume ../../../MagneticModel/eoxmagmod:/usr/local/eoxmagmod \
    --volume ../../../WPS-Backend:/usr/local/eoxs_wps_async \
    --volume ../../../vires_sync:/usr/local/vires_sync \
    --volume ../../contrib/WebClient-Framework.tar.gz:/srv/vires/sources/WebClient-Framework.tar.gz:ro \
    --volume ./volumes/secrets/swarm.conf:/srv/vires/secrets.conf:ro \
    --volume ./volumes/secrets/vires.conf:/srv/vires/vires.conf:ro \
    --volume ./volumes/options.conf:/srv/vires/options.conf:ro \
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
