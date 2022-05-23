#!/bin/bash

#Documentation: https://openwrt.org/docs/guide-user/additional-software/imagebuilder

OUTPUT="$(pwd)/images"
BUILDER="https://downloads.openwrt.org/releases/21.02.3/targets/bcm27xx/bcm2708/openwrt-imagebuilder-21.02.3-bcm27xx-bcm2708.Linux-x86_64.tar.xz"
KERNEL_PARTSIZE=$((4*1024)) #Kernel-Partitionsize in MB
ROOTFS_PARTSIZE=$((10*1024)) #Rootfs-Partitionsize in MB

# download image builder
if [ ! -f "${BUILDER##*/}" ]; then
	wget "$BUILDER"
	tar xJvf "${BUILDER##*/}"
fi

mkdir "$OUTPUT"
cd openwrt-*/

#copy MQTT_GPIO.py script to folder "files", it will be included into the final image
mkdir -p files/root
cp ../../MQTT_GPIO.py files/root/MQTT_GPIO.py

#script to create Debian chroot at boot
cat << "EOF" > files/etc/rc.local

MYLOG="logger -t 🪁 "

while true; do
	echo "waiting for internet..." | $MYLOG
	if [ $(ping -c 1 "$(ip route | awk '/default/ { print $3 }')" > /dev/null; echo $?) -eq 0 ]; then
		echo "Default GW is online, proceed" | $MYLOG
		break
	fi
	sleep 1
done

THIS_CHROOT="/root/mychroot"

#chroot is not there, build it
if [ ! -d "$THIS_CHROOT" ]; then
  debootstrap --arch armel bullseye "$THIS_CHROOT"
  chroot "$THIS_CHROOT" /bin/bash -c "apt install -y python3-rpi.gpio python3-paho-mqtt"
fi

# everything mounted?
mount | grep "$THIS_CHROOT" > /dev/null
if [ $? -ne 0 ]; then
  mount -t proc proc     "$THIS_CHROOT/proc/"
  mount -t sysfs sys     "$THIS_CHROOT/sys/"
  mount -o bind /dev     "$THIS_CHROOT/dev/"
  mount -o bind /dev/pts "$THIS_CHROOT/dev/pts"

  touch "$THIS_CHROOT/root/MQTT_GPIO.py"
  mount -o bind /root/MQTT_GPIO.py "$THIS_CHROOT/root/MQTT_GPIO.py"
fi

while true; do
	chroot "$THIS_CHROOT" /bin/bash -c "python3 /root/MQTT_GPIO.py"
	sleep 1
done &

exit 0
EOF

# clean previous images
make clean

#adjust partition sizes
sed -i "s/CONFIG_TARGET_KERNEL_PARTSIZE=.*/CONFIG_TARGET_KERNEL_PARTSIZE=$KERNEL_PARTSIZE/g" .config
sed -i "s/CONFIG_TARGET_ROOTFS_PARTSIZE=.*/CONFIG_TARGET_ROOTFS_PARTSIZE=$ROOTFS_PARTSIZE/g" .config

# Packages are added if no prefix is given, '-packagename' does not integrate/removes a package
make image  PROFILE="rpi" \
           PACKAGES="kmod-rt2800-usb rt2800-usb-firmware kmod-cfg80211 kmod-lib80211 kmod-mac80211 kmod-rtl8192cu kmod-rtl8xxxu \
                     luci-base luci-ssl luci-mod-admin-full luci-theme-bootstrap \
                     collectd-mod-ping collectd-mod-wireless luci-app-statistics pingcheck collectd-mod-uptime \
                     kmod-usb-storage kmod-usb-ohci kmod-usb-uhci e2fsprogs fdisk resize2fs \
                     htop debootstrap debian-archive-keyring gpgv2 gcc python3-pip block-mount \
                     openssh-sftp-server" \
            BIN_DIR="$OUTPUT" FILES="files"
