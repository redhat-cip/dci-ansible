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
  dci_login:
    required: false
    description: User's DCI login
  dci_password:
    required: false
    description: User's DCI password
  dci_cs_url:
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


def _param_from_module_or_env(module, name, default=None):
    values = [module.params[name.lower()], os.getenv(name.upper())]
    return next((item for item in values if item is not None), default)


def _get_details(module):
    """Method that retrieves the appropriate credentials. """

    login = _param_from_module_or_env(module, 'dci_login')
    password = _param_from_module_or_env(module, 'dci_password')

    client_id = _param_from_module_or_env(module, 'dci_client_id')
    api_secret = _param_from_module_or_env(module, 'dci_api_secret')

    url = _param_from_module_or_env(module, 'dci_cs_url',
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


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            dci_login=dict(required=False, type='str'),
            dci_password=dict(required=False, type='str', no_log=True),
            dci_cs_url=dict(required=False, type='str'),
            dci_client_id=dict(required=False, type='str'),
            dci_api_secret=dict(required=False, type='str', no_log=True),
            undercloud_ip=dict(type='str'),
            undercloud_user=dict(required=False, default='stack', type='str'),
            remoteci=dict(type='str'),
            job_id=dict(type='str'),
            key_filename=dict(default='text/plain', type='str'),
            stack_name=dict(required=False, default='overcloud', type='str'),
        ),
    )

    if not requests_found:
        module.fail_json(msg='The python requests module is required')

    ctx = _build_dci_context(module)

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
