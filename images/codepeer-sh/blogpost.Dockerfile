FROM ubuntu:18.04 AS build
COPY codepeer-24.0w-x86_64-linux-bin.tar.gz /tmp/codepeer/codepeer-24.0w-x86_64-linux-bin.tar.gz
RUN set -xe \
	&& cd /tmp \
	&& mkdir -p codepeer \
	&& tar xf /tmp/codepeer/codepeer-24.0w-x86_64-linux-bin.tar.gz --strip-components 1 -C codepeer \
	&& cd codepeer \
	&& ./doinstall /opt/codepeer \
	&& cd /opt/codepeer \
	&& mkdir -p /tmp/codepeer.keep/share/doc/codepeer && mv share/doc/codepeer /tmp/codepeer.keep/share/doc/codepeer \
	&& rm -rf share/doc/* \
	&& rm -rf share/examples/ \
	&& mv /tmp/codepeer.keep/share/doc/codepeer share/doc/codepeer \
	&& rm -rf /tmp/codepeer.keep/ \
	&& rm -rf /tmp/codepeer

FROM gitlab/gitlab-runner AS run
COPY --from=build /opt/codepeer /opt/codepeer
ENV PATH "/opt/codepeer/bin:${PATH}"
