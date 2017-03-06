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
    from dciclient.v1.api import team as dci_team
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_team
short_description: An ansible module to interact with the /teams endpoint of DCI
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
    description: Teams name
  country:
    required: false
    description: Team country
  email:
    required: false
    description: Email to notify on jobs failure
  notification:
    required: false
    description: Should the team be notified on jobs failure
'''

EXAMPLES = '''
- name: Create a new team
  dci_team:
    name: 'A-Team'
    country: 'USA'


- name: Create a new team
  dci_team:
    name: 'A-Team'
    country: 'USA'
    email: 'mrt@a-team.com'
    notification: True


- name: Get team information
  dci_team:
    id: XXXXX


- name: Update team informations
  dci_team:
    id: XXXX
    name: 'B-Team'


- name: Delete a team
  dci_team:
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


def module_params_empty(module_params):

    for item in module_params:
        if item != 'state' and module_params[item] is not None:
            return False

    return True


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
            country=dict(type='str'),
            email=dict(type='str'),
            notification=dict(type='bool'),
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

    # Action required: List all teams
    # Endpoint called: /teams GET via dci_team.list()
    #
    # List all teams
    if module_params_empty(module.params):
        res = dci_team.list(ctx)

    # Action required: Delete the team matching team id
    # Endpoint called: /teams/<team_id> DELETE via dci_team.delete()
    #
    # If the team exists and it has been succesfully deleted the changed is
    # set to true, else if the team does not exist changed is set to False
    elif module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_team.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['team']['etag']
            }
            res = dci_team.delete(ctx, **kwargs)

    # Action required: Retrieve team informations
    # Endpoint called: /teams/<team_id> GET via dci_team.get()
    #
    # Get team informations
    elif module.params['id'] and not module.params['name'] and not module.params['country'] and not module.params['email'] and module.params['notification'] is None:
        res = dci_team.get(ctx, module.params['id'])

    # Action required: Update an existing team
    # Endpoint called: /teams/<team_id> PUT via dci_team.update()
    #
    # Update the team with the specified characteristics.
    elif module.params['id']:
        res = dci_team.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['team']['etag']
            }
            if module.params['name']:
                kwargs['name'] = module.params['name']
            if module.params['country']:
                kwargs['country'] = module.params['country']
            if module.params['email']:
                kwargs['email'] = module.params['email']
            if module.params['notification'] is not None:
                kwargs['notification'] = module.params['notification']
            res = dci_team.update(ctx, **kwargs)

    # Action required: Creat a team with the specified content
    # Endpoint called: /teams POST via dci_team.create()
    #
    # Create the new team.
    else:
        if not module.params['name']:
            module.fail_json(msg='name parameter must be specified')

        kwargs = {'name': module.params['name']}
        if module.params['country']:
            kwargs['country'] = module.params['country']
        if module.params['email']:
            kwargs['email'] = module.params['email']
        if module.params['notification'] is not None:
            kwargs['notification'] = module.params['notification']

        res = dci_team.create(ctx, **kwargs)

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
