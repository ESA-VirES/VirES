SOURCE_IMAGE_NAME="debian13"
SOURCE_IMAGE="$REGISTRY/$SOURCE_IMAGE_NAME:$IMAGE_TAG"

IMAGE_NAME="debian13-postgresql17"
IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

BUILD_OPTIONS="--squash --no-cache --build-arg=SOURCE_IMAGE=$SOURCE_IMAGE"
CONTAINER_NAME="${POD_NAME:-vires-server}--postgres"
CREATE_OPTIONS="\
    --pod $POD_NAME \
    --volume ${POD_NAME:-vires-server}--pgdb-17:/var/lib/postgresql/data \
    --volume ${POD_NAME:-vires-server}--pgdb-17-logs:/var/log/postgresql \
"
