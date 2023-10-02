SOURCE_IMAGE_NAME="centos7-vires-oauth-base"
SOURCE_IMAGE="$REGISTRY/$SOURCE_IMAGE_NAME:$IMAGE_TAG"

IMAGE_NAME="centos7-vires-oauth-dev"
IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

BUILD_OPTIONS="--squash --no-cache --build-arg=SOURCE_IMAGE=$SOURCE_IMAGE"
CONTAINER_NAME="${POD_NAME:-vires-server}--oauth"
CREATE_OPTIONS="\
    --pod $POD_NAME \
    --volume ../../../VirES-Server:/usr/local/vires \
    --volume ./volumes/logs/oauth:/var/log/vires/oauth \
    --volume ./volumes/oauth:/srv/vires/oauth \
    --volume ${POD_NAME:-vires-server}--oauth-static:/srv/vires/oauth_static \
    --volume ./volumes/secrets/oauth.conf:/srv/vires/secrets.conf:ro \
    --volume ./volumes/secrets/vires.conf:/srv/vires/vires.conf:ro \
    --volume ./volumes/options.conf:/srv/vires/options.conf:ro \
    --volume ./volumes/secrets/users.json:/srv/vires/users.json:ro \
"
EXEC_OPTIONS="--user vires"
