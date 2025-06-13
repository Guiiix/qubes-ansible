import os
import pytest
import time

from plugins.modules.qubesos import core, VIRT_SUCCESS, VIRT_FAILED
from tests.qubes.conftest import qubes, vmname, Module


def test_create_start_shutdown_destroy_remove(qubes, vmname, request):

    request.node.mark_vm_created(vmname)

    # Create
    rc, _ = core(
        Module({"command": "create", "name": vmname, "vmtype": "AppVM"})
    )
    assert rc == VIRT_SUCCESS
    assert vmname in qubes.domains

    # Start
    rc, _ = core(Module({"command": "start", "name": vmname}))
    assert rc == VIRT_SUCCESS
    vm = qubes.domains[vmname]
    assert vm.is_running()

    # Shutdown
    rc, _ = core(Module({"command": "shutdown", "name": vmname}))
    assert rc == VIRT_SUCCESS
    time.sleep(5)
    assert vm.is_halted()

    # Remove
    rc, _ = core(Module({"command": "remove", "name": vmname}))
    assert rc == VIRT_SUCCESS
    qubes.domains.refresh_cache(force=True)
    assert vmname not in qubes.domains


def test_create_and_absent(qubes, vmname, request):
    request.node.mark_vm_created(vmname)

    # Create
    rc, _ = core(
        Module({"command": "create", "name": vmname, "vmtype": "AppVM"})
    )
    assert rc == VIRT_SUCCESS
    assert vmname in qubes.domains

    # Absent
    rc, _ = core(Module({"state": "absent", "name": vmname}))
    assert rc == VIRT_SUCCESS
    qubes.domains.refresh_cache(force=True)
    assert vmname not in qubes.domains


def test_pause_and_unpause(qubes, vmname, request):
    request.node.mark_vm_created(vmname)
    core(Module({"command": "create", "name": vmname, "vmtype": "AppVM"}))
    core(Module({"command": "start", "name": vmname}))
    time.sleep(1)

    rc, _ = core(Module({"command": "pause", "name": vmname}))
    assert rc == VIRT_SUCCESS
    assert qubes.domains[vmname].is_paused()

    rc, _ = core(Module({"command": "unpause", "name": vmname}))
    assert rc == VIRT_SUCCESS
    assert qubes.domains[vmname].is_running()

    # Clean up
    core(Module({"command": "destroy", "name": vmname}))
    core(Module({"state": "absent", "name": vmname}))


def test_status_command(qubes, vmname, request):
    request.node.mark_vm_created(vmname)
    core(Module({"command": "create", "name": vmname, "vmtype": "AppVM"}))
    rc, state = core(Module({"command": "status", "name": vmname}))
    assert rc == VIRT_SUCCESS
    assert state["status"] == "shutdown"

    core(Module({"command": "start", "name": vmname}))
    rc, state = core(Module({"command": "status", "name": vmname}))
    assert state["status"] == "running"

    core(Module({"command": "destroy", "name": vmname}))
    rc, state = core(Module({"command": "status", "name": vmname}))
    assert state["status"] == "shutdown"

    core(Module({"state": "absent", "name": vmname}))


def test_list_info_and_inventory(tmp_path, qubes):
    # Use a temporary directory for inventory
    os.chdir(tmp_path)

    # Create a standalone VM (by default we don't have any)
    core(
        Module(
            {
                "command": "create",
                "name": "teststandalone",
                "vmtype": "StandaloneVM",
                "template": "debian-12-xfce",
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
    rc, res = core(Module({"command": "createinventory"}))
    assert rc == VIRT_SUCCESS
    assert res["status"] == "successful"

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


def test_properties_and_tags(qubes, vmname, request):
    request.node.mark_vm_created(vmname)
    props = {"autostart": True, "debug": True, "memory": 256}
    tags = ["tag1", "tag2"]
    params = {
        "state": "present",
        "name": vmname,
        "properties": props,
        "tags": tags,
    }
    rc, res = core(Module(params))
    assert rc == VIRT_SUCCESS
    changed_values = res["Properties updated"]
    assert "autostart" in changed_values
    assert qubes.domains[vmname].autostart is True
    for t in tags:
        assert t in qubes.domains[vmname].tags
    # cleanup
    core(Module({"state": "absent", "name": vmname}))


def test_invalid_property_key(qubes):
    # Unknown property should fail
    rc, res = core(
        Module(
            {"state": "present", "name": "dom0", "properties": {"titi": "toto"}}
        )
    )
    assert rc == VIRT_FAILED
    assert "Invalid property" in res


def test_invalid_property_type(qubes, vmname, request):
    # Wrong type for memory
    rc, res = core(
        Module(
            {
                "state": "present",
                "name": vmname,
                "properties": {"memory": "toto"},
            }
        )
    )
    assert rc == VIRT_FAILED
    assert "Invalid property value type" in res


def test_missing_netvm(qubes, vmname, request):
    # netvm does not exist
    rc, res = core(
        Module(
            {
                "state": "present",
                "name": vmname,
                "properties": {"netvm": "toto"},
            }
        )
    )
    assert rc == VIRT_FAILED
    assert "Missing netvm" in res


def test_default_netvm(qubes, vm, netvm, request):
    """
    Able to reset back to default netvm without needing to mention it by name
    """
    default_netvm = vm.netvm

    # Change to non-default netvm
    change_netvm_rc, change_netvm_res = core(
        Module(
            {
                "state": "present",
                "name": vm.name,
                "properties": {"netvm": netvm.name},
            }
	)
    )
    assert "netvm" in change_netvm_res["Properties updated"]
    assert change_netvm_rc == VIRT_SUCCESS

    # Ability to reset back to default netvm, whichever it is
    reset_netvm_rc, reset_netvm_res = core(
        Module(
            {
                "state": "present",
                "name": vm.name,
                "properties": {"netvm": "*default*"},
            }
	)
    )
    assert "netvm" in reset_netvm_res["Properties updated"]
    assert default_netvm != netvm
    assert reset_netvm_rc == VIRT_SUCCESS

    qubes.domains.refresh_cache(force=True)
    assert qubes.domains[vm.name].netvm == default_netvm


def test_missing_default_dispvm(qubes):
    # default_dispvm does not exist
    rc, res = core(
        Module(
            {
                "state": "present",
                "name": "dom0",
                "properties": {"default_dispvm": "toto"},
            }
        )
    )
    assert rc == VIRT_FAILED
    assert "Missing default_dispvm" in res


def test_wrong_volume_name(qubes, vmname, request):
    # volume name not allowed for AppVM
    rc, res = core(
        Module(
            {
                "state": "present",
                "name": vmname,
                "properties": {"volume": {"name": "root", "size": 10}},
            }
        )
    )
    assert rc == VIRT_FAILED
    assert "Wrong volume name" in res


def test_missing_volume_fields(qubes, vmname, request):
    # Missing name
    rc1, res1 = core(
        Module(
            {
                "state": "present",
                "name": vmname,
                "properties": {"volume": {"size": 10}},
            }
        )
    )
    assert rc1 == VIRT_FAILED
    assert "Missing name for the volume" in res1

    # Missing size
    rc2, res2 = core(
        Module(
            {
                "state": "present",
                "name": vmname,
                "properties": {"volume": {"name": "private"}},
            }
        )
    )
    assert rc2 == VIRT_FAILED
    assert "Missing size for the volume" in res2


def test_removetags_without_tags(qubes, vmname, request):
    request.node.mark_vm_created(vmname)

    # Create
    rc, _ = core(
        Module({"command": "create", "name": vmname, "vmtype": "AppVM"})
    )
    assert rc == VIRT_SUCCESS
    assert vmname in qubes.domains

    # Remove tags
    rc, res = core(Module({"command": "removetags", "name": vmname}))
    assert rc == VIRT_FAILED
    assert "Missing tag" in res.get("Error", "")
