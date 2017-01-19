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

from dciclient.v1.api import context as dci_context
from dciclient.v1.api import file as dci_file

try:
    import requests
except ImportError:
    requests_found = False
else:
    requests_found = True


DOCUMENTATION = '''
---
module: dci_upload
short_description: An ansible module to attach a file to a DCI job
version_added: 2.2
options:
  login:
    required: false
    description: User's DCI login
  password:
    required: false
    description: User's DCI password
  url:
    required: false
    description: DCI Control Server URL
  job_id:
    required: true
    description: ID of the job to attach the file to
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
'''

EXAMPLES = '''
- name: Attach files to job
  dci_upload:
    path: '{{ item.path }}'
    name: '{{ item.name }}'
    job_id: '{{ job_id }}'
  with_items:
    - {'name': 'SSHd config', 'path': '/etc/ssh/sshd_config'}
    - {'name': 'My OpenStack config', 'path': '/etc/myown.conf'}

- name: Attach junit result
  dci_upload:
    path: '{{ item }}'
    job_id: '{{ job_id }}'
    mime: 'application/junit'
  with_items:
    - '/tmp/result.xml'
'''

# TODO
RETURN = '''
'''


def get_details(module):
    """Method that retrieves the appropriate credentials. """

    login_list = [module.params['login'], os.getenv('DCI_LOGIN')]
    login = next((item for item in login_list if item is not None), None)

    password_list = [module.params['password'], os.getenv('DCI_PASSWORD')]
    password = next((item for item in password_list if item is not None), None)

    url_list = [module.params['url'], os.getenv('DCI_CS_URL')]
    url = next((item for item in url_list if item is not None), 'https://api.distributed-ci.io')

    return login, password, url


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            login=dict(required=False, type='str'),
            password=dict(required=False, type='str'),
            path=dict(type='str'),
            name=dict(required=False, type='str'),
            mime=dict(default='text/plain', type='str'),
            job_id=dict(type='str'),
            url=dict(required=False, type='str'),
        ),
    )

    if not requests_found:
        module.fail_json(msg='The python requests module is required')

    login, password, url = get_details(module)
    if not login or not password:
        module.fail_json(msg='login and/or password have not been specified')

    ctx = dci_context.build_dci_context(url, login, password, 'ansible')

    name = module.params['path']
    if module.params['name']:
        name = module.params['name']

    dci_file.create(ctx, name=name,
                    content=open(module.params['path'], 'r').read(),
                    mime=module.params['mime'], job_id=module.params['job_id'])

    module.exit_json(changed=True)


if __name__ == '__main__':
    main()
