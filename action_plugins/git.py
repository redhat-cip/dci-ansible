#
# Copyright (C) 2020-2022 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible import errors as ansible_errors
from ansible.plugins.action import ActionBase
from ansible.release import __version__ as ansible_version

from dciauth.version import __version__ as dciauth_version
from dciclient.v1.api import context as dci_context
from dciclient.version import __version__ as dciclient_version

import os
import os.path

try:
    from dciclient.v1.api import component as dci_component
    from dciclient.v1.api import job as dci_job
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True

import sys

if sys.version_info >= (3, 0):
    from urllib.parse import urlparse
if sys.version_info < (3, 0) and sys.version_info >= (2, 5):
    from urlparse import urlparse  # noqa


class ActionModule(ActionBase):

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

    def _git_to_reproduce(self, repo_name, components):
        for git_component in components:
            if git_component['type'] != repo_name:
                continue
            # support both naming: <commit id> or <repo name>=<commit id>
            split_git_component = git_component['name'].split("=")
            if len(split_git_component) == 2:
                return split_git_component[1]
            else:
                return git_component['name']
        return None

    def _get_repo_project_name(self, repo):
        repo_parsed = urlparse(repo)
        if repo_parsed.path.endswith('.git'):
            return os.path.basename(repo_parsed.path.replace('.git', ''))
        return os.path.basename(repo_parsed.path)

    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        git_args = self._task.args.copy()

        if 'job_info' in task_vars:
            ctx = self._build_dci_context()
            job_id = task_vars['job_info']['job']['id']
            team_id = task_vars['job_info']['job']['team_id']
            topic_id = task_vars['job_info']['job']['topic_id']
            components = task_vars['job_info']['job']['components']
            _project_name = self._get_repo_project_name(git_args['repo'])

            commit_id = self._git_to_reproduce(_project_name, components)
            if commit_id:
                git_args['version'] = commit_id
                return self._execute_module(module_name='git',
                                            module_args=git_args,
                                            task_vars=task_vars, tmp=tmp)

        module_return = self._execute_module(module_name='git',
                                             module_args=git_args,
                                             task_vars=task_vars, tmp=tmp)

        if 'failed' in module_return or 'job_info' not in task_vars:
            return module_return

        _commit_id = module_return['after']
        if git_args['repo'].endswith('.git'):
            git_args['repo'] = git_args['repo'].replace('.git', '')
        cmpt_name = _commit_id
        cmpt_url = "%s/commit/%s" % (git_args['repo'], _commit_id)

        repo_name = urlparse(git_args['repo'])
        repo_name = repo_name.path

        cmpt, _ = dci_component.get_or_create(
            ctx,
            name=cmpt_name,
            team_id=team_id,
            topic_id=topic_id,
            type=_project_name,
            defaults={
                "canonical_project_name": "%s %s" % (_project_name,
                                                     _commit_id[0:7]),
                "url": cmpt_url})

        if not cmpt.ok:
            raise ansible_errors.AnsibleError('error while getting or creating component %s: %s' % (cmpt_name, cmpt.text))  # noqa
        cmpt_id = cmpt.json()['component']['id']

        ret = dci_job.add_component(
            ctx,
            job_id=job_id,
            component_id=cmpt_id)
        if ret.status_code == 409:
            module_return['message_action_plugin_git'] = ret.text
        elif ret.status_code != 201:
            raise ansible_errors.AnsibleError('error while attaching component %s to job %s: %s' % (cmpt_id, job_id, cmpt.text))  # noqa

        module_return['component'] = cmpt.json()['component']
        return module_return
