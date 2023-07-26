SOURCE_IMAGE_NAME="centos7"
SOURCE_IMAGE="$REGISTRY/$SOURCE_IMAGE_NAME:$IMAGE_TAG"

IMAGE_NAME="centos7-postgresql12"
IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

BUILD_OPTIONS="--squash --no-cache --build-arg=SOURCE_IMAGE=$SOURCE_IMAGE"
CONTAINER_NAME="postgres"
CREATE_OPTIONS="\
    --pod $POD_NAME \
    --volume vires-pgdb-12:/var/lib/postgresql/data \
    --volume vires-pgdb-12-logs:/var/log/postgresql \
    --volume .:/host \
"
