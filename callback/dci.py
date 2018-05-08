# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase

import base64
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

    def format_add_host(self, result):
        add_host = result._result['add_host']
        output = "Adding host '%s'" % add_host['host_name']
        if 'host_vars' in add_host and add_host['host_vars']:
            output += ' (%s)' % str(add_host['host_vars'])
        if 'groups' in add_host and add_host['groups']:
            output += ' into groups (%s)' % ''.join(add_host['groups'])
        output += ' in current inventory'
        return output

    def format_authorized_key(self, result):
        return 'Adding authorized_key for user: %s (changed: %s)\nKey: %s' % (
            result._result['user'],
            result._result['changed'],
            result._result['key'])

    def format_command(self, result):
        output = ''
        if result._result['stderr']:
            output += 'Stderr:\n%s\nStdout:\n' % result._result['stderr']
        output += result._result['stdout']
        return output

    def format_copy(self, result):
        return 'Copying to file: %s (changed: %s)' % (
            result._result['dest'],
            result._result['changed'])

    def format_dci_topic(self, result):
        try:
            return str(result._result['topic'])
        except Exception:
            return str(result._result)

    def format_dci_component(self, result):
        try:
            return '\n'.join(
                ['Downloading %s(%s) in %s' % (
                    c['item']['canonical_project_name'],
                    c['item']['name'],
                    c['invocation']['module_args']['dest'])
                 for c in result._result['results']]
            )
        except Exception:
            return str(result._result)

    def format_dci_file(self, result):
        try:
            ret = ''
            for c in result._result['results']:
                l_file = c['invocation']['module_args']
                ret += (
                    'Uploading %s (filename: %s - mimetype: %s) ',
                    '(details: %s)\n') % (
                        l_file['path'],
                        l_file['name'],
                        l_file['mime'],
                    c.get('msg'))
            return ret
        except Exception:
            l_file = result._result['invocation']['module_args']
            return (
                'Uploading %s (filename: ',
                '%s - mimetype: %s) (details: %s)' % (
                    l_file['path'], l_file['name'],
                    l_file['mime'], result._result.get('msg')))

    def format_debug(self, result):
        return result._result['msg']

    def format_fail(self, result):
        return result._result['msg']

    def format_file(self, result):
        try:
            ret = ''
            for f in result._result['results']:
                ret += "%s: %s (changed: %s)\n" % (
                    f['path'],
                    f['state'],
                    f['changed'])
            return ret
        except Exception:
            return '%s: %s (changed: %s)' % (
                result._result['path'],
                result._result['state'],
                result._result['changed'])

    def format_find(self, result):
        output = 'Examined: %s\nMatched: %s\n\n' % (
            result._result['examined'],
            result._result['matched'])
        output += '\n'.join([item['path'] for item in result._result['files']])
        return output

    def format_firewalld(self, result):
        if result._result.get('module_stderr'):
            return 'Stderr:\n%s' % result._result['module_stderr']
        return result._result['msg']

    def format_generic(self, result):
        return 'All items completed (changed: %s)' % result._result['changed']

    def format_ini_file(self, result):
        try:
            ret = ''
            for ini in result._result['results']:
                m_args = ini['invocation']['module_args']
                ret += '%s - (changed: %s)\nMessage: %s (%s.%s=%s)\n' % (
                    ini['path'],
                    ini['changed'],
                    ini['msg'],
                    m_args['section'],
                    m_args['option'],
                    m_args['value'])
            return ret
        except Exception:
            return '%s - (changed: %s)\nMessage: %s (%s.%s=%s)' % (
                result._result['path'],
                result._result['changed'],
                result._result['msg'],
                result._result['invocation']['module_args']['section'],
                result._result['invocation']['module_args']['option'],
                result._result['invocation']['module_args']['value'])

    def format_lineinfile(self, result):
        m_args = result._result['invocation']['module_args']
        output = '%s - (changed: %s)' % (
            m_args['dest'],
            result._result['changed'])
        if result._result['msg']:
            output += '\nMessage: %s' % result._result['msg']
        output += '\nLine: %s' % m_args['line']
        return output

    def format_package(self, result):
        if 'msg' in result._result:
            return result._result['msg']
        try:
            ret = ''
            for p in result._result['results']:
                ret += p['results'][0] + '\n'
            return ret
        except Exception:
            return ''.join(result._result['results'])

    def format_set_fact(self, result):
        ret = 'Settings the following facts:\n\n'
        for key, value in result._result['ansible_facts'].iteritems():
            ret += '%s: %s' % (key, value)
        return ret

    def format_service(self, result):
        return 'Service Name: %s, Service State: %s (changed: %s)' % (
            result._result['name'],
            result._result['state'],
            result._result['changed'])

    def format_slurp(self, result):
        return 'Slurping content of %s\n\n%s' % (
            result._result['source'],
            base64.b64decode(result._result['content']))

    def format_stat(self, result):
        m_args = result._result['invocation']['module_args']
        return '%s: Stat %s' % (m_args['path'], str(result._result['stat']))

    def format_systemd(self, result):
        return 'Service Name: %s, Service State: %s (changed: %s)' % (
            result._result['name'],
            result._result['state'],
            result._result['changed'])

    def format_template(self, result):
        return 'Copying template to file: %s (changed: %s)' % (
            result._result['dest'],
            result._result['changed'])

    def format_unarchive(self, result):
        output = ''
        for archive in result._result['results']:
            output += 'Source: %s, Destination: %s\n' % (
                archive['src'], archive['dest'])
            if 'files' in archive:
                output += '\n'.join(archive['files'])
        return output

    def format_user(self, result):
        return 'User: %s (changed: %s)\nSSH Public Key: %s' % (
            result._result['comment'],
            result._result['changed'],
            result._result['ssh_public_key'])

    def format_yum_repository(self, result):
        ret = ''
        for repo in result._result['results']:
            ret += 'File: %s (changed: %s)\n\n%s' % (
                repo['diff']['after_header'],
                repo['changed'],
                repo['diff']['after'])
        return ret


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

    def create_jobstate(self, comment, status=None):
        if status:
            self._current_status = status

        r = dci_jobstate.create(
            self._dci_context,
            status=self._current_status,
            comment=comment,
            job_id=self._job_id)
        ns = r.json()
        self._jobstate_id = ns['jobstate']['id']

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
            self.create_jobstate(
                comment='starting the update/upgrade',
                status='pre-run')

        elif (result._task.action == 'dci_job' and
              result._result['invocation']['module_args']['topic'] and
              not result._result['invocation']['module_args']['id']):

            self._job_id = result._result['job']['id']
            self.create_jobstate(comment='start up', status='new')

        try:
            output = Formatter().format(result)
        except Exception as e:
            output = (
                'An error while parsing the output occured, '
                'please reach to distributed-ci@redhat.com: %s' % e)

        if result._task.action != 'setup' and self._job_id:
            self.post_message(result, output)

    def v2_runner_on_unreachable(self, result):

        if not self._job_id:
            return

        super(CallbackModule, self).v2_runner_on_unreachable(result)
        self.create_jobstate(status='failure', comment=self.task_name(result))
        self.post_message(result, result._result['msg'])

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Event executed after each command when it fails. Get the output
        of the command and create a failure jobstate and a file associated.
        """

        if not self._job_id:
            return

        super(CallbackModule, self).v2_runner_on_failed(result, ignore_errors)

        try:
            output = Formatter().format(result)
        except Exception as e:
            output = (
                'An error while parsing the output occured, '
                'please reach to distributed-ci@redhat.com: %s' % e)

        if ignore_errors:
            self.post_message(result, output)
            return

        if self._current_status in ['new', 'pre-run']:
            status = 'error'
        else:
            status = 'failure'

        self.create_jobstate(status=status, comment=self.task_name(result))
        self.post_message(result, output)

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
        self.create_jobstate(
            comment=comment,
            status=play.get_vars().get('dci_status'))
