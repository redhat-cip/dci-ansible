# -*- coding: utf-8 -*-
import callback.dci as dci_callback

from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase


formatter = dci_callback.Formatter()
Options = namedtuple('Options', ['connection', 'module_path', 'forks',
                                 'become', 'become_method', 'become_user',
                                 'check', 'diff'])
options = Options(connection='docker', module_path=['modules'], forks=1,
                  become=None, become_method=None, become_user=None,
                  check=False, diff=False)
loader = DataLoader()
passwords = {'vault_pass': 'secret'}
inventory = InventoryManager(loader=loader, sources='centos-dci-ansible-test,')
variable_manager = VariableManager(loader=loader, inventory=inventory)


def run_task(task):
    play_source = dict(
        name="Ansible Play",
        hosts='centos-dci-ansible-test',
        gather_facts='no',
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
        options=options,
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
    run_task({'action': {'module': 'command', 'args': 'ls /etc'}})
    expectation = 'terminfo'
    outerr = capsys.readouterr()
    assert not outerr.err
    assert expectation in outerr.out


def test_command_failure(capsys):
    run_task({'action': {'module': 'command', 'args': '/ls'}})
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == '[Errno 2] No such file or directory\n\n'


def test_copy_success(capsys):
    args = 'content=foo dest=/tmp/aliases_'
    run_task({'action': {'module': 'copy', 'args': args}})
    outerr = capsys.readouterr()
    assert not outerr.err
    # TODO(Gonéri): won't be required with docker
    if 'Aborting, target uses selinux but python bindings' not in outerr.out:
        assert 'Copying to file' in outerr.out


def test_copy_failure(capsys):
    args = 'content=aa dest=/proc/aliases'
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
    run_task(dict(action=dict(module='debug', args='var=bar')))
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == 'All items completed (changed: False)\n'


def test_debug_failure(capsys):
    run_task(dict(action=dict(module='debug', args='foo=bar')))
    expectation = ("'foo' is not a valid option in debug\nAll items "
                   "completed (changed: False)\n")
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == expectation


def test_file_success(capsys):
    args = 'path=/etc/aliases state=present'
    run_task({'action': {'module': 'file', 'args': args}})
    expectation = ("value of state must be one of: file, directory, link, "
                   "hard, touch, absent, got: present\nNone: None (changed: "
                   "False)\n\n")
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == expectation


def test_file_failure(capsys):
    args = 'path=/proc/1/bob state=present'
    run_task({'action': {'module': 'file', 'args': args}})
    expectation = ('value of state must be one of: file, directory, link, '
                   'hard, touch, absent, got: present\nNone: None (changed: '
                   'False)\n\n')
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == expectation


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
    expectation = 'value of state must be one of'
    outerr = capsys.readouterr()
    assert not outerr.err
    assert expectation in outerr.out


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


def test_package_failure(capsys):
    args = 'name=dontexist state=present'
    run_task(dict(action=dict(module='package', args=args)))
    outerr = capsys.readouterr()
    assert not outerr.err
    expectation = ("No package matching 'dontexist' found available, "
                   "installed or updated\n\n")
    assert outerr.out == expectation


def test_package_failure_with_items(capsys):
    args = 'name={{ item }} state=present'
    run_task({
        'action': {
            'module': 'package',
            'args': args},
        'with_items': ['aa', 'bb']})
    expectation = ("All items completed\n"
                   "No package matching 'aa' found available, installed "
                   "or updated\n"
                   "No package matching 'bb' found available, installed "
                   "or updated\n\n")
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == expectation


def test_set_fact_success(capsys):
    run_task({'action': {'module': 'set_fact', 'args': 'foo=bar'}})
    outerr = capsys.readouterr()
    assert not outerr.err
    assert 'Settings the following facts:' in outerr.out


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


def test_slurp_failure_src_is_a_dir(capsys):
    run_task(dict(action=dict(module='slurp', args='src=/tmp')))
    outerr = capsys.readouterr()
    assert not outerr.err
    assert outerr.out == 'MODULE FAILURE\n\n'


def test_invalid_module_failure(capsys):
    run_task(dict(action=dict(module='invalid_module', args='invalid=key')))
    outerr = capsys.readouterr()
    assert not outerr.err
    assert 'not found in configured module paths.' in outerr.out


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


def test_unarchive_failure_bad_file(capsys):
    args = 'src=/etc/fstab dest=/tmp'
    run_task(dict(action=dict(module='unarchive', args=args)))
    expectation = "sure the required command to extract the file is installed."
    outerr = capsys.readouterr()
    assert not outerr.err
    assert expectation in outerr.out


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
