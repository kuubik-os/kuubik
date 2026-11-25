%post --erroronfail --log=/tmp/anaconda_custom_logs/fstab-drop-root.log
# the composefs root refuses systemd-remount-fs's remount of "/", which then fails on every boot.
# root is mounted from the root=/rootflags= kargs anyway, bootc installs don't list it either
sed -i -E 's|^([^#[:space:]]+[[:space:]]+/[[:space:]].*)$|# \1|' /etc/fstab
cat /etc/fstab
%end
