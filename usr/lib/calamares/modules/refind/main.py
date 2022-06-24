#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# === This file is part of Calamares - <https://calamares.io> ===
#
#   SPDX-FileCopyrightText: 2021 Anke Boersma <demm@kaosx.us>
#   SPDX-License-Identifier: GPL-3.0-or-later
#
#   Calamares is Free Software: see the License-Identifier above.
#

import libcalamares

import os
import subprocess

from libcalamares.utils import check_target_env_call

import gettext
_ = gettext.translation("calamares-python",
                        localedir=libcalamares.utils.gettext_path(),
                        languages=libcalamares.utils.gettext_languages(),
                        fallback=True).gettext


def pretty_name():
    return _("Install rEFInd.")


def get_uuid():
    partitions = libcalamares.globalstorage.value("partitions")
    for partition in partitions:
        if partition["mountPoint"] == "/":
            libcalamares.utils.debug(partition["uuid"])
            return partition["uuid"]
    return None

def get_zfs_root():
    """
    Looks in global storage to find the zfs root
    :return: A string containing the path to the zfs root or None if it is not found
    """

    zfs = libcalamares.globalstorage.value("zfsDatasets")

    if not zfs:
        libcalamares.utils.warning("Failed to locate zfs dataset list")
        return None

    # Find the root dataset
    for dataset in zfs:
        try:
            if dataset["mountpoint"] == "/":
                return dataset["zpool"] + "/" + dataset["dsName"]
        except KeyError:
            # This should be impossible
            libcalamares.utils.warning("Internal error handling zfs dataset")
            raise

    return None

def is_btrfs_root(partition):
    """ Returns True if the partition object refers to a btrfs root filesystem
    :param partition: A partition map from global storage
    :return: True if btrfs and root, False otherwise
    """
    return partition["mountPoint"] == "/" and partition["fs"] == "btrfs"

def is_zfs_root(partition):
    """ Returns True if the partition object refers to a zfs root filesystem
    :param partition: A partition map from global storage
    :return: True if zfs and root, False otherwise
    """
    return partition["mountPoint"] == "/" and partition["fs"] == "zfs"

def update_conf(uuid, conf_path):
    """
    Updates the created rEFInd configuration file based on given parameters.
    """
    partitions = libcalamares.globalstorage.value("partitions")

    kernel_params = ["quiet", "systemd.show_status=0"]
    swap = None  # Partition UUID
    swap_luks = None  # LUKS name
    cryptdevice_params = []
    btrfs_params = ""


    for partition in partitions:
        # systemd-boot with a BTRFS root filesystem needs to be told abouut the root subvolume.
        # If a btrfs root subvolume wasn't set, it means the root is directly on the partition
        # and this option isn't needed
        if is_btrfs_root(partition):
            btrfs_root_subvolume = libcalamares.globalstorage.value("btrfsRootSubvolume")
            if btrfs_root_subvolume:
                kernel_params.append("rootflags=subvol=" + btrfs_root_subvolume)

        # zfs needs to be told the location of the root dataset
        if is_zfs_root(partition):
            zfs_root_path = get_zfs_root()
            if zfs_root_path is not None:
                kernel_params.append("zfs=" + zfs_root_path)
            else:
                # Something is really broken if we get to this point
                libcalamares.utils.warning("Internal error handling zfs dataset")
                raise Exception("Internal zfs data missing, please contact your distribution")


    if cryptdevice_params:
        kernel_params.extend(cryptdevice_params)
    else:
        kernel_params.append("root=UUID={!s}".format(uuid))

    if swap:
        kernel_params.append("resume=UUID={!s}".format(swap))
    if swap_luks:
        kernel_params.append("resume=/dev/mapper/{!s}".format(swap_luks))
    if btrfs_params:
        kernel_params.append(btrfs_params)

    with open(conf_path, "r") as refind_file:
        filedata = [x.strip() for x in refind_file.readlines()]

    with open(conf_path, 'w') as refind_file:
        for line in filedata:
            if line.startswith('"Boot with standard options"'):
                line = '"Boot with standard options"    "rw {!s}"'.format(" ".join(kernel_params))
            refind_file.write(line + "\n")


def efi_partitions(efi_boot_path):
    """
    The (one) partition mounted on @p efi_boot_path, or an empty list.
    """
    return [p for p in libcalamares.globalstorage.value("partitions") if p["mountPoint"] == efi_boot_path]


def install_refind():
    install_path = libcalamares.globalstorage.value("rootMountPoint")
    uuid = get_uuid()
    conf_path = os.path.join(install_path, "boot/refind_linux.conf")

    # TODO: some distro's use /boot/efi , so maybe this needs to
    #       become configurable (that depends on what rEFInd likes).
    efi_boot_path = "/boot"

    # Might not have a /boot configured in the system at all; warn and don't operate
    if not efi_partitions(efi_boot_path):
        libcalamares.utils.warning("No partition mounted on {!s}".format(efi_boot_path))
        # This isn't returned as an error, but the installation
        # probably won't boot because no bootloader was installed.
        return None

    subprocess.call(
        ["refind-install", "--root", "{!s}".format(install_path)])
    update_conf(uuid, conf_path)


def run():
    """
    Optional entry for when providing bootloader choices.
    Values taken from a packagechooser instance.
    Module won't run, if value not present.
    """
    bootchoice = libcalamares.globalstorage.value("packagechooser_bootchoice")

    if bootchoice == "refind":
        return install_refind()
