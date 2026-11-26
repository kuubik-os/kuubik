ARG IMAGE
FROM ${IMAGE}
# what the image is expected to be, so a broken image can't pass by looking like another flavor
ARG KUUBIK_FLAVOR
ARG KUUBIK_EXPECT_SIGNED=0
ARG KUUBIK_IMAGE_VERSION=""
ARG KUUBIK_FEDORA_VERSION=""
# pytest runs inside the image under test, so commands see the image as it ships
RUN dnf5 -y install python3-pytest && dnf5 clean all
COPY tests/podman /tests
# test_30_debloat checks every package this script removes, test_05 that unowned files are ours
COPY build_scripts/30-debloat.sh /tests/data/
COPY system_files /tests/data/system_files
WORKDIR /tests
ENV PYTHONDONTWRITEBYTECODE=1 \
    KUUBIK_FLAVOR=${KUUBIK_FLAVOR} \
    KUUBIK_EXPECT_SIGNED=${KUUBIK_EXPECT_SIGNED} \
    KUUBIK_IMAGE_VERSION=${KUUBIK_IMAGE_VERSION} \
    KUUBIK_FEDORA_VERSION=${KUUBIK_FEDORA_VERSION}
ENTRYPOINT ["python3", "-m", "pytest", "-p", "no:cacheprovider"]
CMD ["--junitxml=/test-results/podman.xml", "--durations=0", "--durations-min=1"]
