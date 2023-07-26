SOURCE_IMAGE_NAME="centos7"
SOURCE_IMAGE="$REGISTRY/$SOURCE_IMAGE_NAME:$IMAGE_TAG"

IMAGE_NAME="centos7-apache"
IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

BUILD_OPTIONS="--squash --no-cache --build-arg=SOURCE_IMAGE=$SOURCE_IMAGE"
CONTAINER_NAME="ingress"
CREATE_OPTIONS="\
    --pod $POD_NAME \
    --volume vires-oauth-static:/var/www/vires/oauth_static \
    --volume vires-swarm-static:/var/www/vires/swarm_static \
    --volume vires-swarm-wps:/var/www/vires/swarm_wps \
    --volume ./ingress/vires.conf:/etc/httpd/conf.d/vires.conf \
    --volume ./volumes/logs/httpd:/var/log/vires/httpd \
"
