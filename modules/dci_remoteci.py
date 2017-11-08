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
    from dciclient.v1.api import remoteci as dci_remoteci
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_remoteci
short_description: An ansible module to interact with the /remotecis endpoint of DCI
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
    description: ID of the remoteci to interact with
  name:
    required: false
    description: RemoteCI name
  data:
    required: false
    description: Data associated with the RemoteCI
  team_id:
    required: false
    description: ID of the team the remoteci belongs to
  embed:
    required: false
    description:
      - List of field to embed within the retrieved resource
'''

EXAMPLES = '''
- name: Create a new remoteci
  dci_remoteci:
    name: 'MyRemoteCI'
    team_id: XXXX


- name: Create a new team
  dci_remoteci:
    name: 'MyRemoteCI'
    team_id: XXXX
    data: >
      {"certification_id": "xfewafeqafewqfeqw"}


- name: Get remoteci information
  dci_remoteci:
    id: XXXXX


- name: Update remoteci informations
  dci_remoteci:
    id: XXXX
    name: New Name


- name: Delete a topic
  dci_remoteci:
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
            data=dict(type='dict'),
            team_id=dict(type='str'),
            embed=dict(type='list'),
        ),
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    ctx = build_dci_context(module)
    action = get_action(module.params)

    if action == 'list':
        res = dci_remoteci.list(ctx)

    elif action == 'delete':
        res = dci_remoteci.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['remoteci']['etag']
            }
            res = dci_remoteci.delete(ctx, **kwargs)

    elif action == 'get':
        kwargs = {}
        if module.params['embed']:
            kwargs['embed'] = module.params['embed']
        res = dci_remoteci.get(ctx, module.params['id'], **kwargs)

    elif action == 'update':
        res = dci_remoteci.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['remoteci']['etag']
            }
            if module.params['name']:
                kwargs['name'] = module.params['name']
            if module.params['data']:
                kwargs['data'] = module.params['data']
            if module.params['team_id']:
                kwargs['team_id'] = module.params['team_id']
            res = dci_remoteci.update(ctx, **kwargs)

    else:
        if not module.params['name']:
            module.fail_json(msg='name parameter must be specified')
        if not module.params['team_id']:
            module.fail_json(msg='team_id parameter must be specified')

        kwargs = {
            'name': module.params['name'],
            'team_id': module.params['team_id']
        }
        if module.params['data']:
            kwargs['data'] = module.params['data']

        res = dci_remoteci.create(ctx, **kwargs)

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
