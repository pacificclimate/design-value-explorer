FROM python:3.6-slim

USER root

RUN apt-get update && \
    apt-get install -y git

# Build arguments (scope limited to build). If you wish to use a different user,
# group, or user home dir, override these in the build command or change them here.
# If you specify build arg USERNAME=root, then the user is root.
ARG USERNAME=dockremap
ARG UID=1000
ARG GROUPNAME=${USERNAME}
ARG GID=1000
ARG USER_DIR=/opt/${USERNAME}

# Environment variables (scope NOT limited to build). These are set here so that
# subsequent builds and containers have access to these build arguments.
ENV USERNAME=${USERNAME}
ENV UID=${UID}
ENV GROUPNAME=${GROUPNAME}
ENV GID=${GID}
ENV USER_DIR=${USER_DIR}

# Create non-privileged user, group, and its directory. This is only done if USERNAME is not root.
RUN if [ "$USERNAME" != "root" ]; \
    then \
        echo "Creating non-root user"; \
        groupadd -r -g ${GID} ${GROUPNAME}; \
        useradd -r -d ${USER_DIR} -g ${GROUPNAME} -u ${UID} ${USERNAME}; \
        mkdir -p ${USER_DIR}; \
        chown ${USERNAME}:${GROUPNAME} ${USER_DIR}; \
    fi

# IMPORTANT: You must mount the local codebase to this directory
WORKDIR /codebase
ADD *requirements.txt /codebase/
RUN chown ${USERNAME}:${GROUPNAME} /codebase

# Set user
USER ${USERNAME}

RUN pip install --trusted-host pypi.python.org -r /codebase/requirements.txt #\
    #pip install -e git+https://github.com/pacificclimate/climpyrical.git#egg=climpyrical
# requirements.txt contains a line for clympirical, but it is not installed (???)
# after the first pip install. The second one fixes that. An ugly mystery.

# Flask app port
EXPOSE 5000

ENV NAME Explorer

# On container startup, the entrypoint installs the local codebase
ENTRYPOINT /codebase/docker/dev-local/entrypoint.sh
