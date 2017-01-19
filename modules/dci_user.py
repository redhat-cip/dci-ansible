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
  login:
    required: false
    description: User's DCI login
  password:
    required: false
    description: User's DCI password
  url:
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
  role:
    required: false
    choices: ['user', 'admin']
    description: User role
  team_id:
    required: false
    description: ID of the team the user belongs to
'''

EXAMPLES = '''
- name: Create a new user
  dci_user:
    name: 'jdoe@customer.com'
    password: 'APassw0rd!'
    role: 'user'
    team_id: XXXXX


- name: Get user information
  dci_user:
    id: XXXXX


- name: Update user informations
  dci_user:
    id: XXXX
    role: 'admin'


- name: Delete a user
  dci_user:
    state: absent
    id: XXXXX
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
            # Authentication related parameters
            #
            login=dict(required=False, type='str'),
            password=dict(required=False, type='str'),
            url=dict(required=False, type='str'),
            # Resource related parameters
            #
            id=dict(type='str'),
            name=dict(type='str'),
            passwd=dict(type='str'),
            role=dict(choices=['user', 'admin'], type='str'),
            team_id=dict(type='str'),
        ),
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    login, password, url = get_details(module)
    if not login or not password:
        module.fail_json(msg='login and/or password have not been specified')

    ctx = dci_context.build_dci_context(url, login, password, 'Ansible')

    # Action required: Delete the user matching user id
    # Endpoint called: /users/<user_id> DELETE via dci_user.delete()
    #
    # If the user exists and it has been succesfully deleted the changed is
    # set to true, else if the user does not exist changed is set to False
    if module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_user.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 422]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['user']['etag']
            }
            res = dci_user.delete(ctx, **kwargs)

    # Action required: Retrieve user informations
    # Endpoint called: /user/<user_id> GET via dci_user.get()
    #
    # Get user informations
    elif module.params['id'] and not module.params['name'] and not module.params['passwd'] and not module.params['role'] and not module.params['team_id']:
        res = dci_user.get(ctx, module.params['id'])

    # Action required: Update an user
    # Endpoint called: /users/<user_id> PUT via dci_user.update()
    #
    # Update the user with the specified characteristics.
    elif module.params['id']:
        res = dci_user.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 422]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['user']['etag']
            }
            if module.params['name']:
                kwargs['name'] = module.params['name']
            if module.params['password']:
                kwargs['password'] = module.params['passwd']
            if module.params['role']:
                kwargs['role'] = module.params['role']
            if module.params['team_id']:
                kwargs['team_id'] = module.params['team_id']
            res = dci_user.update(ctx, **kwargs)

    # Action required: Create a user with the specified content
    # Endpoint called: /users POST via dci_user.create()
    #
    # Create the new user.
    else:
        if not module.params['name']:
            module.fail_json(msg='name parameter must be specified')
        if not module.params['passwd']:
            module.fail_json(msg='passwd parameter must be specified')
        if not module.params['team_id']:
            module.fail_json(msg='team_id parameter must be specified')
        if not module.params['role']:
            role = 'user'

        kwargs = {
            'name': module.params['name'],
            'password': module.params['passwd'],
            'role': role,
            'team_id': module.params['team_id'],
        }

        res = dci_user.create(ctx, **kwargs)

    try:
        result = res.json()
        if res.status_code == 404:
            module.fail_json(msg='The resource does not exist')
        if res.status_code == 422:
            result['changed'] = False
        else:
            result['changed'] = True
    except:
        result = {}
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
