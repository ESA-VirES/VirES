SOURCE_IMAGE_NAME="centos7"
SOURCE_IMAGE="$REGISTRY/$SOURCE_IMAGE_NAME:$IMAGE_TAG"

IMAGE_NAME="centos7-apache"
IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

BUILD_OPTIONS="--squash --no-cache --build-arg=SOURCE_IMAGE=$SOURCE_IMAGE"
CONTAINER_NAME="${POD_NAME:-vires-server}--ingress"
CREATE_OPTIONS="\
    --pod $POD_NAME \
    --volume ${POD_NAME:-vires-server}--oauth-static:/var/www/vires/oauth_static:ro \
    --volume ${POD_NAME:-vires-server}--swarm-static:/var/www/vires/swarm_static:ro \
    --volume ${POD_NAME:-vires-server}--swarm-wps:/var/www/vires/swarm_wps:ro \
    --volume ./ingress/vires.conf:/etc/httpd/conf.d/vires.conf:ro \
    --volume ./volumes/logs/httpd:/var/log/vires/httpd \
"
