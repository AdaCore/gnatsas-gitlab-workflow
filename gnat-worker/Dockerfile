FROM gnat-gitlab-runner
ARG gnat

RUN apt update \
    && apt install \
        git \
        zip \
    && rm -rf /var/lib/apt/lists/
