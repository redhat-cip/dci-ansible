# (c) 2016 Matt Clay <matt@mystile.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# modified for the DCI project:
# - use a regex to match test cases instead of a prefix
# - do not include failed tasks
# - output filename without timestamp
# - python 3.6 compatible (no use of the dataclasses module and type annotations)

import os
import time
import re

from ansible import constants as C
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.plugins.callback import CallbackBase

import abc
import datetime
import decimal

from xml.dom import minidom

# noinspection PyPep8Naming
from xml.etree import ElementTree as ET

DOCUMENTATION = '''
    name: dcijunit
    type: aggregate
    short_description: write playbook output to a JUnit file.
    version_added: historical
    description:
      - This callback writes playbook output to a JUnit formatted XML file.
      - "Tasks show up in the report as follows:
        'ok': pass
        'failed' with 'EXPECTED FAILURE' in the task name: pass
        'failed' with 'TOGGLE RESULT' in the task name: pass
        'ok' with 'TOGGLE RESULT' in the task name: failure
        'failed' due to an exception: error
        'failed' for other reasons: failure
        'skipped': skipped"
    options:
      output_dir:
        name: JUnit output dir
        default: ~/.ansible.log
        description: Directory to write XML files to.
        env:
          - name: JUNIT_OUTPUT_DIR
      task_class:
        name: JUnit Task class
        default: False
        description: Configure the output to be one class per yaml file
        env:
          - name: JUNIT_TASK_CLASS
      task_relative_path:
        name: JUnit Task relative path
        default: none
        description: Configure the output to use relative paths to given directory
        version_added: "2.8"
        env:
          - name: JUNIT_TASK_RELATIVE_PATH
      replace_out_of_tree_path:
        name: Replace out of tree path
        default: none
        description: Replace the directory portion of an out-of-tree relative task path with the given placeholder
        version_added: "2.12.3"
        env:
          - name: JUNIT_REPLACE_OUT_OF_TREE_PATH
      fail_on_change:
        name: JUnit fail on change
        default: False
        description: Consider any tasks reporting "changed" as a junit test failure
        env:
          - name: JUNIT_FAIL_ON_CHANGE
      fail_on_ignore:
        name: JUnit fail on ignore
        default: False
        description: Consider failed tasks as a junit test failure even if ignore_on_error is set
        env:
          - name: JUNIT_FAIL_ON_IGNORE
      include_setup_tasks_in_report:
        name: JUnit include setup tasks in report
        default: True
        description: Should the setup tasks be included in the final report
        env:
          - name: JUNIT_INCLUDE_SETUP_TASKS_IN_REPORT
      hide_task_arguments:
        name: Hide the arguments for a task
        default: False
        description: Hide the arguments for a task
        version_added: "2.8"
        env:
          - name: JUNIT_HIDE_TASK_ARGUMENTS
      test_case_regex:
        name: Regular expression to find actual test cases
        default: <empty>
        description: Consider a task only as test case matches this value. Additionally failing tasks are recorded as failed test cases.
        version_added: "2.8"
        env:
          - name: JUNIT_TEST_CASE_REGEX
    requirements:
      - enable in configuration
'''


# imported from ansible/lib/ansible/utils/_junit_xml.py (commit fd341265d001d4e6545ffb2b7d154340cb1f1931)
"""
Dataclasses for creating JUnit XML files.
See: https://github.com/junit-team/junit5/blob/main/platform-tests/src/test/resources/jenkins-junit.xsd
"""


class TestResult(metaclass=abc.ABCMeta):
    """Base class for the result of a test case."""

    def __init__(self, output=None, message=None, _type=None):
        self.output = output
        self.message = message
        self.type = _type or self.tag

    @property
    @abc.abstractmethod
    def tag(self):
        """Tag name for the XML element created by this result type."""

    def get_attributes(self):
        """Return a dictionary of attributes for this instance."""
        return _attributes(
            message=self.message,
            type=self.type,
        )

    def get_xml_element(self):
        """Return an XML element representing this instance."""
        element = ET.Element(self.tag, self.get_attributes())
        element.text = self.output

        return element


class TestFailure(TestResult):
    """Failure info for a test case."""

    @property
    def tag(self):
        """Tag name for the XML element created by this result type."""
        return 'failure'


class TestError(TestResult):
    """Error info for a test case."""

    @property
    def tag(self):
        """Tag name for the XML element created by this result type."""
        return 'error'


class TestCase:
    """An individual test case."""

    def __init__(self, name, assertions=None, classname=None,
                 status=None, time=None,
                 errors=None, failures=None,
                 skipped=None, system_out=None,
                 system_err=None, is_disabled=False):
        self.name = name
        self.assertions = assertions
        self.classname = classname
        self.status = status
        self.time = time
        self.errors = errors if errors is not None else []
        self.failures = failures if failures is not None else []
        self.skipped = skipped
        self.system_out = system_out
        self.system_err = system_err
        self.is_disabled = is_disabled

    @property
    def is_failure(self):
        """True if the test case contains failure info."""
        return bool(self.failures)

    @property
    def is_error(self):
        """True if the test case contains error info."""
        return bool(self.errors)

    @property
    def is_skipped(self):
        """True if the test case was skipped."""
        return bool(self.skipped)

    def get_attributes(self):
        """Return a dictionary of attributes for this instance."""
        return _attributes(
            assertions=self.assertions,
            classname=self.classname,
            name=self.name,
            status=self.status,
            time=self.time,
        )

    def get_xml_element(self):
        """Return an XML element representing this instance."""
        element = ET.Element('testcase', self.get_attributes())

        if self.skipped:
            ET.SubElement(element, 'skipped').text = self.skipped

        element.extend([error.get_xml_element() for error in self.errors])
        element.extend([failure.get_xml_element() for failure in self.failures])

        if self.system_out:
            ET.SubElement(element, 'system-out').text = self.system_out

        if self.system_err:
            ET.SubElement(element, 'system-err').text = self.system_err

        return element


class TestSuite:
    """A collection of test cases."""

    def __init__(self, name, hostname=None, id=None,
                 package=None, timestamp=None,
                 properties=None, cases=None,
                 system_out=None, system_err=None):
        self.name = name
        self.hostname = hostname
        self.id = id
        self.package = package
        self.timestamp = timestamp
        self.properties = properties if properties is not None else {}
        self.cases = cases if cases is not None else []
        self.system_out = system_out
        self.system_err = system_err

    def __post_init__(self):
        if self.timestamp and self.timestamp.tzinfo != datetime.timezone.utc:
            raise ValueError(f'timestamp.tzinfo must be {datetime.timezone.utc!r}')

    @property
    def disabled(self):
        """The number of disabled test cases."""
        return sum(case.is_disabled for case in self.cases)

    @property
    def errors(self):
        """The number of test cases containing error info."""
        return sum(case.is_error for case in self.cases)

    @property
    def failures(self):
        """The number of test cases containing failure info."""
        return sum(case.is_failure for case in self.cases)

    @property
    def skipped(self):
        """The number of test cases containing skipped info."""
        return sum(case.is_skipped for case in self.cases)

    @property
    def tests(self):
        """The number of test cases."""
        return len(self.cases)

    @property
    def time(self):
        """The total time from all test cases."""
        return decimal.Decimal(sum(case.time for case in self.cases if case.time))

    def get_attributes(self):
        """Return a dictionary of attributes for this instance."""
        return _attributes(
            disabled=self.disabled,
            errors=self.errors,
            failures=self.failures,
            hostname=self.hostname,
            id=self.id,
            name=self.name,
            package=self.package,
            skipped=self.skipped,
            tests=self.tests,
            time=self.time,
            timestamp=self.timestamp.replace(tzinfo=None).isoformat(timespec='seconds') if self.timestamp else None,
        )

    def get_xml_element(self):
        """Return an XML element representing this instance."""
        element = ET.Element('testsuite', self.get_attributes())

        if self.properties:
            ET.SubElement(element, 'properties').extend([ET.Element('property', dict(name=name, value=value)) for name, value in self.properties.items()])

        element.extend([test_case.get_xml_element() for test_case in self.cases])

        if self.system_out:
            ET.SubElement(element, 'system-out').text = self.system_out

        if self.system_err:
            ET.SubElement(element, 'system-err').text = self.system_err

        return element


class TestSuites:
    """A collection of test suites."""

    def __init__(self, name=None, suites=None):
        self.name = name
        self.suites = suites if suites is not None else []

    @property
    def disabled(self):
        """The number of disabled test cases."""
        return sum(suite.disabled for suite in self.suites)

    @property
    def errors(self):
        """The number of test cases containing error info."""
        return sum(suite.errors for suite in self.suites)

    @property
    def failures(self):
        """The number of test cases containing failure info."""
        return sum(suite.failures for suite in self.suites)

    @property
    def tests(self):
        """The number of test cases."""
        return sum(suite.tests for suite in self.suites)

    @property
    def time(self):
        """The total time from all test cases."""
        return decimal.Decimal(sum(suite.time for suite in self.suites))

    def get_attributes(self):
        """Return a dictionary of attributes for this instance."""
        return _attributes(
            disabled=self.disabled,
            errors=self.errors,
            failures=self.failures,
            name=self.name,
            tests=self.tests,
            time=self.time,
        )

    def get_xml_element(self):
        """Return an XML element representing this instance."""
        element = ET.Element('testsuites', self.get_attributes())
        element.extend([suite.get_xml_element() for suite in self.suites])

        return element

    def to_pretty_xml(self):
        """Return a pretty formatted XML string representing this instance."""
        return _pretty_xml(self.get_xml_element())


def _attributes(**kwargs):
    """Return the given kwargs as a dictionary with values converted to strings. Items with a value of None will be omitted."""
    return {key: str(value) for key, value in kwargs.items() if value is not None}


def _pretty_xml(element):
    """Return a pretty formatted XML string representing the given element."""
    return minidom.parseString(ET.tostring(element, encoding='unicode')).toprettyxml()


class CallbackModule(CallbackBase):
    """
    This callback writes playbook output to a JUnit formatted XML file.

    Tasks show up in the report as follows:
        'ok': pass
        'failed' with 'EXPECTED FAILURE' in the task name: pass
        'failed' with 'TOGGLE RESULT' in the task name: pass
        'ok' with 'TOGGLE RESULT' in the task name: failure
        'failed' due to an exception: error
        'failed' for other reasons: failure
        'skipped': skipped

    This plugin makes use of the following environment variables:
        JUNIT_OUTPUT_DIR (optional): Directory to write XML files to.
                                     Default: ~/.ansible.log
        JUNIT_TASK_CLASS (optional): Configure the output to be one class per yaml file
                                     Default: False
        JUNIT_TASK_RELATIVE_PATH (optional): Configure the output to use relative paths to given directory
                                     Default: none
        JUNIT_FAIL_ON_CHANGE (optional): Consider any tasks reporting "changed" as a junit test failure
                                     Default: False
        JUNIT_FAIL_ON_IGNORE (optional): Consider failed tasks as a junit test failure even if ignore_on_error is set
                                     Default: False
        JUNIT_INCLUDE_SETUP_TASKS_IN_REPORT (optional): Should the setup tasks be included in the final report
                                     Default: True
        JUNIT_HIDE_TASK_ARGUMENTS (optional): Hide the arguments for a task
                                     Default: False
        JUNIT_TEST_CASE_REGEX (optional): Consider a task only as test case if it matches this regular expression.
                                     test cases.
                                     Default: <empty>
        JUNIT_GENERATE_TASK_NAME (optional): Name of the task to generate the jUnit report.
                                     Default: Verify mandatory tests
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'dcijunit'
    CALLBACK_NEEDS_ENABLED = False
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

        self._output_dir = os.getenv('JUNIT_OUTPUT_DIR', os.path.expanduser('~/.ansible.log'))
        self._task_class = os.getenv('JUNIT_TASK_CLASS', 'False').lower()
        self._task_relative_path = os.getenv('JUNIT_TASK_RELATIVE_PATH', '')
        self._fail_on_change = os.getenv('JUNIT_FAIL_ON_CHANGE', 'False').lower()
        self._fail_on_ignore = os.getenv('JUNIT_FAIL_ON_IGNORE', 'False').lower()
        self._include_setup_tasks_in_report = os.getenv('JUNIT_INCLUDE_SETUP_TASKS_IN_REPORT', 'True').lower()
        self._hide_task_arguments = os.getenv('JUNIT_HIDE_TASK_ARGUMENTS', 'False').lower()
        self._test_case_regex = os.getenv('JUNIT_TEST_CASE_REGEX', '')
        self._replace_out_of_tree_path = os.getenv('JUNIT_REPLACE_OUT_OF_TREE_PATH', None)
        self._generate_task_name = os.getenv('JUNIT_GENERATE_TASK_NAME', 'Verify mandatory tests')
        self._playbook_path = None
        self._playbook_name = None
        self._loader = None
        self._play = None
        self._play_name = None
        self._task_data = None
        self._test_case_re = None if self._test_case_regex == '' else re.compile(self._test_case_regex, re.IGNORECASE)
        self._generated = False

        self.disabled = False

        self._task_data = {}

        if self._replace_out_of_tree_path is not None:
            self._replace_out_of_tree_path = to_text(self._replace_out_of_tree_path)

        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)

    def _get_job_logs(self):
        """Return the value of job_logs from jumphost or localhost hostvars."""
        vm = self._play.get_variable_manager()
        vars = vm.get_vars()
        for host in ('jumphost', 'localhost'):
            try:
                return vars['hostvars'][host]['job_logs']['path']
            except KeyError:
                continue
        return None

    def _start_task(self, task):
        """ record the start of a task for one or more hosts """

        uuid = task._uuid

        if uuid in self._task_data:
            return

        play = self._play_name
        name = task.get_name().strip()
        path = task.get_path()
        action = task.action

        if not task.no_log and self._hide_task_arguments == 'false':
            args = ', '.join(('%s=%s' % a for a in task.args.items()))
            if args:
                name += ' ' + args

        self._task_data[uuid] = TaskData(uuid, name, path, play, action)

        # Need to generate the report before the end of the playbook
        # if the task name matches the given name. This is useful for
        # the case we need to check the file inside the playbook at a
        # particular stage. For example in doaa, it checks the
        # mandatory tests.
        if self._generate_task_name and name.find(self._generate_task_name) != -1:
            log_dir = self._get_job_logs()
            self._generate_report(log_dir)

    def _finish_task(self, status, result):
        """ record the results of a task for a single host """

        task_uuid = result._task._uuid

        if hasattr(result, '_host'):
            host_uuid = result._host._uuid
            host_name = result._host.name
        else:
            host_uuid = 'include'
            host_name = 'include'

        task_data = self._task_data[task_uuid]

        if self._fail_on_change == 'true' and status == 'ok' and result._result.get('changed', False):
            status = 'failed'

        # ignore failure if expected and toggle result if asked for
        if status == 'failed' and 'EXPECTED FAILURE' in task_data.name:
            status = 'ok'
        elif 'TOGGLE RESULT' in task_data.name:
            if status == 'failed':
                status = 'ok'
            elif status == 'ok':
                status = 'failed'

        if self._test_case_re and self._test_case_re.search(task_data.name):
            task_data.add_host(HostData(host_uuid, host_name, status, result))

    def _build_test_case(self, task_data, host_data):
        """ build a TestCase from the given TaskData and HostData """

        name = '[%s] %s: %s' % (host_data.name, task_data.play, task_data.name)
        duration = host_data.finish - task_data.start

        if self._task_relative_path and task_data.path:
            junit_classname = to_text(os.path.relpath(to_bytes(task_data.path), to_bytes(self._task_relative_path)))
        else:
            junit_classname = task_data.path

        if self._replace_out_of_tree_path is not None and junit_classname.startswith('../'):
            junit_classname = self._replace_out_of_tree_path + to_text(os.path.basename(to_bytes(junit_classname)))

        if self._task_class == 'true':
            junit_classname = re.sub(r'\.yml:[0-9]+$', '', junit_classname)

        if host_data.status == 'included':
            return TestCase(name=name, classname=junit_classname, time=duration, system_out=str(host_data.result))

        res = host_data.result._result
        rc = res.get('rc', 0)
        dump = self._dump_results(res, indent=0)
        dump = self._cleanse_string(dump)

        if host_data.status == 'ok':
            return TestCase(name=name, classname=junit_classname, time=duration, system_out=dump)

        test_case = TestCase(name=name, classname=junit_classname, time=duration)

        if host_data.status == 'failed':
            if 'exception' in res:
                message = res['exception'].strip().split('\n')[-1]
                output = res['exception']
                test_case.errors.append(TestError(message=message, output=output))
            elif 'msg' in res:
                message = res['msg']
                test_case.failures.append(TestFailure(message=message, output=dump))
            else:
                test_case.failures.append(TestFailure(message='rc=%s' % rc, output=dump))
        elif host_data.status == 'skipped':
            if 'skip_reason' in res:
                message = res['skip_reason']
            else:
                message = 'skipped'
            test_case.skipped = message

        return test_case

    def _cleanse_string(self, value):
        """ convert surrogate escapes to the unicode replacement character to avoid XML encoding errors """
        return to_text(to_bytes(value, errors='surrogateescape'), errors='replace')

    def _generate_report(self, odir=None):
        """ generate a TestSuite report from the collected TaskData and HostData """

        # generate the report only once
        if self._generated:
            return

        test_cases = []

        for task_uuid, task_data in self._task_data.items():
            if task_data.action in C._ACTION_SETUP and self._include_setup_tasks_in_report == 'false':
                continue

            for host_uuid, host_data in task_data.host_data.items():
                test_cases.append(self._build_test_case(task_data, host_data))

        test_suite = TestSuite(name=self._playbook_name, cases=test_cases)
        test_suites = TestSuites(suites=[test_suite])
        report = test_suites.to_pretty_xml()

        output_file = os.path.join(odir if odir else self._output_dir, '%s.xml' % (self._playbook_name))

        with open(output_file, 'wb') as xml:
            xml.write(to_bytes(report, errors='surrogate_or_strict'))

        self._generated = True

    def v2_playbook_on_start(self, playbook):
        self._playbook_path = playbook._file_name
        self._playbook_name = os.path.splitext(os.path.basename(self._playbook_path))[0]
        self._loader = playbook.get_loader()

    def v2_playbook_on_play_start(self, play):
        self._play = play
        self._play_name = play.get_name()

    def v2_runner_on_no_hosts(self, task):
        self._start_task(task)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._start_task(task)

    def v2_playbook_on_cleanup_task_start(self, task):
        self._start_task(task)

    def v2_playbook_on_handler_task_start(self, task):
        self._start_task(task)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if ignore_errors and self._fail_on_ignore != 'true':
            self._finish_task('ok', result)
        else:
            self._finish_task('failed', result)

    def v2_runner_on_ok(self, result):
        self._finish_task('ok', result)

    def v2_runner_on_skipped(self, result):
        self._finish_task('skipped', result)

    def v2_playbook_on_include(self, included_file):
        self._finish_task('included', included_file)

    def v2_playbook_on_stats(self, stats):
        self._generate_report()


class TaskData:
    """
    Data about an individual task.
    """

    def __init__(self, uuid, name, path, play, action):
        self.uuid = uuid
        self.name = name
        self.path = path
        self.play = play
        self.start = None
        self.host_data = {}
        self.start = time.time()
        self.action = action

    def add_host(self, host):
        if host.uuid in self.host_data:
            if host.status == 'included':
                # concatenate task include output from multiple items
                host.result = '%s\n%s' % (self.host_data[host.uuid].result, host.result)
            else:
                raise Exception('%s: %s: %s: duplicate host callback: %s' % (self.path, self.play, self.name, host.name))

        self.host_data[host.uuid] = host


class HostData:
    """
    Data about an individual host.
    """

    def __init__(self, uuid, name, status, result):
        self.uuid = uuid
        self.name = name
        self.status = status
        self.result = result
        self.finish = time.time()
