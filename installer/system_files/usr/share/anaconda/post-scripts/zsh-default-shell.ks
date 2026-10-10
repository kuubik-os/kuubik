%post --erroronfail --log=/tmp/anaconda_custom_logs/zsh-default-shell.log
# users made by anaconda already exist here, switch them and make zsh the default for new ones
sed -i 's|^SHELL=.*|SHELL=/usr/bin/zsh|' /etc/default/useradd
getent passwd | awk -F: '$3 >= 1000 && $3 < 60000 && $7 ~ /\/bash$/ {print $1}' | while read -r user; do
	usermod --shell /usr/bin/zsh "$user"
done
%end
