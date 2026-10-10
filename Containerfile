ARG FEDORA_VERSION=44
ARG LTS_VERSION=10

FROM scratch AS ctx
COPY build_scripts /

FROM ghcr.io/ublue-os/brew:latest AS brew

FROM scratch AS overrides
COPY system_files/shared /
COPY cosign.pub /etc/pki/containers/kuubik.pub
# pre-built linuxbrew prefix, unpacked on first boot by brew-setup.service
COPY --from=brew /system_files/usr/share/homebrew.tar.zst /usr/share/homebrew.tar.zst
COPY --from=brew /system_files/usr/lib/systemd/system/brew-setup.service /usr/lib/systemd/system/brew-setup.service
COPY --from=brew /system_files/etc/profile.d/brew.sh /etc/profile.d/brew.sh
COPY --from=brew /system_files/etc/profile.d/brew-bash-completion.sh /etc/profile.d/brew-bash-completion.sh
COPY --from=brew /system_files/usr/share/fish/vendor_conf.d/ublue-brew.fish /usr/share/fish/vendor_conf.d/ublue-brew.fish

FROM quay.io/fedora-ostree-desktops/kinoite:${FEDORA_VERSION} AS base
COPY --from=overrides / /
COPY system_files/fedora /
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=tmpfs,dst=/var \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/fedora/10-kernel.sh && \
    /ctx/fedora/20-multimedia.sh && \
    /ctx/fedora/30-debloat.sh && \
    /ctx/fedora/40-packages.sh && \
    /ctx/shared/50-system-config.sh

FROM base AS kuubik
ARG IMAGE_VERSION=""
LABEL org.opencontainers.image.version=${IMAGE_VERSION}
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=tmpfs,dst=/var \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/shared/90-finalize.sh
RUN bootc container lint

FROM base AS kuubik-nvidia
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=tmpfs,dst=/var \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/fedora/60-nvidia.sh
# after the driver install, nvidia packages ship their own 99-nvidia.conf
COPY system_files/nvidia /
ARG IMAGE_VERSION=""
LABEL org.opencontainers.image.version=${IMAGE_VERSION}
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=tmpfs,dst=/var \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/shared/90-finalize.sh
RUN bootc container lint

FROM quay.io/almalinuxorg/atomic-desktop-kde:${LTS_VERSION} AS lts-base
COPY --from=overrides / /
COPY system_files/rhel /
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=tmpfs,dst=/var \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/rhel/10-kernel.sh && \
    /ctx/rhel/20-multimedia.sh && \
    /ctx/rhel/30-debloat.sh && \
    /ctx/rhel/40-packages.sh && \
    /ctx/shared/50-system-config.sh

FROM lts-base AS kuubik-lts
ARG IMAGE_VERSION=""
LABEL org.opencontainers.image.version=${IMAGE_VERSION}
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=tmpfs,dst=/var \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/shared/90-finalize.sh
RUN bootc container lint

FROM lts-base AS kuubik-lts-nvidia
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=tmpfs,dst=/var \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/rhel/60-nvidia.sh
# after the driver install, nvidia packages ship their own 99-nvidia.conf
COPY system_files/nvidia /
ARG IMAGE_VERSION=""
LABEL org.opencontainers.image.version=${IMAGE_VERSION}
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=tmpfs,dst=/var \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/shared/90-finalize.sh
RUN bootc container lint
