#!/bin/bash

ip l
/usr/bin/ethtool -k lo
echo $?
/usr/bin/ethtool -k eth0
echo $?

ethtool --debug 0xff -k lo
echo $?

ls -lah /usr/bin/ethtool
rpm -qf /usr/bin/ethtool

cat /usr/bin/ethtool


rpm -q ethtool
echo $?


which ethtool

dnf install -y ethtool
echo $?

/usr/bin/ethtool -k lo
echo $?
/usr/bin/ethtool -k eth0
echo $?

dmesg
journalctl -e

ethtool --debug 0xff -k lo
