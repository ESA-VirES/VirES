#!/bin/sh -e
#
# VirES web client installation script
#

_rmdir() {
    [ ! -d "$1" ] || rm -fR "$1"
}

[ -z "$1" ] && {
    echo "USAGE `basename $0` <source-path>" >&2
    exit 1
} 2>&1

BUILD_DIR="$VIRES_ROOT/build/client"
TARGET_DIR="$STATIC_DIR/workspace"
CLIENT_PACKAGE="$1"

# on exit clean-up
cleanup() {
    _rmdir "$BUILD_DIR"
}
trap cleanup EXIT

# remove the client build directory if existing
_rmdir "$BUILD_DIR"

# create new client build directory
[ -d "$BUILD_DIR" ] || mkdir -p "$BUILD_DIR"

# extract package content stripping original ownership, permissions and timestamp
tar --touch --no-same-owner --no-same-permissions -xzf "$CLIENT_PACKAGE" -C "$BUILD_DIR"

# find the location of the extracted directory
cd "$BUILD_DIR"
CLIENT_FILE="$( ls */index.html 2>/dev/null | head -n 1 )"
[ -n "$CLIENT_FILE" ] || {
    echo "ERROR: Failed to locate unpacked client directory."
    echo "ERROR: $CLIENT_PACKAGE does not seem to be a valid client package. "
    exit 1
} >&2
CLIENT_DIR="$( dirname "$CLIENT_FILE" )"

# remove the target directory if it exists
_rmdir "$TARGET_DIR"

# move all files to the target directory
mv "$CLIENT_DIR" "$TARGET_DIR"
