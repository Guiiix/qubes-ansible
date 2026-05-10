#!/usr/bin/python3
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

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule


OCUMENTATION = r"""
---
module: qube_facts

short_description: Retrieve information about a qube.

description:
    - Retrieve properties, features, services and the state of a qube.

version_added: "1.0.0"

requirements:
  - qubesadmin
"""


RETURN = r"""
ansible_facts:
    type: dict
    returned: always
    contains:
        qubes_facts:
            description: Facts related to the qube
            type: dict
            returned: always
            contains:
                name:
                    description: The qube name
                    type: str
                    returned: always
                state:
                    description: The qube state
                    type: str
                    returned: always
                properties:
                    description: Contains the qube available properties and their value
                    type: dict
                    returned: always
                default_properties:
                    description: Contains a boolean indicating if the property is the default value
                    type: dict
                    returned: always
                features:
                    description: The qube features
                    type: dict
                    returned: always
                services:
                    description: Qubes services (false => service is disabled, true => service is enabled)
                    type: dict
                    returned: always
"""

EXAMPLES = r"""
# Use returned data directly
- qubesos.core.qube_facts:
    name: untrusted
  register: untrusted_qube_facts
- ansible.builtin.debug:
    var: untrusted_qube_facts.ansible_facts.qubes_facts

# Install a package on appvms templates
- hosts: appvms
  become: false
  gather_facts: false
  connection: ansible.builtin.local
  strategy: ansible.builtin.linear
  tasks:
    - qubesos.core.qube_facts:
        name: "{{ inventory_hostname }}"
      delegate_to: localhost
    - ansible.builtin.add_host:
        group: templates_to_manage
        name: "{{ qubes_facts.properties.template }}"
- hosts: templates_to_manage
  become: true
  gather_facts: false
  connection: qubesos.core.qube
  strategy: qubesos.security.qubes_proxy
  tasks:
    - ansible.builtin.package:
        name: nano
"""


import qubesadmin


def get_qube_properties(qube):
    props = {}
    default_props = {}
    properties = qube.property_list()
    for prop in sorted(properties):
        try:
            props[prop] = str(getattr(qube, prop))
            default_props[prop] = qube.property_is_default(prop)
        except AttributeError:
            continue
    return props, default_props


def core(module):
    app = qubesadmin.Qubes()
    try:
        qube = app.domains[module.params["name"]]
    except KeyError as e:
        module.fail_json(msg=f"Qube {e} not found")

    props, default_props = get_qube_properties(qube)
    module.exit_json(
        changed=False,
        ansible_facts={
            "qubes_facts": {
                "name": qube.name,
                "state": qube.get_power_state().lower(),
                "properties": props,
                "default_properties": default_props,
                "features": {
                    feat: qube.features[feat] for feat in qube.features
                },
                "services": {
                    feat[len("service.")]: bool(qube.features[feat])
                    for feat in qube.features
                    if feat.startswith("service.")
                },
            },
        },
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type="str"),
        )
    )

    core(module)


if __name__ == "__main__":
    main()
