# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase

import os
from dciclient.v1.api import context as dci_context
from dciclient.v1.api import jobstate as dci_jobstate
from dciclient.v1.api import file as dci_file


class Formatter(object):

    def __init__(self):
        pass

    def format(self, result):

        module_name = result._task.action

        if hasattr(self, 'format_%s' % module_name):
            formatter = getattr(self, 'format_%s' % module_name)
        else:
            formatter = getattr(self, 'format_generic')

        return '%s\n' % formatter(result)

    def format_command(self, result):
        output = ''
        if result._result['stderr']:
            output += 'Stderr:\n%s\nStdout:\n' % result._result['stderr']
        output += result._result['stdout']
        return output

    def format_copy(self, result):
        return 'Copying to file: %s (changed: %s)' % (result._result['dest'],
                                                      result._result['changed'])

    def format_dci_component(self, result):
        return '%s (changed: %s)' % ("METHOD TO IMPLEMENT", result._result['changed'])

    def format_dci_file(self, result):
        return '%s (changed: %s)' % ("METHOD TO IMPLEMENT", result._result['changed'])

    def format_dci_job(self, result):
        return '%s (changed: %s)' % ("METHOD TO IMPLEMENT", result._result['changed'])

    def format_fail(self, result):
        return result._result['msg']

    def format_file(self, result):
        return '\n'.join(['%s: %s (changed: %s)' % (f['path'], f['state'], f['changed']) for f in result._result['results']])

    def format_find(self, result):
        output = 'Examined: %s\nMatched: %s\n\n' % (result._result['examined'], result._result['matched'])
        output += '\n'.join([item['path'] for item in result._result['files']])
        return output

    def format_firewalld(self, result):
        if result._result['module_stderr']:
            return 'Stderr:\n%s' % result._result['module_stderr']
        return result._result['msg']

    def format_generic(self, result):
        return 'All items completed (changed: %s, failed: %s)' % (result._result['changed'], result._result['failed'])

    def format_package(self, result):
        try:
            return '\n'.join([p['results'][0] for p in result._result['results']])
        except:
            return ''.join(result._result['results'])

    def format_service(self, result):
        return 'Service Name: %s, Service State: %s (changed: %s)' % (result._result['name'],
                                                                      result._result['state'],
                                                                      result._result['changed'])

    def format_systemd(self, result):
        return 'Service Name: %s, Service State: %s (changed: %s)' % (result._result['name'],
                                                                      result._result['state'],
                                                                      result._result['changed'])

    def format_template(self, result):
        return 'Copying template to file: %s (changed: %s)' % (result._result['dest'],
                                                               result._result['changed'])

    def format_unarchive(self, result):
        output = ''
        for archive in result._result['results']:
            output += 'Source: %s, Destination: %s\n' % (archive['src'], archive['dest'])
            if 'files' in archive:
                output += '\n'.join(archive['files'])
        return output

    def format_uri(self, result):
        return 'uri'

    def format_user(self, result):
        return 'User: %s (changed: %s)\nSSH Public Key: %s' % (result._result['comment'],
                                                               result._result['changed'],
                                                               result._result['ssh_public_key'])

    def format_yum_repository(self, result):
        return '\n'.join(['File: %s (changed: %s)\n\n%s' % (repo['diff']['after_header'], repo['changed'], repo['diff']['after']) for repo in result._result['results']])


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

        output = Formatter().format(result)

        if result._task.action != 'setup' and self._job_id:
            self.post_message(result, output)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Event executed after each command when it fails. Get the output
        of the command and create a failure jobstate and a file associated.
        """

        super(CallbackModule, self).v2_runner_on_failed(result, ignore_errors)

        output = Formatter().format(result)

        if ignore_errors:
            self.post_message(result, output)
            return

        new_state = dci_jobstate.create(
            self._dci_context,
            status='failure',
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
        status = None
        comment = _get_comment(play)
        fact_cache = play._variable_manager._nonpersistent_fact_cache
        if play.get_vars():
            status = play.get_vars().get('dci_status')
            if 'dci_mime_type' in play.get_vars():
                self._mime_type = play.get_vars()['dci_mime_type']
            else:
                self._mime_type = 'text/plain'

        if status:
            if not self._job_id:
                for hostvar in fact_cache:
                    if 'job_informations' in fact_cache[hostvar]:
                        self._job_id = \
                            fact_cache[hostvar]['job_informations']['id']
                        break

            ns = dci_jobstate.create(self._dci_context, status=status,
                                     comment=comment,
                                     job_id=self._job_id).json()
            self._jobstate_id = ns['jobstate']['id']
