IMAGE_NAME="debian12"

IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

BUILD_OPTIONS="--squash-all --no-cache"
OPTIONS="-u root"
