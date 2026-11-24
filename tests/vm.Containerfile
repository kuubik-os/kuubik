ARG IMAGE
FROM ${IMAGE}
# autologin so the tests see a real plasma session, not the login screen.
RUN systemctl enable sshd.service && \
    echo "test_user ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/test_user && \
    chmod 0440 /etc/sudoers.d/test_user && \
    mkdir -p /etc/plasmalogin.conf.d && \
    printf '%s\n' '[Autologin]' 'User=test_user' 'Session=plasma' >/etc/plasmalogin.conf.d/zz-test-autologin.conf
