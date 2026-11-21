ARG IMAGE
FROM ${IMAGE}
# autologin so the tests see a real plasma session, not the login screen.
# fedora uses plasmalogin, the el base still sddm
RUN systemctl enable sshd.service && \
    echo "test_user ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/test_user && \
    chmod 0440 /etc/sudoers.d/test_user && \
    for d in /etc/plasmalogin.conf.d /etc/sddm.conf.d; do \
        mkdir -p "$d" && \
        printf '%s\n' '[Autologin]' 'User=test_user' 'Session=plasma' >"$d/zz-test-autologin.conf"; \
    done
