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
from ansible.module_utils.common import build_dci_context, module_params_empty

try:
    from dciclient.v1.api import context as dci_context
    from dciclient.v1.api import feeder as dci_feeder
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_feeder
short_description: An ansible module to interact with the /feeders endpoint of DCI
version_added: 2.4
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
  data:
    required: false
    description: Data field of a feeder
  team_id:
    required: false
    description: ID of the team the feeder belongs to
'''

EXAMPLES = '''
- name: Create a new feeder
  dci_feeder:
    name: 'A-Feeder'
    team_id: XXX


- name: Create a new feeder
  dci_feeder:
    name: 'A-Feeder'
    team_id: XXX
    data:
      key: value


- name: Get feeder information
  dci_feeder:
    id: XXXXX


- name: Update feeder informations
  dci_feeder:
    id: XXXX
    name: 'B-Feeder'


- name: Delete a feeder
  dci_feeder:
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
            team_id=dict(type='str'),
            data=dict(type='json'),
            embed=dict(type='list'),
        ),
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    ctx = build_dci_context(module)

    # Action required: List all feeders
    # Endpoint called: /feeders GET via dci_feeder.list()
    #
    # List all feeders
    if module_params_empty(module.params):
        res = dci_feeder.list(ctx)

    # Action required: Delete the feeder matching feeder id
    # Endpoint called: /feeders/<feeder_id> DELETE via dci_feeder.delete()
    #
    # If the feeder exists and it has been succesfully deleted the changed is
    # set to true, else if the feeder does not exist changed is set to False
    elif module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_feeder.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['feeder']['etag']
            }
            res = dci_feeder.delete(ctx, **kwargs)

    # Action required: Retrieve feeder informations
    # Endpoint called: /feeders/<feeder_id> GET via dci_feeder.get()
    #
    # Get feeder informations
    elif module.params['id'] and not module.params['name'] and not module.params['data'] and not module.params['team_id']:

        kwargs = {}
        if module.params['embed']:
            kwargs['embed'] = module.params['embed']

        res = dci_feeder.get(ctx, module.params['id'], **kwargs)

    # Action required: Update an existing feeder
    # Endpoint called: /feeders/<feeder_id> PUT via dci_feeder.update()
    #
    # Update the feeder with the specified characteristics.
    elif module.params['id']:
        res = dci_feeder.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['feeder']['etag']
            }
            if module.params['name']:
                kwargs['name'] = module.params['name']
            if module.params['data']:
                kwargs['data'] = module.params['data']
            if module.params['team_id']:
                kwargs['team_id'] = module.params['team_id']
            res = dci_feeder.update(ctx, **kwargs)

    # Action required: Creat a feeder with the specified content
    # Endpoint called: /feeders POST via dci_feeder.create()
    #
    # Create the new feeder.
    else:
        if not module.params['name']:
            module.fail_json(msg='name parameter must be specified')

        kwargs = {'name': module.params['name']}
        if module.params['data']:
            kwargs['data'] = module.params['data']
        if module.params['team_id']:
            kwargs['team_id'] = module.params['team_id']

        res = dci_feeder.create(ctx, **kwargs)

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
