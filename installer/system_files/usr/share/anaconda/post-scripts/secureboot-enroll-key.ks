%post --erroronfail --log=/tmp/anaconda_custom_logs/secureboot-enroll-key.log
# queue the kuubik mok key, confirmed in mokmanager on first boot with password "kuubik"
if [ ! -d /sys/firmware/efi ]; then
	exit 0
fi
mokutil --timeout -1 || :
# fails when the key is already enrolled
printf '%s\n%s\n' kuubik kuubik | mokutil --import /usr/share/kuubik/secureboot/kuubik.der || :
%end
