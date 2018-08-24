# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase

import base64
import os
from dciclient.v1.api import context as dci_context
from dciclient.v1.api import jobstate as dci_jobstate
from dciclient.v1.api import file as dci_file
from ansible.release import __version__ as ansible_version
from dciclient.version import __version__ as dciclient_version
from dciauth.version import __version__ as dciauth_version


class Formatter(object):

    def __init__(self):
        pass

    @staticmethod
    def _get_result_entries(result):
        if 'results' in result._result:
            return result._result['results']
        else:
            return [result._result]

    def format(self, result):

        module_name = result._task.action
        msg = ''
        if result._result.get('msg'):
            msg += result._result['msg']
            msg += '\n'

        if hasattr(self, 'format_%s' % module_name):
            formatter = getattr(self, 'format_%s' % module_name)
        else:
            formatter = getattr(self, 'format_generic')

        return '%s%s' % (msg, formatter(result) or '')

    def format_add_host(self, result):
        if 'msg' in result._result:
            return ''
        add_host = result._result['add_host']
        output = "Adding host '%s'" % add_host['host_name']
        if 'host_vars' in add_host and add_host['host_vars']:
            output += ' (%s)' % str(add_host['host_vars'])
        if 'groups' in add_host and add_host['groups']:
            output += ' into groups (%s)' % ''.join(add_host['groups'])
        output += ' in current inventory'
        return output

    def format_authorized_key(self, result):
        if 'msg' in result._result:
            return ''
        return 'Adding authorized_key for user: %s (changed: %s)\nKey: %s' % (
            result._result.get('user'),
            result._result.get('changed'),
            result._result.get('key'))

    def format_command(self, result):
        output = ''
        if result._result.get('stderr'):
            output += 'Stderr:\n%s\nStdout:\n' % result._result.get('stderr')
        if result._result.get('stdout'):
            output += result._result.get('stdout')
        return output

    def format_copy(self, result):
        if 'msg' in result._result:
            return ''
        return 'Copying to file: %s (changed: %s)' % (
            result._result.get('dest'),
            result._result.get('changed'))

    def format_dci_topic(self, result):
        try:
            return str(result._result['topic'])
        except Exception:
            return str(result._result)

    def format_dci_component(self, result):
        ret = ''
        for c in self._get_result_entries(result):
            ret += 'Downloading %s(%s) in %s' % (
                c['item'].get('canonical_project_name'),
                c['item'].get('name'),
                c['invocation']['module_args'].get('dest'))
        return ret

    def format_dci_file(self, result):
        ret = ''
        for c in self._get_result_entries(result):
            l_file = c['invocation']['module_args']
            ret += (
                'Uploading %s (filename: %s - mimetype: %s) ',
                '(details: %s)\n') % (
                    l_file.get('path'),
                    l_file.get('name'),
                    l_file.get('mime'),
                    c.get('msg'))
        return ret

    def format_file(self, result):
        ret = ''
        for c in self._get_result_entries(result):
            ret += "%s: %s (changed: %s)\n" % (
                c.get('path'),
                c.get('state'),
                c.get('changed'))
        return ret

    def format_find(self, result):
        output = 'Examined: %s\nMatched: %s\n\n' % (
            result._result.get('examined'),
            result._result.get('matched'))
        for item in result._result.get('files', []):
            output += item.get('path')
            output += '\n'
        return output

    def format_firewalld(self, result):
        if result._result.get('module_stderr'):
            return 'Stderr:\n%s' % result._result['module_stderr']

    def format_generic(self, result):
        changed = result._result.get('changed')
        return 'All items completed (changed: %s)' % changed

    def format_ini_file(self, result):
        ret = ''
        for c in self._get_result_entries(result):
            m_args = c['invocation']['module_args']
            ret += '%s - (changed: %s)\nMessage: %s (%s.%s=%s)\n' % (
                c.get('path'),
                c.get('changed'),
                c.get('msg'),
                m_args.get('section'),
                m_args.get('option'),
                m_args.get('value'))
        return ret

    def format_lineinfile(self, result):
        m_args = result._result['invocation']['module_args']
        output = '%s - (changed: %s)' % (
            m_args.get('dest'),
            result._result.get('changed'))
        output += '\nLine: %s' % m_args.get('line')
        return output

    def format_package(self, result):
        ret = ''
        for c in self._get_result_entries(result):
            if 'results' in c:
                ret += c['results'][0] + '\n'
        return ret

    def format_set_fact(self, result):
        ret = 'Settings the following facts:\n\n'
        for c in self._get_result_entries(result):
            for key, value in c.get('ansible_facts', {}).iteritems():
                ret += '%s: %s\n' % (key, value)
        return ret

    def format_service(self, result):
        return 'Service Name: %s, Service State: %s (changed: %s)' % (
            result._result.get('name'),
            result._result.get('state'),
            result._result.get('changed'))

    def format_slurp(self, result):
        if 'msg' in result._result:
            return ''
        return 'Slurping content of %s\n\n%s' % (
            result._result.get('source'),
            base64.b64decode(result._result.get('content')))

    def format_stat(self, result):
        m_args = result._result['invocation']['module_args']
        return '%s: Stat %s' % (
            m_args.get('path'),
            str(result._result.get('stat')))

    def format_systemd(self, result):
        return 'Service Name: %s, Service State: %s (changed: %s)' % (
            result._result.get('name'),
            result._result.get('state'),
            result._result.get('changed'))

    def format_template(self, result):
        return 'Copying template to file: %s (changed: %s)' % (
            result._result.get('dest'),
            result._result.get('changed'))

    def format_unarchive(self, result):
        ret = ''
        for c in self._get_result_entries(result):
            ret += 'Source: %s, Destination: %s\n' % (
                c.get('src'), c.get('dest'))
            if 'files' in c:
                ret += '\n'.join(c['files'])
        return ret

    def format_user(self, result):
        return 'User: %s (changed: %s)\nSSH Public Key: %s' % (
            result._result.get('comment'),
            result._result.get('changed'),
            result._result.get('ssh_public_key'))

    def format_yum_repository(self, result):
        ret = ''
        for c in self._get_result_entries(result):
            ret += 'File: %s (changed: %s)\n\n%s' % (
                c.get('diff', {}).get('after_header'),
                c.get('changed'),
                c.get('diff', {}).get('after'))
        return ret

    def format_debug(self, result):
        if 'msg' in result._result:
            return ''
        result = result._result
        for k in result.keys():
            if k.startswith('_ansible'):
                del result[k]
        return str(result)


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
        user_agent = ('Ansible/%s (python-dciclient/%s, python-dciauth/%s)'
                     ) % (ansible_version, dciclient_version, dciauth_version)
        if login is not None and password is not None:
            return dci_context.build_dci_context(url, login, password,
                                                 user_agent)
        elif client_id is not None and api_secret is not None:
            return dci_context.build_signature_context(url, client_id,
                                                       api_secret, user_agent)

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
