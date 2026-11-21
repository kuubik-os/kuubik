# kuubik network install on top of the fedora netinstall iso, which boots with secure boot on.
# disk, user, locale and network are left to the installer ui. @REGISTRY@ is set by build_netinst.yml,
# post-scripts from installer/system_files/usr/share/anaconda/post-scripts are appended after this.
# the flavor comes from kuubik.image=<image> on the kernel cmdline, set by the iso boot menu.

%pre
mkdir -p /tmp/anaconda_custom_logs
image=kuubik
for arg in $(cat /proc/cmdline); do
	case "$arg" in kuubik.image=*) image="${arg#kuubik.image=}" ;; esac
done
echo "ostreecontainer --url=@REGISTRY@/${image}:latest --transport=registry --no-signature-verification" >/tmp/kuubik-image.ks
%end

%include /tmp/kuubik-image.ks

# point installed system at signed registry image for updates
%post --erroronfail --log=/tmp/anaconda_custom_logs/bootc-switch.log
image=kuubik
for arg in $(cat /proc/cmdline); do
	case "$arg" in kuubik.image=*) image="${arg#kuubik.image=}" ;; esac
done
bootc switch --mutate-in-place --enforce-container-sigpolicy --transport registry "@REGISTRY@/${image}:latest"
%end
