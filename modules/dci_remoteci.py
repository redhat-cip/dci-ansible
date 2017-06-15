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
            dci_password=dict(required=False, type='str', no_log=True),
            dci_cs_url=dict(required=False, type='str'),
            # Resource related parameters
            #
            id=dict(type='str'),
            name=dict(type='str'),
            data=dict(type='dict'),
            team_id=dict(type='str'),
        ),
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    ctx = _build_dci_context(module)

    # Action required: List all remotecis
    # Endpoint called: /remotecis GET via dci_remoteci.list()
    #
    # List all remotecis
    if module_params_empty(module.params):
        res = dci_remoteci.list(ctx)

    # Action required: Delete the remoteci matching remoteci id
    # Endpoint called: /remotecis/<remoteci_id> DELETE via dci_remoteci.delete()
    #
    # If the remoteci exists and it has been succesfully deleted the changed is
    # set to true, else if the remoteci does not exist changed is set to False
    elif module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_remoteci.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['remoteci']['etag']
            }
            res = dci_remoteci.delete(ctx, **kwargs)

    # Action required: Retrieve remoteci informations
    # Endpoint called: /remotecis/<remoteci_id> GET via dci_remoteci.get()
    #
    # Get remoteci informations
    elif module.params['id'] and not module.params['name'] and not module.params['data'] and not module.params['team_id']:
        res = dci_remoteci.get(ctx, module.params['id'])

    # Action required: Update an existing remoteci
    # Endpoint called: /remotecis/<remoteci_id> PUT via dci_remoteci.update()
    #
    # Update the remoteci with the specified characteristics.
    elif module.params['id']:
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

    # Action required: Create a remoteci with the specified content
    # Endpoint called: /remotecis POST via dci_remoteci.create()
    #
    # Create the new remoteci.
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
