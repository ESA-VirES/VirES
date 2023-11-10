IMAGE_NAME="debian12"

IMAGE="$REGISTRY/$IMAGE_NAME:${BASE_IMAGE_TAG:-${IMAGE_TAG}}"

BUILD_OPTIONS="--squash-all --no-cache"
OPTIONS="-u root"
