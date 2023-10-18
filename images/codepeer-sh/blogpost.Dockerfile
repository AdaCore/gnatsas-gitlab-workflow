FROM ubuntu:18.04 AS build
COPY gnatsas-24.0w-x86_64-linux-bin.tar.gz /tmp/gnatsas/gnatsas-24.0w-x86_64-linux-bin.tar.gz
RUN set -xe \
	&& cd /tmp \
	&& mkdir -p gnatsas \
	&& tar xf /tmp/gnatsas/gnatsas-24.0w-x86_64-linux-bin.tar.gz --strip-components 1 -C gnatsas \
	&& cd gnatsas \
	&& ./doinstall /opt/gnatsas \
	&& cd /opt/gnatsas \
	&& rm -rf share/doc/ \
    && rm -rf /tmp/gnatsas

# FROM gitlab/gitlab-runner AS run
FROM ubuntu:18.04 AS run
COPY --from=build /opt/gnatsas /opt/gnatsas
ENV PATH "/opt/gnatsas/bin:${PATH}"
