FROM jlesage/baseimage-gui:ubuntu-24.04-v4.14.0@sha256:e7c54da3446b4c65b6755bf00a874463c640a1f579f25bed99532051e81649ef

ARG IMAGE_VERSION=0.1.0
ARG TARGETPLATFORM

LABEL org.opencontainers.image.title="rapid-photo-web" \
      org.opencontainers.image.description="Rapid Photo Downloader in your browser" \
      org.opencontainers.image.version="${IMAGE_VERSION}"

RUN add-pkg rapid-photo-downloader dbus udisks2 util-linux locales fonts-noto-cjk \
    && sed -i -e 's/^# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' \
              -e 's/^# ko_KR.UTF-8 UTF-8/ko_KR.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen \
    && mkdir -p /input /uploads /output \
    && chown 1000:1000 /uploads /output \
    && set-cont-env APP_NAME "Rapid Photo Downloader" \
    && set-cont-env APP_VERSION "$(dpkg-query -W -f='${Version}' rapid-photo-downloader)" \
    && set-cont-env DOCKER_IMAGE_VERSION "${IMAGE_VERSION}" \
    && set-cont-env DOCKER_IMAGE_PLATFORM "${TARGETPLATFORM}"

# The base recreates passwd/group at startup from these account definitions.
RUN for account in messagebus systemd-network; do \
        mkdir -p "/etc/cont-users.d/${account}" "/etc/cont-groups.d/${account}"; \
        id -u "${account}" > "/etc/cont-users.d/${account}/id"; \
        id -g "${account}" > "/etc/cont-users.d/${account}/gid"; \
        id -g "${account}" > "/etc/cont-groups.d/${account}/id"; \
    done

COPY rootfs/ /

RUN chmod 755 /startapp.sh \
    /etc/cont-init.d/90-rapid-photo-web.sh \
    /etc/services.d/system-dbus/run \
    /etc/services.d/system-dbus/is_ready \
    /usr/local/bin/rapid-photo-web-healthcheck.py

ENV KEEP_APP_RUNNING=1 \
    WEB_TERMINAL=0 \
    WEB_FILE_MANAGER=1 \
    WEB_FILE_MANAGER_ALLOWED_PATHS="/uploads,/output" \
    TZ=Etc/UTC \
    LANG=en_US.UTF-8

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=3 \
    CMD ["/usr/local/bin/rapid-photo-web-healthcheck.py"]
