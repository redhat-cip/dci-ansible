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
from ansible.module_utils.common import build_dci_context, get_action

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
  embed:
    required: false
    description:
      - List of field to embed within the retrieved resource
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


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            # Authentication related parameters
            #
            dci_login=dict(required=False, type='str'),
            dci_password=dict(required=False, type='str', no_log=True),
            dci_cs_url=dict(required=False, type='str'),
            dci_client_id=dict(required=False, type='str'),
            dci_api_secret=dict(required=False, type='str', no_log=True),
            # Resource related parameters
            #
            id=dict(type='str'),
            name=dict(type='str'),
            country=dict(type='str'),
            email=dict(type='str'),
            notification=dict(type='bool'),
            embed=dict(type='list'),
        ),
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    ctx = build_dci_context(module)
    action = get_action(module.params)

    if action == 'list':
        res = dci_team.list(ctx)

    elif action == 'delete':
        res = dci_team.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['team']['etag']
            }
            res = dci_team.delete(ctx, **kwargs)

    elif action == 'get':
        kwargs = {}
        if module.params['embed']:
            kwargs['embed'] = module.params['embed']

        res = dci_team.get(ctx, module.params['id'], **kwargs)

    elif action == 'update':
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
