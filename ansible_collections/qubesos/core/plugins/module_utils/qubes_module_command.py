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

DOCUMENTATION = """
---
module: qubesos.core.command
short_description: Non-idempotent command to execute on the VM.
description:
    - This module allows to execute commands against Qubes
    - The commands are not idempotent. Use qubesos.core.qube to manage a Qube
version_added: "2.8"
options:
  command:
    description:
      - Non-idempotent command to execute on the VM.
      - "Available commands include:"
      - " - C(create): Create a new VM."
      - " - C(createinventory): Generate an inventory file for Qubes OS VMs."
      - " - C(destroy): Force shutdown of a VM."
      - " - C(get_states): Get the states of all VMs."
      - " - C(info): Retrieve information about all VMs."
      - " - C(list_vms): List VMs filtered by state."
      - " - C(pause): Pause a running VM."
      - " - C(remove): Remove a VM"
      - " - C(removetags): Remove specified tags from a VM."
      - " - C(shutdown): Gracefully shut down a VM."
      - " - C(status): Retrieve the current state of a VM."
      - " - C(start): Start a VM."
      - " - C(stop): Stop a VM."
      - " - C(unpause): Resume a paused VM."
  label:
    description:
      - Label (or color) assigned to the VM. For more details, see the Qubes OS Glossary.
    default: "red"
  name:
    description:
      - Name of the Qubes OS virtual machine to manage.
      - This parameter is required for operations targeting a specific VM. It can also be specified as C(guest).
  netvm:
    description:
      - Name of the NetVM to assign to assign to the qubes (valid for create only)
      - For more details, see the Qubes OS Glossary.
  state:
    description:
      - Only used for list_vms command - Get VM having the specified state.
    choices: [running, paused, shutdown]
  tags:
    description:
      - A list of tags to apply to the VM.
      - Tags are used within Qubes OS for VM categorization.
    type: list
    default: []
  template:
    description:
      - Name of the template VM to use when creating or cloning a VM.
      - For AppVMs, this is the base TemplateVM from which the VM is derived.
    default: "default"
  vmtype:
    description:
      - The type of VM to manage.
      - Typical values include C(AppVM), C(StandaloneVM), C(TemplateVM) and C(DispVM).
      - Refer to the Qubes OS Glossary for definitions of these terms.
    default: "AppVM"

requirements:
  - python >= 3.12
  - qubesadmin
  - jinja2

author:
  - Kushal Das
  - Frédéric Pierret
  - Guillaume Chinal
"""

from contextlib import suppress
from enum import Enum, auto
from jinja2 import Template
from typing import Optional
from functools import wraps

from ansible_collections.qubesos.core.plugins.module_utils.qubes_helper import (
    QubesHelper,
)

from ansible.module_utils.basic import AnsibleModule

from qubesadmin.exc import (
    QubesTagNotFoundError,
)


class CommandType(Enum):
    HOST = auto()
    VM = auto()


# This dictionary is automatically populated by the command registered with
# the decorator @register_command
SUPPORTED_COMMANDS = {}


def get_module_param(module, param, required=True):
    param_value = module.params.get(param, None)
    if param_value is None and required:
        module.fail_json(msg=f"Expected '{param}' parameter to be specified")
    return param_value


def register_command(
    command_name: str, command_type: Optional[CommandType] = None
):
    """
    Populates SUPPORTED_COMMANDS and injecting guest function parameter
    for VM commands
    """

    def decorator(func):
        @wraps(func)
        def wrapper(module, qubes_virt: QubesHelper):
            if wrapper.__command_type__ == CommandType.VM:
                guest = get_module_param(module, "name")
                return func(module, qubes_virt, guest)
            return func(module, qubes_virt)

        SUPPORTED_COMMANDS[command_name] = wrapper
        wrapper.__command_type__ = command_type

        return func

    return decorator


@register_command("createinventory", CommandType.HOST)
def create_inventory(module, qubes_virt: QubesHelper):
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
    result = qubes_virt.all_vms()
    template = Template(template_str)
    res = template.render(result=result)
    with open("inventory", "w") as fobj:
        fobj.write(res)
    module.exit_json(status="successful")


@register_command("create", CommandType.VM)
def create_qube(module, qubes_virt: QubesHelper, guest: str):
    try:
        qubes_virt.get_vm(guest)
        module.exit_json(changed=False)
    except KeyError:
        qubes_virt.create_or_clone(
            guest,
            get_module_param(module, "vmtype"),
            get_module_param(module, "label", False) or "red",
            get_module_param(module, "template", False),
            get_module_param(module, "netvm", False),
        )

        module.exit_json(changed=True, created=guest)


@register_command("get_states", CommandType.HOST)
def get_states(module, qubes_virt: QubesHelper):
    module.exit_json(states=qubes_virt.get_states())


@register_command("list_vms", CommandType.HOST)
def list_vms(module, qubes_virt: QubesHelper):
    module.exit_json(
        list_vms=qubes_virt.list_vms(get_module_param(module, "state"))
    )


@register_command("removetags", CommandType.VM)
def remove_tags(module, qubes_virt: QubesHelper, guest: str):
    vm = qubes_virt.get_vm(guest)
    changed = False
    tags = get_module_param(module, "tags")

    with suppress(QubesTagNotFoundError):
        for tag in tags:
            vm.tags.remove(tag)
            changed = True

    module.exit_json(changed=changed)


@register_command("destroy", CommandType.VM)
@register_command("info", CommandType.HOST)
@register_command("pause", CommandType.VM)
@register_command("remove", CommandType.VM)
@register_command("shutdown", CommandType.VM)
@register_command("start", CommandType.VM)
@register_command("status", CommandType.VM)
@register_command("unpause", CommandType.VM)
def generic_command(module, qubes_virt, guest: Optional[str] = None):
    command = get_module_param(module, "command")
    args = [] if guest is None else [guest]
    res = getattr(qubes_virt, command)(*args)
    if not isinstance(res, dict):
        res = {command: res}
    if "changed" not in res:
        res["changed"] = True
    module.exit_json(**res)


def core(module):
    command = get_module_param(module, "command")

    command_func = SUPPORTED_COMMANDS.get(command)
    if command_func is None:
        module.fail_json(msg=f"Command '{command}' not recognized")

    qubes_virt = QubesHelper(module)

    command_func(module, qubes_virt)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            command=dict(type="str", choices=list(SUPPORTED_COMMANDS.keys())),
            label=dict(type="str", default="red"),
            name=dict(type="str", aliases=["guest"]),
            netvm=dict(type="str", default=None),
            state=dict(
                type="str",
                choices=[
                    "paused",
                    "running",
                    "shutdown",
                ],
            ),
            tags=dict(type="list", default=[]),
            template=dict(type="str", default=None),
            vmtype=dict(type="str", default="AppVM"),
        ),
    )

    core(module)


if __name__ == "__main__":
    main()
