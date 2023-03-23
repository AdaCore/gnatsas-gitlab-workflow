FROM gnatpro:deps AS build-install
ARG codepeer
ARG gnat

# Install from local archive
COPY ${codepeer} /tmp/codepeer_release.tar.gz
COPY ${gnat} /tmp/gnatpro_release.tar.gz
RUN set -xe \
    && cd /tmp \
    && mkdir codepeer_release \
    && tar -xf codepeer_release.tar.gz -C codepeer_release/ \
        --strip-components 1 \
    && cd codepeer_release \
    && (echo "/opt/codepeer"; sleep 0.1; echo "y") | ./doinstall \
    && cd /opt/codepeer/share \
    && mv doc/codepeer/ /tmp/codepeer \
    && rm -rf doc/* examples \
    && mv /tmp/codepeer doc/codepeer

RUN set -xe \
    && cd /tmp \
    && mkdir gnatpro_release \
    && tar -xf gnatpro_release.tar.gz -C gnatpro_release/ \
        --strip-components 1 \
    && cd gnatpro_release \
    && echo "\n/opt/gnatpro\ny\ny" | ./doinstall \
    && cd /opt/gnatpro/share \
    && rm -rf doc man examples

FROM gnat-gitlab-runner
COPY --from=build-install /opt/codepeer /opt/codepeer
COPY --from=build-install /opt/gnatpro /opt/gnatpro

ENV PATH "/opt/codepeer/bin:/opt/gnatpro/bin:${PATH}"
