SOURCE_IMAGE_NAME="centos7-jhub-base"
SOURCE_IMAGE="$REGISTRY/$SOURCE_IMAGE_NAME:${JHUB_IMAGE_TAG:-${IMAGE_TAG}}"

IMAGE_NAME="centos7-jhub-dev"
IMAGE="$REGISTRY/$IMAGE_NAME:${JHUB_IMAGE_TAG:-${IMAGE_TAG}}"

BUILD_OPTIONS="--squash --no-cache --build-arg=SOURCE_IMAGE=$SOURCE_IMAGE"
CONTAINER_NAME="${POD_NAME:-vires-server}--jhub"
CREATE_OPTIONS="\
    --pod $POD_NAME \
    --volume ../../../VirES-Server:/usr/local/vires \
    --volume ./volumes/secrets/jhub.conf:/srv/vires/secrets.conf:ro \
    --volume ./volumes/secrets/oauth_jhub.conf:/srv/vires/oauth.conf:ro \
    --volume ./volumes/logs/jhub:/var/log/vires/jhub \
    --volume ./volumes/jhub:/srv/vires/users \
    --volume ${POD_NAME:-vires-server}--jhub:/srv/vires/data \
"
RUN_OPTIONS="$CREATE_OPTIONS"
