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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: qubesos
short_description: Manage Qubes OS virtual machines
description:
    - This module manages Qubes OS virtual machines using the qubesadmin API.
    - It supports VM creation, state management, and various operations such as starting, pausing, shutting down, and more.
    - For definitions of Qubes OS terminology (e.g. AppVM, TemplateVM, StandaloneVM, DispVM), please refer to the Qubes OS Glossary at https://www.qubes-os.org/doc/glossary/.
version_added: "2.8"
options:
  name:
    description:
      - Name of the Qubes OS virtual machine to manage.
      - This parameter is required for operations targeting a specific VM. It can also be specified as C(guest).
  state:
    description:
      - Desired state of the VM.
      - When set to C(present), ensures the VM is defined.
      - When set to C(running), ensures the VM is started.
      - When set to C(shutdown), ensures the VM is stopped.
      - When set to C(destroyed), forces the VM to shut down.
      - When set to C(restarted), shuts the VM down then starts it again.
      - When set to C(pause), pauses a running VM.
      - When set to C(absent), removes the VM definition.
    choices: [ present, running, shutdown, destroyed, restarted, pause, absent ]
  wait:
    description:
      - If C(true), block until the VM has fully halted before returning.
      - Only applies to C(shutdown) and C(restarted) states.
    type: bool
    default: false
  command:
    description:
      - Non-idempotent command to execute on the VM.
      - "Available commands include:"
      - " - C(create): Create a new VM."
      - " - C(destroy): Force shutdown of a VM."
      - " - C(pause): Pause a running VM."
      - " - C(shutdown): Gracefully shut down a VM."
      - " - C(status): Retrieve the current state of a VM."
      - " - C(start): Start a VM."
      - " - C(stop): Stop a VM."
      - " - C(unpause): Resume a paused VM."
      - " - C(removetags): Remove specified tags from a VM."
      - " - C(info): Retrieve information about all VMs."
      - " - C(list_vms): List VMs filtered by state."
      - " - C(get_states): Get the states of all VMs."
      - " - C(createinventory): Generate an inventory file for Qubes OS VMs."
  label:
    description:
      - Label (or color) assigned to the VM. For more details, see the Qubes OS Glossary.
    default: "red"
  vmtype:
    description:
      - The type of VM to manage.
      - Typical values include C(AppVM), C(StandaloneVM), C(TemplateVM) and C(DispVM).
      - Refer to the Qubes OS Glossary for definitions of these terms.
    default: "AppVM"
  template:
    description:
      - Name of the template VM to use when creating or cloning a VM.
      - For AppVMs, this is the base TemplateVM from which the VM is derived.
    default: "default"
  properties:
    description:
      - A dictionary of VM properties to set.
      - "Valid keys include:"
      - " - autostart (bool)"
      - " - debug (bool)"
      - " - include_in_backups (bool)"
      - " - kernel (str)"
      - " - kernelopts (str)"
      - " - label (str)"
      - " - maxmem (int)"
      - " - memory (int)"
      - " - provides_network (bool)"
      - " - netvm (str)"
      - " - default_dispvm (str)"
      - " - management_dispvm (str)"
      - " - default_user (str)"
      - " - guivm (str)"
      - " - audiovm (str)"
      - " - ip (str)"
      - " - ip6 (str)"
      - " - mac (str)"
      - " - qrexec_timeout (int)"
      - " - shutdown_timeout (int)"
      - " - template (str)"
      - " - template_for_dispvms (bool)"
      - " - vcpus (int)"
      - " - virt_mode (str)"
      - " - features (dict)"
      - " - services (list)"
      - " - volumes (list of dict that must include both 'name' and 'size')"
    default: {}
  features:
    description:
      - A dictionary of VM features to set (or remove). No value for removing.
  tags:
    description:
      - A list of tags to apply to the VM.
      - Tags are used within Qubes OS for VM categorization.
    type: list
    default: []
  devices:
    description:
      - Device assignment configuration for the VM.
      - "Supported usage patterns:"
      - "1. A list (default _strict_ mode) device specs (strings or dicts). The VM's assigned devices will be exactly those listed, removing any others."
      - "2. A dictionary:"
      - " - strategy (str): assignment strategy to use.  "
      - "    - C(strict) (default): enforce exact match of assigned devices to C(items).  "
      - "    - C(append): add only new devices in C(items), leaving existing assignments intact."
      - " - items (list): list of device specs (strings or dicts) to apply under the chosen strategy."
      - "Device spec formats:"
      - " - string: `<devclass>:<backend_domain>:<port_id>[:<dev_id>]` (e.g. C(pci:dom0:5), C(block:dom0:vdb))"
      - " - dict:"
      - "    - device (str, required): the string spec as above."
      - "    - mode (str, optional):"
      - "       - For PCI devices defaults to C(required)."
      - "       - For other classes defaults to C(auto-attach)."
      - "    - options (dict, optional): extra Qubes device flags to pass when attaching."
    type: raw
    default: []
  notes:
    description:
      - Notes and comments (up to 256KB of clear text), For user reference only

requirements:
  - python >= 3.12
  - qubesadmin
  - jinja2
author:
  - Kushal Das
  - Frédéric Pierret
"""

from ansible_collections.qubesos.core.plugins.module_utils.qubes_virt import (
    QubesHelper,
    VIRT_FAILED,
    VIRT_SUCCESS,
)

import traceback


try:
    import qubesadmin
    import qubesadmin.events.utils
    from qubesadmin.exc import (
        QubesVMNotStartedError,
        QubesTagNotFoundError,
        QubesVMError,
    )
    from qubesadmin.device_protocol import (
        VirtualDevice,
        DeviceAssignment,
        ProtocolError,
    )
except ImportError:
    qubesadmin = None
    QubesVMNotStartedError = None
    QubesTagNotFoundError = None
    QubesVMError = None


from jinja2 import Template
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native


ALL_COMMANDS = []
VM_COMMANDS = [
    "create",
    "destroy",
    "pause",
    "shutdown",
    "remove",
    "status",
    "start",
    "stop",
    "unpause",
    "removetags",
]
HOST_COMMANDS = ["info", "list_vms", "get_states", "createinventory"]
ALL_COMMANDS.extend(VM_COMMANDS)
ALL_COMMANDS.extend(HOST_COMMANDS)

PROPS = {
    "autostart": bool,
    "debug": bool,
    "include_in_backups": bool,
    "kernel": str,
    "kernelopts": str,
    "label": str,
    "maxmem": int,
    "memory": int,
    "provides_network": bool,
    "template": str,
    "template_for_dispvms": bool,
    "vcpus": int,
    "virt_mode": str,
    "default_dispvm": str,
    "management_dispvm": str,
    "default_user": str,
    "guivm": str,
    "audiovm": str,
    "netvm": str,
    "ip": str,
    "ip6": str,
    "mac": str,
    "qrexec_timeout": int,
    "shutdown_timeout": int,
    "features": dict,
    "services": list,
    "volumes": list,
}


def create_inventory(result):
    """
    Creates the inventory file dynamically for QubesOS
    """
    template_str = """[local]
dom0
localhost

[local:vars]
ansible_connection=local

{% if result.AppVM %}
[appvms]
{% for item in result.AppVM %}
{{ item -}}
{% endfor %}

[appvms:vars]
ansible_connection=qubes
{% endif %}

{% if result.TemplateVM %}
[templatevms]
{% for item in result.TemplateVM %}
{{ item -}}
{% endfor %}

[templatevms:vars]
ansible_connection=qubes
{% endif %}

{% if result.StandaloneVM %}
[standalonevms]
{% for item in result.StandaloneVM %}
{{ item -}}
{% endfor %}

[standalonevms:vars]
ansible_connection=qubes
{% endif %}
"""
    template = Template(template_str)
    res = template.render(result=result)
    with open("inventory", "w") as fobj:
        fobj.write(res)


def core(module):
    state = module.params.get("state", None)
    guest = module.params.get("name", None)
    command = module.params.get("command", None)
    vmtype = module.params.get("vmtype", None)
    label = module.params.get("label", "red")
    template = module.params.get("template", None)
    properties = module.params.get("properties", {})
    features = module.params.get("features", {})
    tags = module.params.get("tags", [])
    devices = module.params.get("devices", None)
    notes = module.params.get("notes", None)
    netvm = None
    res = {}
    device_specs = []

    v = QubesVirt(module)

    # gather device facts
    if module.params.get("gather_device_facts", False):
        facts = {
            "pci_net": sorted(v.find_devices_of_class("02")),
            "pci_usb": sorted(v.find_devices_of_class("0c03")),
            "pci_audio": sorted(
                list(v.find_devices_of_class("0401"))
                + list(v.find_devices_of_class("0403"))
            ),
        }
        return VIRT_SUCCESS, {"changed": False, "ansible_facts": facts}

    if state == "present" and guest:
        try:
            vm = v.get_vm(guest)
            vmtype = vm.klass
        except KeyError:
            # Set default vmtype to AppVM if vmtype is not provided
            vmtype = vmtype or "AppVM"
            v.create(guest, vmtype, label, template)

    # properties will only work with state=present
    if properties:
        for key, val in properties.items():
            if key not in PROPS:
                return VIRT_FAILED, {"Invalid property": key}
            if type(val) != PROPS[key]:
                return VIRT_FAILED, {"Invalid property value type": key}

            # Make sure that the netvm exists
            if key == "netvm" and val not in ["*default*", "", "none", "None"]:
                try:
                    vm = v.get_vm(val)
                except KeyError:
                    return VIRT_FAILED, {"Missing netvm": val}
                # Also the vm should provide network
                if not vm.provides_network:
                    return VIRT_FAILED, {"Missing netvm capability": val}
                netvm = vm

            # Make sure volume has both name and value
            if key == "volumes":
                if not isinstance(val, list):
                    return VIRT_FAILED, {"Invalid volumes provided": val}
                for vol in val:
                    try:
                        if "name" not in vol:
                            return VIRT_FAILED, {
                                "Missing name for the volume": vol
                            }
                        if "size" not in vol:
                            return VIRT_FAILED, {
                                "Missing size for the volume": vol
                            }
                        if not vol["name"] in ["root", "private"]:
                            return VIRT_FAILED, {
                                "Wrong volume name": vol["name"]
                            }
                        if vol["name"] == "root" and vmtype not in [
                            "TemplateVM",
                            "StandaloneVM",
                        ]:
                            return VIRT_FAILED, {
                                f"Cannot change root volume size for '{vmtype}'"
                            }
                    except KeyError:
                        return VIRT_FAILED, {"Invalid volume provided": vol}

            # Make sure that the default_dispvm exists
            if key == "default_dispvm":
                try:
                    vm = v.get_vm(val)
                except KeyError:
                    return VIRT_FAILED, {"Missing default_dispvm": val}
                # Also the vm should provide network
                if not vm.template_for_dispvms:
                    return VIRT_FAILED, {"Missing dispvm capability": val}

    if state == "present" and guest and vmtype:
        prop_changed, prop_vals = v.properties(guest, properties)
        # Apply the tags
        tags_changed = []
        if tags:
            tags_changed = v.tags(guest, tags)
        feats_changed = []
        if features:
            feats_changed = v.features(guest, features)
        if devices is not None:
            dev_changed = apply_devices(guest)
        else:
            dev_changed = False
        res = {"changed": prop_changed or dev_changed}
        if tags_changed:
            res["Tags updated"] = tags_changed
        if feats_changed:
            res["Features updated"] = feats_changed
        if prop_changed:
            res["Properties updated"] = prop_vals
        if dev_changed:
            res["Devices updated"] = True
        if notes:
            res["Notes updated"] = v.notes(guest, notes)
        return VIRT_SUCCESS, res

    # notes will only work with state=present
    if notes and state == "present" and guest and vmtype:
        result = v.notes(guest, notes)
        return VIRT_SUCCESS, {"changed": result, "Notes updated": result}

    # features will only work with state=present
    if features and state == "present" and guest and vmtype:
        res = v.features(guest, features)
        return VIRT_SUCCESS, {"changed": bool(res), "Features updated": res}

    # This is without any properties
    if state == "present" and guest:
        try:
            v.get_vm(guest)
            dev_changed = apply_devices(guest)
            res = {"changed": dev_changed}
        except KeyError:
            v.create(guest, vmtype, label, template)
            # Apply the tags
            tags_changed = []
            if tags:
                tags_changed = v.tags(guest, tags)
            apply_devices(guest)
            res = {"changed": True, "created": guest, "devices": devices}
            if tags_changed:
                res["tags"] = tags_changed
        return VIRT_SUCCESS, res

    # list_vms, get_states, createinventory commands
    if state and command == "list_vms":
        res = v.list_vms(state=state)
        if not isinstance(res, dict):
            res = {command: res}
        return VIRT_SUCCESS, res

    if command == "get_states":
        states = v.get_states()
        res = {"states": states}
        return VIRT_SUCCESS, res

    if command == "createinventory":
        result = v.all_vms()
        create_inventory(result)
        return VIRT_SUCCESS, {"status": "successful"}

    # single-command VM operations
    if command:
        if command in VM_COMMANDS:
            if not guest:
                module.fail_json(msg=f"{command} requires 1 argument: guest")
            if command == "create":
                try:
                    v.get_vm(guest)
                except KeyError:
                    v.create(guest, vmtype, label, template, netvm)
                    res = {"changed": True, "created": guest}
                return VIRT_SUCCESS, res
            elif command == "removetags":
                vm = v.get_vm(guest)
                changed = False
                if not tags:
                    return VIRT_FAILED, {"Error": "Missing tag(s) to remove."}
                for tag in tags:
                    try:
                        vm.tags.remove(tag)
                        changed = True
                    except QubesTagNotFoundError:
                        pass
                return VIRT_SUCCESS, {
                    "Message": "Removed the tag(s).",
                    "changed": changed,
                }
            res = getattr(v, command)(guest)
            if not isinstance(res, dict):
                res = {command: res}
            return VIRT_SUCCESS, res
        elif hasattr(v, command):
            res = getattr(v, command)()
            if not isinstance(res, dict):
                res = {command: res}
            return VIRT_SUCCESS, res

        else:
            module.fail_json(msg=f"Command {command} not recognized")

    if state:
        if not guest:
            module.fail_json(msg="State change requires a guest specified")
        current = v.status(guest)
        if state == "running":
            if current == "paused":
                res["changed"] = True
                res["msg"] = v.unpause(guest)
            elif current != "running":
                res["changed"] = True
                res["msg"] = v.start(guest)
        elif state == "shutdown":
            if current != "shutdown":
                res["changed"] = True
                try:
                    v.shutdown(guest, wait=module.params.get("wait", False))
                except RuntimeError as e:
                    module.fail_json(msg=str(e))
        elif state == "restarted":
            res["changed"] = True
            try:
                v.restart(guest, wait=module.params.get("wait", False))
                res["msg"] = "restarted"
            except RuntimeError as e:
                module.fail_json(msg=str(e))
        elif state == "destroyed":
            if current != "shutdown":
                res["changed"] = True
                res["msg"] = v.destroy(guest)
        elif state == "pause":
            if current == "running":
                res["changed"] = True
                res["msg"] = v.pause(guest)
        elif state == "absent":
            if current == "shutdown":
                res["changed"] = True
                res["msg"] = v.remove(guest)
        else:
            module.fail_json(msg="Unexpected state")

        return VIRT_SUCCESS, res

    module.fail_json(msg="Expected state or command parameter to be specified")

    return None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type="str", aliases=["guest"]),
            state=dict(
                type="str",
                choices=[
                    "destroyed",
                    "pause",
                    "running",
                    "shutdown",
                    "restarted",
                    "absent",
                    "present",
                ],
            ),
            wait=dict(type="bool", default=False),
            command=dict(type="str", choices=ALL_COMMANDS),
            label=dict(type="str", default="red"),
            vmtype=dict(type="str", default="AppVM"),
            template=dict(type="str", default=None),
            properties=dict(type="dict", default={}),
            features=dict(type="dict", default={}),
            tags=dict(type="list", default=[]),
            devices=dict(type="raw", default=None),
            notes=dict(type="str", default=None),
            gather_device_facts=dict(type="bool", default=False),
        ),
    )

    module.deprecate(
        "Usage of this module is deprecated and support will be dropped in a "
        "future release. Consider switching to qubes.core.qubes module instead.",
    )

    if not qubesadmin:
        module.fail_json(
            msg="The `qubesos` module is not importable. Check the requirements."
        )

    result = None
    rc = VIRT_SUCCESS
    try:
        rc, result = core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    if rc != 0:  # something went wrong emit the msg
        module.fail_json(rc=rc, msg=result)
    else:
        module.exit_json(**result)


if __name__ == "__main__":
    main()
