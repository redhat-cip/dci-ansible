# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from datetime import datetime

from ansible.plugins.callback import CallbackBase


import os
from dciclient.v1.api import context as dci_context
from dciclient.v1.api import jobstate as dci_jobstate
from dciclient.v1.api import job as dci_job
from dciclient.v1.api import file as dci_file

FIELDS = ['cmd', 'command', 'start', 'end', 'delta', 'msg', 'stdout', 'stderr', 'module_stdout', 'module_stderr', 'item']


class CallbackModule(CallbackBase):
    """
    This callback module tells you how long your plays ran for.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'dci'
    CALLBACK_NEEDS_WHITELIST = True

    def _build_dci_context(self):
        return dci_context.build_dci_context(os.getenv('DCI_CS_URL'), os.getenv('DCI_LOGIN'),
                                             os.getenv('DCI_PASSWORD'), 'ansible')

    def format_output(self, result):
        """ Return the proper output for a given task output.

            There is no standard about which variable should hold the task
            output. It is generally available in 'stdout' but this is not
            true for all the tasks. This function returns the most meaningful
            value.
        """

        output = ''
        if type(result) == type(dict()):
            for field in FIELDS:
                if field in result.keys():
                    if not field:
                        continue
                    output += '\n{0}: {1}'.format(field, result[field])
        return output

    def post_message(self, result, output):
        dci_file.create(
            self._dci_context,
            name=self.task_name(result),
            content=output.encode('UTF-8'),
            mime=self._mime_type,
            jobstate_id=self._jobstate_id)

    def task_name(self, result):
        """Ensure we alway return a string"""
        name = result._task.get_name()
        if name:
            return name.encode('UTF-8')
        else:
            return ''

    def __init__(self):

        super(CallbackModule, self).__init__()

        self._mime_type = None
        self._jobstate_id = None
        self._job_id = None
        self._dci_context = self._build_dci_context()

    def v2_runner_on_ok(self, result, **kwargs):
        """Event executed after each command when it succeed. Get the output
        of the command and create a file associated to the current
        jobstate.
        """

        super(CallbackModule, self).v2_runner_on_ok(result, **kwargs)

        output = self.format_output(result._result)

        if (self._mime_type == 'application/junit'):
            dci_file.create(
                self._dci_context,
                name=task_name(result),
                content=output and output.encode('UTF-8'),
                mime=self._mime_type,
                job_id=self._job_id)
            return

        if self.task_name(result) != 'setup':
            self.post_message(result, output)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Event executed after each command when it fails. Get the output
        of the command and create a failure jobstate and a file associated.
        """

        super(CallbackModule, self).v2_runner_on_failed(result, ignore_errors)

        output = self.format_output(result._result)

        if ignore_errors:
            self.post_message(result, output)
            return

        new_state = dci_jobstate.create(
            self._dci_context,
            status='failure',
            comment=self.task_name(result),
            job_id=self._job_id).json()
        self._jobstate_id = new_state['jobstate']['id']
        dci_file.create(
            self._dci_context,
            name=self.task_name(result),
            content=output.encode('UTF-8'),
            mime=self._mime_type,
            jobstate_id=self._jobstate_id)

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
        status = None
        comment = _get_comment(play)
        if play.get_vars():
            status = play.get_vars().get('dci_status')
            if 'dci_mime_type' in play.get_vars():
                self._mime_type = play.get_vars()['dci_mime_type']
            else:
                self._mime_type = 'text/plain'

        if status:
            self._job_id = dci_job.list(self._dci_context).json()['jobs'][0]['id']
            ns = dci_jobstate.create(self._dci_context, status=status,
                                     comment=comment, job_id=self._job_id).json()
            self._jobstate_id = ns['jobstate']['id']
