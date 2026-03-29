from ansible_collections.qubesos.core.plugins.module_utils.qubes_module_host_devices_facts import (
    main,
)

DOCUMENTATION = r"""
---
module: host_devices_facts

short_description: Retrieve information about the host devices.

description:
    - Retrieve information related to the host devices
    - You can use the gathered facts to assign devices to a qube using
      qubesos.core.qube.

version_added: "1.0.0"

requirements:
  - qubesadmin
"""


RETURN = r"""
ansible_facts:
    description: Facts related to host devices
    type: dict
    returned: always
    contains:
        pci_net:
            description: Network devices
            type: list
            returned: always
        pci_usb:
            description: USB devices
            type: list
            returned: always
        pci_audio:
            description: Audio devices
            type: list
            returned: always
"""

EXAMPLES = r"""
- qubesos.core.host_devices_facts:
- ansible.builtin.debug:
    var: ansible_facts.pci_net
"""


if __name__ == "__main__":
    main()
