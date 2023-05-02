# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible import constants as C
from ansible.plugins.callback.default import CallbackModule as CM_default
from ansible.release import __version__ as ansible_version

from dciauth.version import __version__ as dciauth_version
from dciclient.v1.api import context as dci_context
from dciclient.v1.api import file as dci_file
from dciclient.v1.api import jobstate as dci_jobstate
from dciclient.version import __version__ as dciclient_version


COMPAT_OPTIONS = (('display_skipped_hosts', C.DISPLAY_SKIPPED_HOSTS),
                  ('display_ok_hosts', True),
                  ('show_custom_stats', C.SHOW_CUSTOM_STATS),
                  ('display_failed_stderr', False),
                  ('check_mode_markers', False),
                  ('show_per_host_start', False))


class CallbackModule(CM_default):
    """This callback module uploads the Ansible output to a DCI control
server."""
    CALLBACK_VERSION = '2.0'
    CALLBACK_TYPE = 'dci'
    CALLBACK_NAME = 'dci'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):

        super(CallbackModule, self).__init__()

        self._real_display = self._display
        self.verbosity = self._display.verbosity
        self._display = self

        self._jobstate_id = os.getenv("DCI_JOBSTATE_ID")
        self._job_id = os.getenv("DCI_JOB_ID")
        self._current_status = None
        self._dci_context = self._build_dci_context()
        self._explicit = self._job_id is not None
        self._backlog = []
        self._file_backlog = []
        self._name = None
        self._content = ''
        self._color = None
        self._warns = []
        self._warn_prefix = False
        self._item_failed = False

    def get_option(self, name):
        for key, val in COMPAT_OPTIONS:
            if key == name:
                return val
        return False

    @staticmethod
    def _get_details():
        """Method that retrieves the appropriate credentials. """

        login = os.getenv('DCI_LOGIN')
        password = os.getenv('DCI_PASSWORD')

        client_id = os.getenv('DCI_CLIENT_ID')
        api_secret = os.getenv('DCI_API_SECRET')

        url = os.getenv('DCI_CS_URL', 'https://api.distributed-ci.io')

        return login, password, url, client_id, api_secret

    def _build_dci_context(self):
        login, password, url, client_id, api_secret = self._get_details()
        user_agent = ('Ansible/%s (python-dciclient/%s, python-dciauth/%s)'
                      ) % (ansible_version, dciclient_version, dciauth_version)
        if login is not None and password is not None:
            return dci_context.build_dci_context(url, login, password,
                                                 user_agent)
        elif client_id is not None and api_secret is not None:
            return dci_context.build_signature_context(url, client_id,
                                                       api_secret, user_agent)

    def warning(self, msg):
        pass

    def deprecated(self, *args, **kwargs):
        pass

    def _handle_warnings(self, res):
        """If displaying warning messages is enabled and the current task has
        any, add them to the task content and activate the flag so the task is
        marked and formatted properly in the CS. This ignores warning messages
        that have already occurred in the execution."""
        if C.ACTION_WARNINGS:
            if 'warnings' in res:
                for warning in res['warnings']:
                    if warning not in self._warns:
                        self._content += "[WARNING]: " + warning + "\n"
                        self._warns.append(warning)
                        self._warn_prefix = True
            if 'deprecations' in res:
                for warning in res['deprecations']:
                    if warning["msg"] not in self._warns:
                        self._content += "[DEPRECATION WARNING]: " + warning["msg"] + "\n"
                        self._warns.append(warning["msg"])
                        self._warn_prefix = True

        super(CallbackModule, self)._handle_warnings(res)

    def display(self, msg, color=None, screen_only=False, *args, **kwargs):
        if screen_only:
            return

        if color is not None:
            self._color = color

        self._content += msg + '\n'

    def banner(self, msg):
        # upload the previous content when we have a new banner (start
        # of task/play/playbook...)

        if self._name:
            if self._color == C.COLOR_SKIP:
                prefix = 'skipped/'
            elif self._color == C.COLOR_UNREACHABLE:
                prefix = "unreachable/"
            elif self._color == C.COLOR_ERROR or self._item_failed:
                prefix = "failed/"
            else:
                prefix = ''

            self._item_failed = False

            if self._warn_prefix:
                prefix += "warn/"
                self._warn_prefix = False

            self.create_file(prefix + self._name,
                             self._content if self._content != '' else ' ')
            self._content = ''

        self._name = msg

    def create_file(self, name, content):
        """If the job ID already exists, create task files for every task in the
        backlog and clear it. If it does not, store the new task content in
        the backlog."""
        def _content_to_utf8():
            try:
                return name, content and content.encode('UTF-8')
            except ValueError as ve:
                return "warn/%s" % name, "invalid content, not able to encode to utf-8: %s" % str(ve)

        name, content = _content_to_utf8()
        if self._job_id is None:
            self._backlog.append({'name': name, 'content': content})
        else:
            kwargs = {
                'name': name,
                'content': content,
                'mime': 'application/x-ansible-output',
                'job_id': self._job_id,
                'jobstate_id': self._jobstate_id
            }
            for idx in range(len(self._file_backlog)):
                ret = dci_file.create(self._dci_context,
                                      **self._file_backlog[idx])
                if ret.status_code // 100 != 2:
                    self._file_backlog = self._file_backlog[idx:]
                    self._file_backlog.append(kwargs)
                    return
            self._file_backlog = []
            ret = dci_file.create(self._dci_context, **kwargs)
            if ret.status_code // 100 != 2:
                self._file_backlog.append(kwargs)

    def create_jobstate(self, comment, status):
        if self._explicit:
            return

        if not status or self._current_status == status:
            return

        if self._job_id is None:
            self._backlog.append({'comment': comment, 'status': status})
            return

        self._current_status = status

        r = dci_jobstate.create(
            self._dci_context,
            status=self._current_status,
            comment=comment,
            job_id=self._job_id
        )
        ns = r.json()
        if 'jobstate' in ns and 'id' in ns['jobstate']:
            self._jobstate_id = ns['jobstate']['id']
            os.environ["DCI_JOBSTATE_ID"] = self._jobstate_id

    def v2_playbook_on_stats(self, stats):
        super(CallbackModule, self).v2_playbook_on_stats(stats)
        # do a fake call to banner to output the last content
        self.banner('')

    def v2_runner_on_ok(self, result, **kwargs):
        """Event executed after each command when it succeed. Get the output
        of the command and create a file associated to the current
        jobstate.
        """
        # Store the jobstate id when the there is an explicit call to
        # set it. Example in a playbook:
        #
        # dci_job:
        #   id: "{{ job_id }}"
        #   status: running
        #
        # switch to explicit mode (not reacting to the dci_status
        # variable anymore).
        if ("jobstate" in result._result and
           "id" in result._result["jobstate"]):
            self._jobstate_id = result._result["jobstate"]["id"]
            self._explicit = True
            os.environ["DCI_JOBSTATE_ID"] = self._jobstate_id

        # Check if the task that just run was the schedule of an upgrade
        # job. If so, set self._job_id to the new job ID
        if (result._task.action == 'dci_job' and
            'invocation' in result._result and
            (result._result['invocation']['module_args']['upgrade'] or
             result._result['invocation']['module_args']['update'])):
            self._job_id = result._result['job']['id']
            self.create_jobstate(
                comment='starting the update/upgrade',
                status='pre-run'
            )
        # Capture job_id from a set_fact task (needed for dci-pipeline)
        elif (result._task.action == 'set_fact' and
              'ansible_facts' in result._result and
              'job_id' in result._result['ansible_facts'] and
              result._result['ansible_facts']['job_id'] is not None):

            self._job_id = result._result['ansible_facts']['job_id']
            self.process_backlog()
        # Capture job_id from a dci_job task (job created in playbook)
        elif (result._task.action == 'dci_job' and
              'job' in result._result and
              'id' in result._result['job'] and
              result._result['job']['id'] is not None):

            self._job_id = result._result['job']['id']
            self.process_backlog()

        super(CallbackModule, self).v2_runner_on_ok(result, **kwargs)

    def process_backlog(self):
        self.create_jobstate(comment='start up', status='new')

        for rec in self._backlog:
            if 'status' in rec:
                self.create_jobstate(rec['comment', rec['status']])
            else:
                self.create_file(rec['name'],
                                 rec['content'])
        self._backlog = []

    def v2_playbook_on_play_start(self, play):
        """Event executed before each play. Create a new jobstate and save
        the current jobstate id.
        """

        def _get_comment(play):
            """ Return the comment for the new jobstate

                The order of priority is as follow:

                  * play/vars/dci_comment
                  * play/name
                  * '' (Empty String)
            """

            if play.get_vars() and 'dci_comment' in play.get_vars():
                comment = play.get_vars()['dci_comment']
            # If no name has been specified to the play, play.name is equal
            # to the hosts value
            elif play.name and play.name not in play.hosts:
                comment = play.name
            else:
                comment = ''

            return comment

        super(CallbackModule, self).v2_playbook_on_play_start(play)

        if not self._job_id:
            return

        comment = _get_comment(play)
        self.create_jobstate(
            comment=comment,
            status=play.get_vars().get('dci_status')
        )

    def task_name(self, result):
        """Ensure we alway return a string"""
        name = result._task.get_name()
        # add the included file name in the task's name
        if name == 'include_tasks':
            if hasattr(result._task, 'get_ds'):
                if 'include_tasks' in result._task.get_ds():
                    name = '%s: %s' % (name, result._task.get_ds()['include_tasks'])  # noqa
        return name

    def v2_runner_on_unreachable(self, result):
        self.create_jobstate(comment=self.task_name(result), status='failure')
        super(CallbackModule, self).v2_runner_on_unreachable(result)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Event executed after each command when it fails. Get the output
        of the command and create a failure jobstate and a file associated.
        """
        if not ignore_errors:
            self.create_jobstate(comment=self.task_name(result),
                                 status='failure')

        super(CallbackModule, self).v2_runner_on_failed(result, ignore_errors)

    def v2_runner_item_on_failed(self, result):
        """When a loop item fails, enable a flag for the banner to be formatted
        accordingly.
        """
        self._item_failed = True
        super(CallbackModule, self).v2_runner_item_on_failed(result)
