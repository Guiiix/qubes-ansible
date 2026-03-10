#!/usr/bin/python3
# Copyright (c) 2017 Ansible Project
# Copyright (C) 2018 Kushal Das
# Copyright (C) 2025 Frédéric Pierret (fepitre) <frederic@invisiblethingslab.com>
# Copyright (C) 2026 Guillaume Chinal (guiiix) <guiiix@invisiblethingslab.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.qubesos.core.plugins.module_utils.qubes_virt import (
    QubesHelper,
)


def core(module):
    helper = QubesHelper(module)
    module.exit_json(
        ansible_facts={
            "pci_net": sorted(helper.find_devices_of_class("02")),
            "pci_usb": sorted(helper.find_devices_of_class("0c03")),
            "pci_audio": sorted(
                list(helper.find_devices_of_class("0401"))
                + list(helper.find_devices_of_class("0403"))
            ),
        }
    )


def main():
    module = AnsibleModule(argument_spec=dict())

    try:
        import qubesadmin
        import qubesadmin.exc
        from qubesadmin.device_protocol import DeviceAssignment
    except ImportError:
        qubesadmin = None

    if qubesadmin is None:
        module.fail_json("Failed to import the qubesadmin module.")

    core(module)


if __name__ == "__main__":
    main()
