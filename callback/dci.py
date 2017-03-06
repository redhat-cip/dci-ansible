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
from dciclient.v1.api import remoteci as dci_remoteci


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

        if 'stderr' in result and result['stderr']:
            if result['stdout']:
                output = 'Error Output:\n\n%s\n\nStandard Output:\n\n%s' % (
                    result['stderr'], result['stdout']
                )
            else:
                output = result['stderr']

        else:
            # The following if/elif/else block is due to lack of consistency in the object
            # returned by ansible. Ideally the result['invocation']['module_name'] should
            # work for all modules.
            if 'invocation' not in result:
                module_name = 'file'
            elif 'extract_result' in result:
                module_name = 'unarchive'
            elif 'module_name' not in result['invocation']:
                module_name = 'package'
            else:
                module_name = result['invocation']['module_name']

            if module_name == 'os_server':
                output = '%s - %s' % (result['server']['status'], result['server']['id'])
            elif module_name == 'hostname':
                output = 'Hostname: %s' % result['name']
            elif module_name == 'user':
                output = 'Name: %s - uid: %s - gid: %s' % (result['name'], result['uid'], result['group'])
            elif module_name == 'lineinfile':
                output = '%s - %s' % (result['invocation']['module_args']['line'], result['msg'])
            elif module_name == 'get_url':
                output = '%s - %s' % (result['dest'], result['msg'])
            elif module_name == 'unarchive':
                output = '%s unarchived in %s' % (result['src'], result['dest'])
            elif module_name == 'package':
                output = result['results']
            elif 'stdout_lines' in result:
                output = '\n'.join(result['stdout_lines'])
            elif 'msg' in result:
                output = result['msg']
            else:
                output = 'All items completed'

        return '%s\n' % output

    def __init__(self):

        super(CallbackModule, self).__init__()

        self._mime_type = None
        self._job_id = None
        self._remoteci_id = None
        self._dci_context = self._build_dci_context()
        self._previous_job_id = self.get_current_job_id()

    def remoteci_id(self):
        if self._remoteci_id:
            return self._remoteci_id
        r = dci_remoteci.list(self._dci_context, where='name:' + self.config['remoteci'], limit=1)
        self._remoteci_id = r.json()['remotecis'][0]['id']
        return self._remoteci_id

    def get_current_job_id(self):
        r = dci_job.list(self._dci_context, where='remoteci_id:' + self.remoteci_id(), limit=1)
        if not len(r.json()['jobs']):
            return
        return r.json()['jobs'][0]['id']

    def job_id(self):
        if self._job_id:
            return self._job_id
        current_job_id = self.get_current_job_id()
        if current_job_id != self._previous_job_id:
            self._job_id = current_job_id
        return self._job_id

    def jobstate_id(self):
        job_id = self.job_id()
        if not job_id:
            return
        r = dci_jobstate.list(self._dci_context, where='job_id:' + self.job_id(), sort='created_at', limit=1)
        if not len(r.json()['jobstates']):
            return
        last_jobstate = r.json()['jobstates'][0]
        return last_jobstate['id']

    def v2_runner_on_ok(self, result, **kwargs):
        """Event executed after each command when it succeed. Get the output
        of the command and create a file associated to the current
        jobstate.
        """

        super(CallbackModule, self).v2_runner_on_ok(result, **kwargs)

        output = self.format_output(result._result)

        if (result._task.get_name() != 'setup' and
                self._mime_type == 'application/junit'):
            r = dci_file.create(
                self._dci_context,
                name=result._task.get_name().encode('UTF-8'),
                content=output.encode('UTF-8'),
                mime=self._mime_type,
                job_id=self.job_id())
        elif result._task.get_name() != 'setup' and output != '\n':
            r = dci_file.create(
                self._dci_context,
                name=result._task.get_name().encode('UTF-8'),
                content=output.encode('UTF-8'),
                mime=self._mime_type,
                jobstate_id=self.jobstate_id())

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Event executed after each command when it fails. Get the output
        of the command and create a failure jobstate and a file associated.
        """

        super(CallbackModule, self).v2_runner_on_failed(result, ignore_errors)

        output = self.format_output(result._result)

        new_state = dci_jobstate.create(
            self._dci_context,
            status='failure',
            comment='',
            job_id=self.job_id()).json()
        self._jobstate_id = new_state['jobstate']['id']
        r = dci_file.create(
            self._dci_context,
            name=result._task.get_name().encode('UTF-8'),
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

        if status and self.job_id():
            ns = dci_jobstate.create(self._dci_context, status=status,
                                     comment=comment, job_id=self.job_id()).json()
            self._jobstate_id = ns['jobstate']['id']
