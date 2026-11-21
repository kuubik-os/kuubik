# kuubik network install on top of the fedora netinstall iso, which boots with secure boot on.
# disk, user, locale and network are left to the installer ui. @IMAGE@ is set by build_netinst.yml,
# post-scripts from installer/system_files/usr/share/anaconda/post-scripts are appended after this.

ostreecontainer --url=@IMAGE@ --transport=registry --no-signature-verification

%pre
mkdir -p /tmp/anaconda_custom_logs
%end

# point installed system at signed registry image for updates
%post --erroronfail --log=/tmp/anaconda_custom_logs/bootc-switch.log
bootc switch --mutate-in-place --enforce-container-sigpolicy --transport registry @IMAGE@
%end
