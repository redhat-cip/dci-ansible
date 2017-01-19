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
from dciclient.v1.api import job as dci_job
from dciclient.v1 import tripleo_helper as dci_tripleo_helper

try:
    import requests
except ImportError:
    requests_found = False
else:
    requests_found = True


DOCUMENTATION = '''
---
module: dci_run_tests
short_description: An ansible module to run tests attached to a job
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
  undercloud_ip:
    required: true
    description: IP of the undercloud to run the tests on
  undercloud_user:
    required: false
    default: stack
    description: User to connect to the undercloud with
  remoteci:
    required: true
    description: Name or ID of the remoteci
  key_filename:
    required: true
    description: Path to the ssh private key
  job_id:
    required: true
    description: ID of the job
  stack_name:
    required: false
    default: overcloud
    description: stack name
'''

EXAMPLES = '''
- name: Run tests associated to job
  dci_run_tests:
    unercloud_ip: '{{ ansible_ipv4 }}'
    remoteci: 'dev-ovb-1'
    key_filename: '{{ ansible_ssh_priv_key }}'
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
            undercloud_ip=dict(type='str'),
            undercloud_user=dict(required=False, default='stack', type='str'),
            remoteci=dict(type='str'),
            job_id=dict(type='str'),
            key_filename=dict(default='text/plain', type='str'),
            stack_name=dict(required=False, default='overcloud', type='str'),
            url=dict(required=False, type='str'),
        ),
    )

    if not requests_found:
        module.fail_json(msg='The python requests module is required')

    login, password, url = get_details(module)
    if not login or not password:
        module.fail_json(msg='login and/or password have not been specified')

    ctx = dci_context.build_dci_context(url, login, password, 'ansible')

    last_js = dci_job.list_jobstates(ctx, module.params['job_id']).json()['jobstates'][0]

    ctx.last_job_id = last_js['job_id']
    ctx.last_jobstate_id = last_js['id']

    dci_tripleo_helper.run_tests(
                ctx,
                undercloud_ip=module.params['undercloud_ip'],
                key_filename=module.params['key_filename'],
                remoteci_id=module.params['remoteci'],
                stack_name=module.params['stack_name'],
                user=module.params['undercloud_user'])

    module.exit_json(changed=True)


if __name__ == '__main__':
    main()
