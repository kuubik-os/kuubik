%post --nochroot --erroronfail --log=/tmp/anaconda_custom_logs/verbose-boot.log
# anaconda always adds "rhgb quiet", drop both to show the full boot process instead of the splash.
# ostree carries kargs over from these boot entries to new deployments
sed -i -E '/^options /{s/ rhgb( |$)/\1/g;s/ quiet( |$)/\1/g}' /mnt/sysimage/boot/loader/entries/ostree-*.conf
grep '^options ' /mnt/sysimage/boot/loader/entries/ostree-*.conf
%end
