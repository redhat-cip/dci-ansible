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
import yaml

try:
    from dciclient.v1.api import context as dci_context
    from dciclient.v1.api import test as dci_test
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_test
short_description: An ansible module to interact with the /tests endpoint of DCI
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
  id:
    required: false
    description: ID of the team to interact with
  name:
    required: false
    description: Test name
  data:
    required: false
    description: Test data
  team_id:
    required: false
    description: Team to which the test will be attached
'''

EXAMPLES = '''
- name: Create a new test
  dci_test:
    name: 'tempest'
    data: {"url": "http://www.redhat.com"}
    team_id: XXXX


- name: Get test information
  dci_test:
    id: XXXXX


- name: Delete a test
  dci_test:
    state: absent
    id: XXXXX
'''

# TODO
RETURN = '''
'''


def get_config(module):
    from_file = {}
    if os.path.exists('/etc/dci/dci.yaml'):
        with open('/etc/dci/dci.yaml') as fd:
            from_file = yaml.load(fd)

    return {
        'login':
            module.params.get('dci_login')
            or from_file.get('login'),
        'password':
            module.params.get('dci_password')
            or from_file.get('password'),
        'cs_url':
            module.params.get('dci_cs_url')
            or from_file.get('cs_url')
            or 'https://api.distributed-ci.io',
        'remoteci':
            module.params.get('remoteci')
            or from_file.get('remoteci'),
        'topic':
            module.params.get('topic')
            or from_file.get('topic')
        }


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            # Authentication related parameters
            #
            dci_login=dict(required=False, type='str'),
            dci_password=dict(required=False, type='str'),
            dci_cs_url=dict(required=False, type='str'),
            # Resource related parameters
            #
            id=dict(type='str'),
            name=dict(type='str'),
            data=dict(type='dict'),
            team_id=dict(type='str'),
        ),
    )
    config = get_config(module)

    if not dciclient_found:
        module.fail_json(msg='the python dciclient module is required')

    if not set(['login', 'password']).issubset(config):
        module.fail_json(msg='login and/or password have not been specified')

    ctx = dci_context.build_dci_context(
        config['cs_url'], config['login'],
        config['password'], 'ansible')

    # Action required: Delete the test matching test id
    # Endpoint called: /tests/<test_id> DELETE via dci_test.delete()
    #
    # If the test exists and it has been succesfully deleted the changed is
    # set to true, else if the test does not exist changed is set to False
    if module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_test.delete(ctx, module.params['id'])

    # Action required: Retrieve test informations
    # Endpoint called: /tests/<test_id> GET via dci_test.get()
    #
    # Get test informations
    elif module.params['id']:
        res = dci_test.get(ctx, module.params['id'])

    # Action required: Create a test with the specified content
    # Endpoint called: /tests POST via dci_test.create()
    #
    # Create the new test.
    else:
        if not module.params['name']:
            module.fail_json(msg='name parameter must be specified')
        if not module.params['team_id']:
            module.fail_json(msg='team_id parameter must be specified')

        kwargs = {
            'name': module.params['name'],
            'team_id': module.params['team_id'],
        }
        if module.params['data']:
            kwargs['data'] = module.params['data']

        res = dci_test.create(ctx, **kwargs)

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
