# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase


import os
from dciclient.v1.api import context as dci_context
from dciclient.v1.api import jobstate as dci_jobstate
from dciclient.v1.api import file as dci_file


class CallbackModule(CallbackBase):
    """
    This callback module tells you how long your plays ran for.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'dci'
    CALLBACK_NEEDS_WHITELIST = True

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
        if login is not None and password is not None:
            return dci_context.build_dci_context(url, login, password,
                                                 'Ansible')
        elif client_id is not None and api_secret is not None:
            return dci_context.build_signature_context(url, client_id,
                                                       api_secret, 'Ansible')

    def format_output(self, result):
        """ Return the proper output for a given task output.

            There is no standard about which variable should hold the task
            output. It is generally available in 'stdout' but this is not
            true for all the tasks. This function returns the most meaningful
            value.
        """

        if 'stderr' in result and result['stderr']:
            if result['stdout']:
                output = 'Error Output:\n\n%s\n\nStandard Output:\n\n%s' % (
                    result['stderr'], result['stdout']
                )
            else:
                output = result['stderr']

        else:
            if 'invocation' not in result:
                module_name = 'file'
            elif 'extract_result' in result:
                module_name = 'unarchive'
            elif 'module_name' not in result['invocation']:
                module_name = 'package'
            else:
                module_name = result['invocation']['module_name']

            if module_name == 'os_server':
                output = '%s - %s' % (result['server']['status'],
                                      result['server']['id'])
            elif module_name == 'hostname':
                output = 'Hostname: %s' % result['name']
            elif module_name == 'user':
                output = 'Name: %s - uid: %s - gid: %s' % (result['name'],
                                                           result['uid'],
                                                           result['group'])
            elif module_name == 'lineinfile':
                output = '%s - %s' % (
                    result['invocation']['module_args']['line'], result['msg']
                )
            elif module_name == 'get_url':
                output = '%s - %s' % (result['dest'], result['msg'])
            elif module_name == 'unarchive':
                output = '%s unarchived in %s' % (
                    result['src'], result['dest']
                )
            elif 'stdout_lines' in result:
                output = '\n'.join(result['stdout_lines'])
            elif 'msg' in result:
                output = result['msg']
            else:
                output = 'All items completed'

        return '%s\n' % output

    def post_message(self, result, output):
        kwargs = {
            'name': self.task_name(result),
            'content': output and output.encode('UTF-8'),
            'mime': self._mime_type}

        kwargs['job_id'] = self._job_id
        if not self._mime_type == 'application/junit':
            kwargs['jobstate_id'] = self._jobstate_id
        dci_file.create(
            self._dci_context,
            **kwargs)

    def task_name(self, result):
        """Ensure we alway return a string"""
        name = result._task.get_name()
        return name.encode('UTF-8')

    def __init__(self):

        super(CallbackModule, self).__init__()

        self._mime_type = None
        self._jobstate_id = None
        self._job_id = None
        self._current_status = None
        self._dci_context = self._build_dci_context()

    def v2_runner_on_ok(self, result, **kwargs):
        """Event executed after each command when it succeed. Get the output
        of the command and create a file associated to the current
        jobstate.
        """

        super(CallbackModule, self).v2_runner_on_ok(result, **kwargs)
        # Check if the task that just run was the schedule of an upgrade
        # job. If so, set self._job_id to the new job ID

        if (result._task.action == 'dci_job' and (
                result._result['invocation']['module_args']['upgrade'] or
                result._result['invocation']['module_args']['update'])):
            self._job_id = result._result['job']['id']

            ns = dci_jobstate.create(self._dci_context, status='pre-run',
                                     comment='starting the update/upgrade',
                                     job_id=self._job_id).json()
            self._jobstate_id = ns['jobstate']['id']

        output = self.format_output(result._result)

        if result._task.action != 'setup' and self._job_id:
            self.post_message(result, output)

    def v2_runner_on_unreachable(self, result):
        super(CallbackModule, self).v2_runner_on_unreachable(result)
        new_state = dci_jobstate.create(
            self._dci_context,
            status='failure',
            comment=self.task_name(result),
            job_id=self._job_id).json()
        self._jobstate_id = new_state['jobstate']['id']
        self.post_message(result, result._result['msg'])

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Event executed after each command when it fails. Get the output
        of the command and create a failure jobstate and a file associated.
        """

        super(CallbackModule, self).v2_runner_on_failed(result, ignore_errors)

        output = self.format_output(result._result)

        if ignore_errors:
            self.post_message(result, output)
            return

        if self._current_status in ['new', 'pre-run']:
            status = 'error'
        else:
            status = 'failure'

        new_state = dci_jobstate.create(
            self._dci_context,
            status=status,
            comment=self.task_name(result),
            job_id=self._job_id).json()
        self._jobstate_id = new_state['jobstate']['id']
        self.post_message(result, output)

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
                comment = play.get_vars()['dci_comment'].encode('UTF-8')
            # If no name has been specified to the play, play.name is equal
            # to the hosts value
            elif play.name and play.name not in play.hosts:
                comment = play.name.encode('UTF-8')
            else:
                comment = ''

            return comment

        super(CallbackModule, self).v2_playbook_on_play_start(play)
        comment = _get_comment(play)
        fact_cache = play._variable_manager._nonpersistent_fact_cache
        if play.get_vars():
            self._current_status = play.get_vars().get('dci_status')
            if 'dci_mime_type' in play.get_vars():
                self._mime_type = play.get_vars()['dci_mime_type']
            else:
                self._mime_type = 'text/plain'

        if self._current_status:
            if not self._job_id:
                for hostvar in fact_cache:
                    if 'job_informations' in fact_cache[hostvar]:
                        self._job_id = \
                            fact_cache[hostvar]['job_informations']['id']
                        break

            ns = dci_jobstate.create(self._dci_context, status=self._current_status,
                                     comment=comment,
                                     job_id=self._job_id).json()
            self._jobstate_id = ns['jobstate']['id']
