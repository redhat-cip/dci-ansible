#!/usr/bin/python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ansible.module_utils.basic import *

import os

try:
    from dciclient.v1.api import context as dci_context
    from dciclient.v1.api import file as dci_file
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_file
short_description: An ansible module to interact with the /files endpoint of DCI
version_added: 2.2
options:
  state:
    required: false
    description: Desired state of the resource
  dci_login:
    required: false
    description: User's DCI login
  dci_password:
    required: false
    description: User's DCI password
  dci_cs_url:
    required: false
    description: DCI Control Server URL
  job_id:
    required: false
    description: ID of the job to attach the file to
  jobstate_id:
    required: false
    description: ID of the jobstate to attach the file to
  mime:
    required: false
    default: text/plain
    description: mime-type of the document to upload
  path:
    required: true
    description: Path of the document to upload
  name:
    required: false
    description: Name under which the file will be saved on the control-server
  content:
    required: false
    description: Contentn of the file to upload
'''

EXAMPLES = '''
- name: Attach files to job
  dci_file:
    job_id: '{{ job_id }}'
    path: '{{ item.path }}'
    name: '{{ item.name }}'
  with_items:
    - {'name': 'SSHd config', 'path': '/etc/ssh/sshd_config'}
    - {'name': 'My OpenStack config', 'path': '/etc/myown.conf'}


- name: Get file information
  dci_file:
    id: XXXXX


- name: Attach content to a file to a job
  dci_file:
    job_id: '{{ job_id }}'
    content: 'This is the content of the file I want to create'
    name: 'My test file'


- name: Remove file
  dci_file:
    state: absent
    id: XXXXX


- name: Attach junit result
  dci_file:
    path: '{{ item }}'
    job_id: '{{ job_id }}'
    mime: 'application/junit'
  with_items:
    - '/tmp/result.xml'
'''

# TODO
RETURN = '''
'''


def _param_from_module_or_env(module, name, default=None):
    values = [module.params[name.lower()], os.getenv(name.upper())]
    return next((item for item in values if item is not None), default)


def _get_details(module):
    """Method that retrieves the appropriate credentials. """

    login = param_from_module_or_env(module, 'dci_login')
    password = param_from_module_or_env(module, 'dci_password')

    client_id = param_from_module_or_env(module, 'dci_client_id')
    api_secret = param_from_module_or_env(module, 'dci_api_secret')

    url = param_from_module_or_env(module, 'dci_cs_url',
                                   'https://api.distributed-ci.io')

    return login, password, url, client_id, api_secret


def _build_dci_context(module):
    login, password, url, client_id, api_secret = _get_details(module)

    if login is not None and password is not None:
        return dci_context.build_dci_context(url, login, password, 'Ansible')
    elif client_id is not None and api_secret is not None:
        return dci_context.build_signature_context(url, client_id, api_secret,
                                                   'Ansible')
    else:
        module.fail_json(msg='Missing or incomplete credentials.')


def module_params_empty(module_params):

    for item in module_params:
        if item not in ['state', 'mime'] and module_params[item] is not None:
            return False

    return True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            # Authentication related parameters
            #
            dci_login=dict(required=False, type='str'),
            dci_password=dict(required=False, type='str', no_log=True),
            dci_cs_url=dict(required=False, type='str'),
            # Resource related parameters
            #
            id=dict(type='str'),
            content=dict(type='str'),
            path=dict(type='str'),
            name=dict(type='str'),
            job_id=dict(type='str'),
            jobstate_id=dict(type='str'),
            mime=dict(default='text/plain', type='str'),
        ),
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    ctx = _build_dci_context(module)

    # Action required: List all files
    # Endpoint called: /files GET via dci_file.list()
    #
    # List all files
    if module_params_empty(module.params):
        res = dci_file.list(ctx)

    # Action required: Delete the file matchin file id
    # Endpoint called: /files/<file_id> DELETE via dci_file.delete()
    #
    # If the file exist and it has been succesfully deleted the changed is
    # set to true, else if the file does not exist changed is set to False
    elif module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_file.delete(ctx, module.params['id'])

    # Action required: Retrieve file informations
    # Endpoint called: /files/<file_id> GET via dci_job.file()
    #
    # Get file informations
    elif module.params['id']:
        res = dci_file.get(ctx, module.params['id'])

    # Action required: Creat a file with the specified content
    # Endpoint called: /files POST via dci_file.create()
    #
    # Create the file and attach it where it belongs (either jobstate or job)
    # with the specified content/content of path provided.
    #
    # NOTE: /files endpoint does not support PUT method, hence no update can
    #       be accomplished.
    else:
        if not module.params['job_id'] and not module.params['jobstate_id']:
            module.fail_json(msg='Either job_id or jobstate_id must be specified')

        if (not module.params['content'] and not module.params['path']) or \
            (module.params['content'] and module.params['path']):
            module.fail_json(msg='Either content or path must be specified')

        if module.params['content'] and not module.params['name']:
            module.fail_json(msg='name parameter must be specified when content has been specified')

        if module.params['path'] and not module.params['name']:
            name = module.params['path']
        else:
            name = module.params['name']

        if module.params['path']:
            try:
                content = open(module.params['path'], 'r').read()
            except IOError as e:
                module.fail_json(msg='The path specified cannot be read')
        else:
            content = module.params['content']

        kwargs = {'name': name, 'content': content, 'mime': module.params['mime']}

        if module.params['job_id']:
            kwargs['job_id'] = module.params['job_id']
        if module.params['jobstate_id']:
            kwargs['jobstate_id'] = module.params['jobstate_id']

        res = dci_file.create(ctx, **kwargs)

    try:
        result = res.json()
        if res.status_code == 404:
            module.fail_json(msg='The resource does not exist')
        if res.status_code == 409:
            result['changed'] = False
        else:
            result['changed'] = True
    except:
        result = {}
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
