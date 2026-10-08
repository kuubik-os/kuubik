ARG IMAGE
FROM ${IMAGE}
RUN systemctl enable sshd.service && \
    echo "test_user ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/test_user && \
    chmod 0440 /etc/sudoers.d/test_user
