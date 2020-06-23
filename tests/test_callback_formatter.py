# -*- coding: utf-8 -*-
import callback.dci as dci_callback

from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
import sys

import pytest

has_dnf = True
try:
    import yum  # noqa
except ImportError:
    try:
        import dnf  # noqa
    except ImportError:
        has_dnf = False


formatter = dci_callback.Formatter()
loader = DataLoader()
passwords = {'vault_pass': 'secret'}
inventory = InventoryManager(loader=loader, sources='localhost,')
variable_manager = VariableManager(loader=loader, inventory=inventory)

# NOTE(Gonéri): In case we are in a virtualenv, we must reuse the same Python
# interpreter to be able to reach the dciclient lib.
variable_manager._extra_vars = {'ansible_python_interpreter': sys.executable}  # noqa


def run_task(task):
    play_source = dict(
        name="Ansible Play",
        hosts='localhost',
        gather_facts='no',
        connection='local',
        tasks=[task])

    play = Play().load(play_source)

    class ResultCallback(CallbackBase):

        def v2_runner_on_ok(self, result, **kwargs):
            print(formatter.format(result))

        def v2_runner_on_failed(self, result, **kwargs):
            print(formatter.format(result))

    results_callback = ResultCallback()
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords=passwords,
        stdout_callback=results_callback)
    tqm.run(play)


def test_add_host_success(capsys):
    run_task({'action': {'module': 'add_host', 'args': 'name=foo'}})
    expectation = "Adding host 'foo' in current inventory\n"
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == expectation


def test_add_host_failure(capsys):
    # TODO: Should return "name or hostname arg needs to be provided"
    run_task({'action': {'module': 'add_host', 'args': 'state=bob'}})
    expectation = 'name or hostname arg needs to be provided\n\n'
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == expectation


def test_authorized_key_failure(capsys):
    args = 'user=charlie state=present'
    run_task({'action': {'module': 'authorized_key', 'args': args}})
    expectation = 'missing required arguments: key\n\n'
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == expectation


def test_command_success(capsys):
    run_task({'action': {'module': 'command', 'args': 'ls samples'}})
    expectation = ('sample_1.yml\n'
                   'sample_2.yml\n'
                   'sample_3.yml\n'
                   'sample_4.yml\n'
                   'sample_upgrade.yml\n')
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == expectation


def test_command_failure(capsys):
    run_task({'action': {'module': 'command', 'args': '/ls'}})
    outerr = capsys.readouterr()
    assert not outerr.err
    assert '[Errno 2]' in outerr.out


def test_copy_success(capsys, tmpdir):
    args = 'content=foo dest=%s/aliases_' % tmpdir
    run_task({'action': {'module': 'copy', 'args': args}})
    outerr = capsys.readouterr()
    assert not outerr.err
    # TODO(Gonéri): won't be required with docker
    if 'Aborting, target uses selinux but python bindings' not in outerr.out:
        assert 'Copying to file' in outerr.out


def test_copy_failure(capsys):
    args = 'src=/etc/aliases dest=/proc/aliases'
    run_task({'action': {'module': 'copy', 'args': args}})
    expectation = "not writable"
    outerr = capsys.readouterr()
    assert not outerr.err
    assert expectation in outerr.out


# def test_dci_topic_failure_bad_params(capsys):
#     run_task(dict(action=dict(module='dci_topic', args='named=bob')))
#     outerr = capsys.readouterr()
#     assert not outerr.err
#     assert 'Unsupported parameters' in outerr.out


# def test_dci_topic_failure_no_auth(capsys):
#     run_task(dict(action=dict(module='dci_topic', args='name=bob')))
#     outerr = capsys.readouterr()
#     assert not outerr.err
#     assert 'Missing or incomplete credentials.' in outerr.out


def test_debug_success(capsys):
    run_task(dict(action=dict(module='debug', args='var=hostvars')))
    outerr = capsys.readouterr()
    assert not outerr.err
    assert 'inventory_hostname' in outerr.out


def test_debug_failure(capsys):
    run_task(dict(action=dict(module='debug', args='foo=bar')))
    expectation = [
        "'foo' is not a valid option in debug",
        "Invalid options for debug"]
    outerr = capsys.readouterr()
    assert not outerr.err
    for i in expectation:
        if i in outerr.out:
            break
    else:
        assert False


def test_file_success(capsys, tmpdir):
    args = 'path=%s/aliases state=touch' % tmpdir
    run_task({'action': {'module': 'file', 'args': args}})
    outerr = capsys.readouterr()
    assert not outerr.err
    assert 'changed: True' in outerr.out


def test_file_failure(capsys):
    args = 'path=/proc/1/bob state=touch'
    run_task({'action': {'module': 'file', 'args': args}})
    expectation = '[Errno 2]'
    outerr = capsys.readouterr()
    assert not outerr.err
    assert expectation in outerr.out


def test_find_success(capsys):
    run_task({'action': {'module': 'find', 'args': 'paths=/proc/1 age=400w'}})
    outerr = capsys.readouterr()
    assert not outerr.err
    assert 'Examined:' in outerr.out


def test_find_failure(capsys):
    args = 'pathz=/proc/1/bob age=400w'
    run_task({'action': {'module': 'find', 'args': args}})
    outerr = capsys.readouterr()
    assert not outerr.err
    assert 'Unsupported parameters' in outerr.out


def test_firewalld_failure(capsys):
    run_task({'action': {'module': 'firewalld', 'args': 'port=80 state=BOB'}})
    exceptation = ('value of state must be one of: absent, disabled, '
                   'enabled, present, got: BOB\n\n')
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == exceptation


def test_ini_file_success(capsys, tmpdir):
    args = 'path=%s/foo.ini section=bar value=1 state=present' % tmpdir
    run_task({'action': {'module': 'ini_file', 'args': args}})
    outerr = capsys.readouterr()
    assert not outerr.err
    assert 'Message: OK (bar.None=1)' in outerr.out


def test_ini_file_failure(capsys):
    args = 'path=/proc/1/foo.ini section=bar value=1 state=present'
    run_task(dict(action=dict(module='ini_file', args=args)))
    outerr = capsys.readouterr()
    assert not outerr.err
    assert '/proc/1/foo.ini - (changed: False)' in outerr.out


@pytest.mark.skipif(not has_dnf, reason="no dnf available in virtualenv")
def test_package_failure(capsys):
    args = 'name=dontexist state=present'
    run_task(dict(action=dict(module='package', args=args)))
    outerr = capsys.readouterr()
    assert not outerr.err
    expectation = 'Error: This command has to be run under the root user.\n\n'
    if 'bindings for rpm are needed for this module.' not in outerr.out:
        assert outerr.out == expectation


@pytest.mark.skipif(not has_dnf, reason="no dnf available in virtualenv")
def test_package_failure_with_items(capsys):
    args = 'name={{ item }} state=present'
    run_task({
        'action': {
            'module': 'package',
            'args': args},
        'with_items': ['aa', 'bb']})
    expectation = 'All items completed\n\n'
    outerr = capsys.readouterr()
    assert not outerr.err
    if 'bindings for rpm are needed for this module.' not in outerr.out:
        assert outerr.out == expectation


def test_set_fact_success(capsys):
    run_task({'action': {'module': 'set_fact', 'args': 'foo=bar bar=foo'}})
    outerr = capsys.readouterr()
    assert not outerr.err
    assert 'Settings the following facts:\n' in outerr.out
    assert 'foo: bar\n' in outerr.out
    assert 'bar: foo\n' in outerr.out


def test_set_fact_success_with_items(capsys):
    run_task({
        'action': {
            'module': 'set_fact',
            'args': 'foo={{ item }}'},
        'with_items': ['a', 'b', 'c']})
    outerr = capsys.readouterr()
    assert not outerr.err
    assert 'Settings the following facts:' in outerr.out


def test_service_failure(capsys):
    args = 'name=nothing state=restarted'
    run_task({'action': {'module': 'service', 'args': args}})
    expectation = ("Could not find the requested service nothing: host\n"
                   "Service Name: None, Service State: None (changed: "
                   "False)\n")
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == expectation


def test_slurp_failure_no_src(capsys):
    run_task(dict(action=dict(module='slurp', args='invalid=key')))
    outerr = capsys.readouterr()
    assert not outerr.err
    assert 'Unsupported parameters' in outerr.out


def test_slurp_failure_src_is_a_dir(capsys, tmpdir):
    run_task(dict(action=dict(module='slurp', args='src=%s' % tmpdir)))
    outerr = capsys.readouterr()
    assert not outerr.err
    assert 'MODULE FAILURE' in outerr.out


def test_invalid_module_failure(capsys):
    run_task(dict(action=dict(module='invalid_module', args='invalid=key')))
    outerr = capsys.readouterr()
    assert not outerr.err
    assert 'not found in configured module paths' in outerr.out


def test_stat_failure(capsys):
    run_task(dict(action=dict(module='stat', args='invalid=key')))
    expectation = 'Unsupported parameters for (stat) module'
    outerr = capsys.readouterr()
    assert not outerr.err
    assert expectation in outerr.out


def test_template_failure(capsys):
    run_task(dict(action=dict(module='template', args='invalid=key')))
    expectation = ('src and dest are required\nCopying template to file: None '
                   '(changed: False)\n')
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == expectation


def test_unarchive_failure_bad_args(capsys):
    run_task(dict(action=dict(module='unarchive', args='invalid=key')))
    expectation = ("src (or content) and dest are required\nSource: None, "
                   "Destination: None\n\n")
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == expectation


def test_unarchive_failure_bad_file(capsys, tmpdir):
    args = 'src=/etc/fstab dest=%s' % tmpdir
    run_task(dict(action=dict(module='unarchive', args=args)))
    expectation = [
        "sure the required command to extract the file is installed.",
        "Could not find or access '/etc/fstab'"]
    outerr = capsys.readouterr()
    assert not outerr.err
    for i in expectation:
        if i in outerr.out:
            break
    else:
        assert False


def test_user_failure(capsys):
    run_task(dict(action=dict(module='user', args='invalid=key')))
    expectation = 'Unsupported parameters for (user) module'
    outerr = capsys.readouterr()
    assert not outerr.err
    assert expectation in outerr.out


def test_yum_repository_failure(capsys):
    run_task(dict(action=dict(module='yum_repository', args='invalid=key')))
    expectation = 'Unsupported parameters for (yum_repository) module'
    outerr = capsys.readouterr()
    assert not outerr.err
    assert expectation in outerr.out
