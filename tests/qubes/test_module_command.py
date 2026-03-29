import os
import time

import pytest
import qubesadmin

from ansible_collections.qubesos.core.plugins.module_utils.qubes_module_command import (
    core,
)
from tests.qubes.conftest import qubes, vmname, Module, ModuleExitWithError


def test_unrecognized_command():
    # Create
    fake_module = Module({"command": "foo"})
    try:
        core(fake_module)
    except ModuleExitWithError:
        assert (
            fake_module.returned_data["msg"] == "Command 'foo' not recognized"
        )
    else:
        pytest.fail("Module should have raised an error")


def test_lifecycle_full_create_start_shutdown_remove(qubes, vmname, request):

    request.node.mark_vm_created(vmname)

    # Create
    fake_module = Module(
        {"command": "create", "name": vmname, "vmtype": "AppVM"}
    )
    core(fake_module)
    assert fake_module.returned_data["created"] == vmname
    assert vmname in qubes.domains

    # Start
    core(Module({"command": "start", "name": vmname}))
    vm = qubes.domains[vmname]
    assert vm.is_running()

    # Shutdown
    core(Module({"command": "shutdown", "name": vmname}))
    time.sleep(5)
    assert vm.is_halted()

    # Remove
    core(Module({"command": "remove", "name": vmname}))
    qubes.domains.refresh_cache(force=True)
    assert vmname not in qubes.domains


def test_lifecycle_create_and_absent(qubes, vmname, request):
    request.node.mark_vm_created(vmname)

    # Create
    core(Module({"command": "create", "name": vmname, "vmtype": "AppVM"}))
    assert vmname in qubes.domains

    # Absent
    core(Module({"command": "remove", "name": vmname}))
    qubes.domains.refresh_cache(force=True)
    assert vmname not in qubes.domains


def test_lifecycle_pause_and_resume(qubes, vmname, request):
    request.node.mark_vm_created(vmname)
    core(Module({"command": "create", "name": vmname, "vmtype": "AppVM"}))
    core(Module({"command": "start", "name": vmname}))
    time.sleep(1)

    core(Module({"command": "pause", "name": vmname}))
    assert qubes.domains[vmname].is_paused()

    core(Module({"command": "unpause", "name": vmname}))
    assert qubes.domains[vmname].is_running()

    # Clean up
    core(Module({"command": "destroy", "name": vmname}))
    core(Module({"command": "remove", "name": vmname}))


def test_lifecycle_status_reporting(qubes, vmname, request):
    request.node.mark_vm_created(vmname)
    fake_module = Module({"command": "status", "name": vmname})

    core(Module({"command": "create", "name": vmname, "vmtype": "AppVM"}))
    core(fake_module)
    assert fake_module.returned_data["status"] == "shutdown"

    core(Module({"command": "start", "name": vmname}))
    core(fake_module)
    assert fake_module.returned_data["status"] == "running"

    core(Module({"command": "destroy", "name": vmname}))
    core(fake_module)
    assert fake_module.returned_data["status"] == "shutdown"
    assert qubes.domains[vmname].get_power_state() == "Halted"

    core(Module({"command": "remove", "name": vmname}))


def test_create_clone_vmtype_combinations(qubes, vmname, request):
    request.node.mark_vm_created(vmname)
    request.node.mark_vm_created(f"{vmname}-clone-appvm")
    # request.node.mark_vm_created(f"{vmname}-clone-templatevm")
    # request.node.mark_vm_created(f"{vmname}-clone-standalonevm")

    # Test creating / cloning from AppVM
    core(Module({"command": "create", "name": vmname, "vmtype": "AppVM"}))
    core(
        Module(
            {
                "command": "create",
                "name": f"{vmname}-clone-appvm",
                "template": vmname,
                "vmtype": "AppVM",
            }
        )
    )

    assert f"{vmname}-clone-appvm" in qubes.domains

    # rc, _ = core(Module({"command": "create", "name": f"{vmname}-clone-templatevm", "template": vmname, "vmtype": "TemplateVM"}))
    # assert rc == VIRT_SUCCESS
    # assert f"{vmname}-clone-templatevm" in qubes.domains

    # rc, _ = core(Module({"command": "create", "name": f"{vmname}-clone-standalonevm", "template": vmname, "vmtype": "StandaloneVM"}))
    # assert rc == VIRT_SUCCESS
    # assert f"{vmname}-clone-standalonevm" in qubes.domains

    # Test creating / cloning from TemplateVM
    core(Module({"command": "create", "name": vmname, "vmtype": "TemplateVM"}))
    core(
        Module(
            {
                "command": "create",
                "name": f"{vmname}-clone-appvm",
                "template": vmname,
                "vmtype": "AppVM",
            }
        )
    )

    assert f"{vmname}-clone-appvm" in qubes.domains
    #
    # rc, _ = core(Module({"command": "create", "name": f"{vmname}-clone-templatevm", "template": vmname, "vmtype": "TemplateVM"}))
    #
    # assert rc == VIRT_SUCCESS
    # assert f"{vmname}-clone-templatevm" in qubes.domains
    #
    # rc, _ = core(Module({"command": "create", "name": f"{vmname}-clone-standalonevm", "template": vmname, "vmtype": "StandaloneVM"}))
    #
    # assert rc == VIRT_SUCCESS
    # assert f"{vmname}-clone-standalonevm" in qubes.domains
    #
    # # Test creating / cloning from StandaloneVM
    # core(Module({"command": "create", "name": vmname, "vmtype": "StandaloneVM"}))
    # rc, _ = core(Module({"command": "create", "name": f"{vmname}-clone-appvm", "template": vmname, "vmtype": "AppVM"}))
    # assert rc == VIRT_SUCCESS
    # assert f"{vmname}-clone-appvm" in qubes.domains
    #
    # rc, _ = core(Module({"command": "create", "name": f"{vmname}-clone-templatevm", "template": vmname, "vmtype": "TemplateVM"}))
    # assert rc == VIRT_SUCCESS
    # assert f"{vmname}-clone-templatevm" in qubes.domains
    #
    # rc, _ = core(Module({"command": "create", "name": f"{vmname}-clone-standalonevm", "template": vmname, "vmtype": "StandaloneVM"}))
    # assert rc == VIRT_SUCCESS
    # assert f"{vmname}-clone-standalonevm" in qubes.domains
    #
    # Cleanup
    core(Module({"command": "remove", "name": f"{vmname}-clone-appvm"}))
    # core(Module({"state": "absent", "name": f"{vmname}-clone-templatevm"}))
    # core(Module({"state": "absent", "name": f"{vmname}-clone-standalonevm"}))
    core(Module({"command": "remove", "name": vmname}))


def test_inventory_generation_and_grouping(tmp_path, qubes):
    # Use a temporary directory for inventory
    os.chdir(tmp_path)

    # Create a standalone VM (by default we don't have any)
    core(
        Module(
            {
                "command": "create",
                "name": "teststandalone",
                "vmtype": "StandaloneVM",
                "template": "debian-13-xfce",
            }
        )
    )

    # Collect expected VMs by class
    expected = {}
    for vm in qubes.domains.values():
        if vm.name == "dom0":
            continue
        expected.setdefault(vm.klass, []).append(vm.name)

    # Run createinventory
    fake_module = Module({"command": "createinventory"})
    core(fake_module)
    assert fake_module.returned_data["status"] == "successful"

    inv_file = tmp_path / "inventory"
    assert inv_file.exists()
    lines = inv_file.read_text().splitlines()

    # Helper to extract section values
    def section(name):
        start = lines.index(f"[{name}]") + 1
        # find next section header
        for i, line in enumerate(lines[start:], start=start):
            if line.startswith("["):
                end = i
                break
        else:
            end = len(lines)
        return [l for l in lines[start:end] if l.strip()]

    appvms = section("appvms")
    templatevms = section("templatevms")
    standalonevms = section("standalonevms")

    assert set(appvms) == set(expected.get("AppVM", []))
    assert set(templatevms) == set(expected.get("TemplateVM", []))
    assert set(standalonevms) == set(expected.get("StandaloneVM", []))


def test_removetags_errors_if_no_tags_present(qubes, vmname, request):
    request.node.mark_vm_created(vmname)

    # Create
    fake_module = Module(
        {"command": "create", "name": vmname, "vmtype": "AppVM"}
    )
    core(fake_module)
    assert vmname in qubes.domains

    # Remove tags
    fake_module = Module({"command": "removetags", "name": vmname})
    try:
        core(fake_module)

    except ModuleExitWithError:
        assert (
            fake_module.returned_data["msg"]
            == "Expected 'tags' parameter to be specified"
        )
    else:
        pytest.fail("Module should have raised an error")


def test_list_vms_command(vm):
    fake_module = Module({"command": "list_vms", "state": "shutdown"})
    core(fake_module)
    assert vm.name in fake_module.returned_data["list_vms"]


def test_get_states_command(vm):
    fake_module = Module({"command": "get_states"})
    core(fake_module)
    assert f"{vm.name} shutdown" in fake_module.returned_data["states"]
