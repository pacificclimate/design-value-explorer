FROM python:3.8-slim

USER root

RUN apt-get update && \
    apt-get install -y git libgeos-dev

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

# Install dependencies
# Note we install in ${USER_DIR} and not /codebase. This prevents the mounting
# of /codebase to the container from obscuring the installation of clympirical.
WORKDIR ${USER_DIR}
ENV PATH ${USER_DIR}/.local/bin:${PATH}
COPY --chown=${USERNAME}:${GROUPNAME} Pipfile* ${USER_DIR}/
USER ${USERNAME}
RUN pip install -U pip pipenv && \
    pipenv install --dev

# Flask app port
EXPOSE 5000

ENV NAME Explorer

# On container startup, the entrypoint installs the local codebase
ENTRYPOINT /codebase/docker/dev-local/entrypoint.sh
