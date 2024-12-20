#-----------------------------------------------------------------------
#
# JupyterHub base development image
#
# Copyright (C) 2023 EOX IT Services GmbH
#-----------------------------------------------------------------------

ARG SOURCE_IMAGE
FROM $SOURCE_IMAGE
LABEL maintainer="EOX <martin.paces@eox.at>"

USER root

ENV VIRES_ROOT="/srv/vires"
ENV VENV_ROOT="$VIRES_ROOT/venv_jhub"
ENV USER_VENV_ROOT="$VIRES_ROOT/venv_jlab"
ENV PIP_OPTIONS="--upgrade --upgrade-strategy=only-if-needed"

# store copy of the original PATH
ENV _PATH="$PATH"

RUN apt-get -y update \
 && apt-get -y install nodejs npm \
 && apt-get -y install vim-tiny less \
 && apt-get -y clean

RUN npm install -g configurable-http-proxy
RUN rm -fR /root/.npm

# JupyterHub venv installation
RUN python3 -m 'venv' "$VENV_ROOT"
ENV PATH="$VENV_ROOT/bin:$_PATH"

RUN pip3 install $PIP_OPTIONS pip
RUN pip3 install $PIP_OPTIONS wheel
RUN pip3 install $PIP_OPTIONS Jinja2
RUN pip3 install $PIP_OPTIONS "jupyterhub<5.0"
RUN pip3 install $PIP_OPTIONS "oauthenticator<17.0"
RUN pip3 install $PIP_OPTIONS notebook
RUN pip3 install $PIP_OPTIONS jupyterlab
RUN pip3 install $PIP_OPTIONS viresclient
RUN pip3 cache purge && rm -fR "/root/.cache"

ENV PATH="$_PATH"

# JupyterLabe venv installation
RUN python3 -m 'venv' "$USER_VENV_ROOT"
ENV PATH="$USER_VENV_ROOT/bin:$_PATH"

RUN pip3 install $PIP_OPTIONS notebook
RUN pip3 install $PIP_OPTIONS jupyterlab
RUN pip3 install $PIP_OPTIONS viresclient
RUN pip3 cache purge && rm -fR "/root/.cache"

ENV PATH="$VENV_ROOT/bin:$_PATH"

# install script rendering Jinja2 templates
COPY render_template.py $VENV_ROOT/bin/render_template
