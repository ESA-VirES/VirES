SOURCE_IMAGE_NAME="debian12"
SOURCE_IMAGE="$REGISTRY/$SOURCE_IMAGE_NAME:$IMAGE_TAG"

IMAGE_NAME="debian12-redis"
IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

BUILD_OPTIONS="--squash --no-cache --build-arg=SOURCE_IMAGE=$SOURCE_IMAGE"
CONTAINER_NAME="${POD_NAME:-vires-server}--redis"
CREATE_OPTIONS="\
    --pod $POD_NAME \
    --volume ${POD_NAME:-vires-server}--redis:/var/lib/redis \
    --volume ${POD_NAME:-vires-server}--redis-logs:/var/log/redis \
"
