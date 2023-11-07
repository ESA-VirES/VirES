# common settings

export POD_PORT="8300"
export POD_NAME="vires-server-debian12-dev"

list_images() {
    cat - << END
debian12
ingress
database
django-base
oauth-base
oauth
swarm-base
swarm
END
}

. ./tag.conf
