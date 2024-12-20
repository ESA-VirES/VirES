SOURCE_IMAGE_NAME="debian12-vires-oauth-base"
SOURCE_IMAGE="$REGISTRY/$SOURCE_IMAGE_NAME:$IMAGE_TAG"

IMAGE_NAME="debian12-vires-oauth-dpl"
IMAGE="$REGISTRY/$IMAGE_NAME:${OAUTH_IMAGE_TAG:-${IMAGE_TAG}}"

BUILD_OPTIONS="\
    --squash \
    --no-cache \
    --build-arg=SOURCE_IMAGE=$SOURCE_IMAGE \
    --build-arg=OAUTH_GIT_REFERENCE=${OAUTH_GIT_REFERENCE:-staging} \
"
CONTAINER_NAME="${POD_NAME:-vires-server}--oauth"
CREATE_OPTIONS="\
    --pod $POD_NAME \
    --volume ./volumes/logs/oauth:/var/log/vires/oauth \
    --volume ./volumes/oauth:/srv/vires/oauth \
    --volume ${POD_NAME:-vires-server}--oauth-static:/srv/vires/oauth_static \
"
EXEC_OPTIONS="--user vires"
RUN_OPTIONS="$CREATE_OPTIONS"
