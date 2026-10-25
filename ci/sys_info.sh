#!/bin/bash

# Display some information about the running system to
# help troubleshoot CI errors

echo "##### System prefs #####"
qubes-prefs
echo
qvm-prefs dom0
echo
qvm-features dom0
default_mgmt_dispvm="$(qubes-prefs management_dispvm)"

echo "##### Installed Qubes #####"
qvm-ls

echo
echo "##### ${default_mgmt_dispvm} prefs #####"

qvm-prefs "$default_mgmt_dispvm"
echo
qvm-features "$default_mgmt_dispvm"
default_mgmt_dispvm_template="$(qvm-prefs "$default_mgmt_dispvm" template)"


echo
echo "##### ${default_mgmt_dispvm_template} prefs #####"
qvm-prefs "$default_mgmt_dispvm_template"
echo
qvm-features "$default_mgmt_dispvm_template"

fedora_ver="$(echo "$default_mgmt_dispvm_template" | cut -d- -f2)"
echo
echo "Fedora vers: ${fedora_ver}"
