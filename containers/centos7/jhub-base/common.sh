SOURCE_IMAGE="python:3.11-bookworm"
#BUILD_WITH_FRESH_SOURCE="YES"

IMAGE_NAME="centos7-jhub-base"
IMAGE="$REGISTRY/$IMAGE_NAME:${JHUB_IMAGE_TAG:-${IMAGE_TAG}}"

BUILD_OPTIONS="--squash --no-cache --build-arg=SOURCE_IMAGE=$SOURCE_IMAGE"
CONTAINER_NAME="${POD_NAME:-vires-server}--jhub"
