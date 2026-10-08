ARG FEDORA_VERSION=44

FROM scratch AS ctx
COPY build_scripts /

FROM ghcr.io/ublue-os/brew:latest AS brew

FROM scratch AS overrides
COPY system_files/base /
COPY cosign.pub /etc/pki/containers/kuubik.pub
# pre-built linuxbrew prefix, unpacked on first boot by brew-setup.service
COPY --from=brew /system_files/usr/share/homebrew.tar.zst /usr/share/homebrew.tar.zst
COPY --from=brew /system_files/usr/lib/systemd/system/brew-setup.service /usr/lib/systemd/system/brew-setup.service
COPY --from=brew /system_files/etc/profile.d/brew.sh /etc/profile.d/brew.sh
COPY --from=brew /system_files/etc/profile.d/brew-bash-completion.sh /etc/profile.d/brew-bash-completion.sh
COPY --from=brew /system_files/usr/share/fish/vendor_conf.d/ublue-brew.fish /usr/share/fish/vendor_conf.d/ublue-brew.fish

FROM quay.io/fedora-ostree-desktops/kinoite:${FEDORA_VERSION} AS base
COPY --from=overrides / /
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=tmpfs,dst=/var \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/10-kernel.sh && \
    /ctx/20-multimedia.sh && \
    /ctx/30-debloat.sh && \
    /ctx/40-packages.sh && \
    /ctx/50-system-config.sh

FROM base AS kuubik
ARG IMAGE_VERSION=""
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=tmpfs,dst=/var \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/90-finalize.sh
RUN bootc container lint

FROM base AS kuubik-nvidia
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=tmpfs,dst=/var \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/60-nvidia.sh
# after the driver install, nvidia packages ship their own 99-nvidia.conf
COPY system_files/nvidia /
ARG IMAGE_VERSION=""
RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=tmpfs,dst=/var \
    --mount=type=tmpfs,dst=/tmp \
    /ctx/90-finalize.sh
RUN bootc container lint
