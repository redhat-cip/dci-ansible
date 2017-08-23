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
    from dciclient.v1.api import user as dci_user
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_user
short_description: An ansible module to interact with the /users endpoint of DCI
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
    description: ID of the user to interact with
  name:
    required: false
    description: User name
  password:
    required: false
    description: User password
  fullname:
    required: false
    description: User fullname
  email:
    required: false
    description: User email
  role_id:
    required: false
    description: ID of the role the user is attached to
  team_id:
    required: false
    description: ID of the team the user belongs to
  embed:
    required: false
    description:
      - List of field to embed within the retrieved resource
'''

EXAMPLES = '''
- name: Create a new user
  dci_user:
    name: jdoe
    fullname: John Doe
    email: jdoe@example.tld
    password: 'APassw0rd!'
    role_id: XXXXX
    team_id: XXXXX


- name: Get user information
  dci_user:
    id: XXXXX


- name: Update user informations
  dci_user:
    id: XXXX
    role_id: XXXX
    email: jdoe@newcompany.org


- name: Delete a user
  dci_user:
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
            fullname=dict(type='str'),
            email=dict(type='str'),
            password=dict(type='str',no_log=True),
            role_id=dict(type='str'),
            team_id=dict(type='str'),
            embed=dict(type='list'),
        ),
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    ctx = build_dci_context(module)

    # Action required: List all users
    # Endpoint called: /users GET via dci_user.list()
    #
    # List all users
    if module_params_empty(module.params):
        res = dci_user.list(ctx)

    # Action required: Delete the user matching user id
    # Endpoint called: /users/<user_id> DELETE via dci_user.delete()
    #
    # If the user exists and it has been succesfully deleted the changed is
    # set to true, else if the user does not exist changed is set to False
    elif module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_user.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['user']['etag']
            }
            res = dci_user.delete(ctx, **kwargs)

    # Action required: Retrieve user informations
    # Endpoint called: /user/<user_id> GET via dci_user.get()
    #
    # Get user informations
    elif module.params['id'] and not module.params['name'] and \
            not module.params['team_id'] and not module.params['role_id'] and \
            not module.params['password'] and not module.params['email'] and \
            not module.params['fullname']:
        kwargs = {}
        if module.params['embed']:
            kwargs['embed'] = module.params['embed']
        res = dci_user.get(ctx, module.params['id'], **kwargs)

    # Action required: Update an user
    # Endpoint called: /users/<user_id> PUT via dci_user.update()
    #
    # Update the user with the specified characteristics.
    elif module.params['id']:
        res = dci_user.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['user']['etag']
            }
            if module.params['name']:
                kwargs['name'] = module.params['name']
            if module.params['password']:
                kwargs['password'] = module.params['password']
            if module.params['role_id']:
                kwargs['role_id'] = module.params['role_id']
            if module.params['team_id']:
                kwargs['team_id'] = module.params['team_id']
            if module.params['fullname']:
                kwargs['fullname'] = module.params['fullname']
            if module.params['email']:
                kwargs['email'] = module.params['email']
            res = dci_user.update(ctx, **kwargs)

    # Action required: Create a user with the specified content
    # Endpoint called: /users POST via dci_user.create()
    #
    # Create the new user.
    else:
        if not module.params['name']:
            module.fail_json(msg='name parameter must be specified')
        if not module.params['password']:
            module.fail_json(msg='password parameter must be specified')
        if not module.params['team_id']:
            module.fail_json(msg='team_id parameter must be specified')
        if not module.params['email']:
            module.fail_json(msg='email parameter must be specified')

        kwargs = {
            'name': module.params['name'],
            'fullname': module.params['fullname'] or module.params['name'],
            'email': module.params['email'],
            'password': module.params['password'],
            'role_id': module.params['role_id'],
            'team_id': module.params['team_id'],
        }

        res = dci_user.create(ctx, **kwargs)

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
