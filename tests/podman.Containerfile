ARG IMAGE
FROM ${IMAGE}
# pytest runs inside the image under test, so commands see the image as it ships
RUN dnf5 -y install python3-pytest && dnf5 clean all
COPY tests/podman /tests
WORKDIR /tests
ENV PYTHONDONTWRITEBYTECODE=1
ENTRYPOINT ["python3", "-m", "pytest", "-p", "no:cacheprovider"]
CMD ["--junitxml=/test-results/podman.xml", "--durations=0", "--durations-min=1"]
