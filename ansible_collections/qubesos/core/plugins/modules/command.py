from ansible_collections.qubesos.core.plugins.module_utils.qubes_module_command import (
    main,
)

DOCUMENTATION = r"""
---
module: command

short_description: Run an action in your qubes or in your dom0.

description:
    - This module runs predefined actions in your dom0 or in your qubes.
    - The actions are not idempotent.
version_added: "1.0.0"
options:
    name:
        description:
            - Name of the Qubes OS virtual machine to manage.
            - This parameter is required for operations targeting a specific VM. It can also be specified as C(guest).
    state:
        description:
            - Desired state of the VM.
            - When set to C(running), ensures the VM is started.
            - When set to C(shutdown), ensures the VM is stopped.
            - When set to C(paused), pauses a running VM.
        choices: [ present, running, shutdown, destroyed, restarted, pause, absent ]
    command:
        description:
            - Non-idempotent command to execute in the VM.
            - "Available commands include:"
            - "C(create): Create a new VM."
            - "C(createinventory): Generate an inventory file for Qubes OS VMs."
            - "C(destroy): Force shutdown of a VM."
            - "C(get_states): Get the states of all VMs."
            - "C(info): Retrieve information about all VMs."
            - "C(list_vms): List VMs filtered by state."
            - "C(pause): Pause a running VM."
            - "C(remove): Remove a VM."
            - "C(removetags): Remove specified tags from a VM."
            - "C(shutdown): Gracefully shut down a VM."
            - "C(start): Start a VM."
            - "C(status): Retrieve the current state of a VM."
            - "C(unpause): Resume a paused VM."
        required: true
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
    tags:
        description:
            - A list of tags to apply to the VM.
            - Tags are used within Qubes OS for VM categorization.
        type: list
        default: []

    netvm:
        description:
            - The netvm to set
        type: str
    

requirements:
  - qubesadmin
author:
  - Kushal Das
  - Frédéric Pierret
  - Guillaume Chinal
"""

if __name__ == "__main__":
    main()
