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
    from dciclient.v1.api import role as dci_role
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_role
short_description: An ansible module to interact with the /roles endpoint of DCI
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
  label:
    required: false
    description: Label of the role
  description:
    required: false
    description: Description of the role
  where:
    required: false
    description: Specific criterai for search
'''

EXAMPLES = '''
- name: Create a new role
  dci_role:
    name: 'A-Role'


- name: Create a new role
  dci_role:
    name: 'A-Role'
    label: 'AROLE'
    description: 'God on earth'


- name: Get role information
  dci_role:
    id: XXXXX


- name: Update role informations
  dci_role:
    id: XXXX
    name: 'B-Role'


- name: Delete a role
  dci_role:
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
            label=dict(type='str'),
            description=dict(type='str'),
            embed=dict(type='list'),
            where=dict(type='str'),
        ),
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    ctx = build_dci_context(module)

    # Action required: List all roles
    # Endpoint called: /roles GET via dci_role.list()
    #
    # List all roles
    if module_params_empty(module.params) or module.params['where']:
        res = dci_role.list(ctx, where=module.params['where'])

    # Action required: Delete the role matching role id
    # Endpoint called: /roles/<role_id> DELETE via dci_role.delete()
    #
    # If the role exists and it has been succesfully deleted the changed is
    # set to true, else if the role does not exist changed is set to False
    elif module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_role.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['role']['etag']
            }
            res = dci_role.delete(ctx, **kwargs)

    # Action required: Retrieve role informations
    # Endpoint called: /roles/<role_id> GET via dci_role.get()
    #
    # Get role informations
    elif module.params['id'] and not module.params['name'] and not module.params['label'] and not module.params['description']:

        kwargs = {}
        if module.params['embed']:
            kwargs['embed'] = module.params['embed']

        res = dci_role.get(ctx, module.params['id'], **kwargs)

    # Action required: Update an existing role
    # Endpoint called: /roles/<role_id> PUT via dci_role.update()
    #
    # Update the role with the specified characteristics.
    elif module.params['id']:
        res = dci_role.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['role']['etag']
            }
            if module.params['name']:
                kwargs['name'] = module.params['name']
            if module.params['label']:
                kwargs['label'] = module.params['label']
            if module.params['description']:
                kwargs['description'] = module.params['description']
            res = dci_role.update(ctx, **kwargs)

    # Action required: Creat a role with the specified content
    # Endpoint called: /roles POST via dci_role.create()
    #
    # Create the new role.
    else:
        if not module.params['name']:
            module.fail_json(msg='name parameter must be specified')

        kwargs = {'name': module.params['name']}
        if module.params['label']:
            kwargs['label'] = module.params['label']
        if module.params['description']:
            kwargs['description'] = module.params['description']

        res = dci_role.create(ctx, **kwargs)

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
