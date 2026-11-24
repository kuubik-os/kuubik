%post --nochroot --erroronfail --log=/tmp/anaconda_custom_logs/no-quiet-karg.log
# anaconda always adds "rhgb quiet". ostree carries kargs over from these boot entries to new deployments
sed -i -E '/^options /s/ quiet( |$)/\1/g' /mnt/sysimage/boot/loader/entries/ostree-*.conf
grep '^options ' /mnt/sysimage/boot/loader/entries/ostree-*.conf
%end
