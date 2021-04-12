# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase

import os
import json
from dciclient.v1.api import context as dci_context
from dciclient.v1.api import jobstate as dci_jobstate
from dciclient.v1.api import file as dci_file
from ansible.release import __version__ as ansible_version
from dciclient.version import __version__ as dciclient_version
from dciauth.version import __version__ as dciauth_version


def remove_duplicated_content(result):
    try:
        new_result = dict(result)
        duplicated_keys = (
            (
                "stdout",
                "stdout_lines",
            ),
            (
                "stderr",
                "stderr_lines",
            ),
        )
        for keys in duplicated_keys:
            key_to_keep = keys[0]
            key_to_remove = keys[1]
            if key_to_keep in new_result and key_to_remove in new_result:
                del new_result[key_to_remove]

        return new_result
    except:  # noqa
        return result


class CallbackModule(CallbackBase):
    """
    This callback module tells you how long your plays ran for.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'dci'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):

        super(CallbackModule, self).__init__()

        self._jobstate_id = None
        self._job_id = None
        self._current_status = None
        self._dci_context = self._build_dci_context()
        self._explicit = False

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

    def create_file(self, name, content):
        kwargs = {
            'name': name,
            'content': content and content.encode('UTF-8'),
            'mime': 'application/x-ansible-output'
        }
        kwargs['job_id'] = self._job_id
        kwargs['jobstate_id'] = self._jobstate_id
        dci_file.create(self._dci_context, **kwargs)

    def post_message(self, result, output):
        name = self.task_name(result)
        self.create_file(name, output)

    def post_skipped_message(self, result, output):
        name = "skipped/%s" % self.task_name(result)
        self.create_file(name, output)

    def post_failed_message(self, result, output):
        name = "failed/%s" % self.task_name(result)
        self.create_file(name, output)

    def post_ignored_message(self, result, output):
        name = "ignored/%s" % self.task_name(result)
        self.create_file(name, output)

    def post_unreachable_message(self, result, output):
        name = "unreachable/%s" % self.task_name(result)
        self.create_file(name, output)

    def post_item_message(self, result, output, name_prefix=None):
        name = result._result['item']
        if name_prefix:
            name = "%s/%s" % (name_prefix, name)
        self.create_file(name, output)

    def create_jobstate(self, comment, status=None):
        if self._explicit:
            return

        if status:
            self._current_status = status

        r = dci_jobstate.create(
            self._dci_context,
            status=self._current_status,
            comment=comment,
            job_id=self._job_id
        )
        ns = r.json()
        self._jobstate_id = ns['jobstate']['id']

    def task_name(self, result):
        """Ensure we alway return a string"""
        name = result._task.get_name()
        # add the included file name in the task's name
        if name == 'include_tasks':
            if hasattr(result._task, 'get_ds'):
                if 'include_tasks' in result._task.get_ds():
                    name = '%s: %s' % (name, result._task.get_ds()['include_tasks'])  # noqa
        return name

    def v2_runner_on_ok(self, result, **kwargs):
        """Event executed after each command when it succeed. Get the output
        of the command and create a file associated to the current
        jobstate.
        """

        super(CallbackModule, self).v2_runner_on_ok(result, **kwargs)
        # Check if the task that just run was the schedule of an upgrade
        # job. If so, set self._job_id to the new job ID

        # Store the jobstate id when the there is an explicit call to
        # set it. Example in a playbook:
        #
        # dci_job:
        #   id: "{{ job_id }}"
        #   status: running
        if ("jobstate" in result._result and
           "id" in result._result["jobstate"]):
            self._jobstate_id = result._result["jobstate"]["id"]
            self._explicit = True

        if (result._task.action == 'dci_job' and (
                result._result['invocation']['module_args']['upgrade'] or
                result._result['invocation']['module_args']['update'])):

            self._job_id = result._result['job']['id']
            self.create_jobstate(
                comment='starting the update/upgrade',
                status='pre-run'
            )
        elif (result._task.action == 'set_fact' and
              'job_id' in result._result['ansible_facts']):
            if self._job_id is None:
                self._job_id = result._result['ansible_facts']['job_id']
                self.create_jobstate(comment='start up', status='new')

        cleaned_result = remove_duplicated_content(result._result)
        output = json.dumps(cleaned_result, indent=2)

        if result._task.action != 'setup' and self._job_id:
            self.post_message(result, output)

    def v2_runner_on_unreachable(self, result):

        if not self._job_id:
            return

        super(CallbackModule, self).v2_runner_on_unreachable(result)
        self.create_jobstate(comment=self.task_name(result), status='failure')
        self.post_unreachable_message(result, "msg:%s\n%s" % json.dumps(result._result['results']))  # noqa

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Event executed after each command when it fails. Get the output
        of the command and create a failure jobstate and a file associated.
        """

        if not self._job_id:
            return

        super(CallbackModule, self).v2_runner_on_failed(result, ignore_errors)

        cleaned_result = remove_duplicated_content(result._result)
        output = json.dumps(cleaned_result, indent=2)

        if ignore_errors:
            self.post_ignored_message(result, output)
            return

        self.create_jobstate(comment=self.task_name(result), status='failure')
        self.post_failed_message(result, output)

    def v2_runner_on_skipped(self, result):
        super(CallbackModule, self).v2_runner_on_skipped(result)
        if not self._job_id:
            return
        self.post_skipped_message(result, result._result['skip_reason'])

    def v2_playbook_on_play_start(self, play):
        """Event executed before each play. Create a new jobstate and save
        the current jobstate id.
        """

        if not self._job_id:
            return

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

        comment = _get_comment(play)
        self.create_jobstate(
            comment=comment,
            status=play.get_vars().get('dci_status')
        )

    def v2_runner_item_on_ok(self, result):
        if not self._job_id:
            return

        super(CallbackModule, self).v2_runner_item_on_ok(result)
        self.post_item_message(result, result._result['msg'], 'item_ok')

    def v2_runner_item_on_failed(self, result):
        if not self._job_id:
            return

        super(CallbackModule, self).v2_runner_item_on_failed(result)
        self.post_item_message(result, result._result['msg'], 'item_failed')

    def v2_runner_item_on_skipped(self, result):
        if not self._job_id:
            return

        super(CallbackModule, self).v2_runner_item_on_skipped(result)
        self.post_item_message(result, result._result['msg'], 'item_failed')
