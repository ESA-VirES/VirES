#!/bin/sh
#
DIR="$(cd "$(dirname $0)" ; pwd )"

while read C
do
    if $DIR/image_exists.sh "$C"
    then
        echo "$C image already exists. Build is skipped."
    else
        $DIR/build.sh "$C" || break
    fi
done << END 
centos7
ingress
database
django-base
oauth-base
oauth
swarm-base
swarm
END
