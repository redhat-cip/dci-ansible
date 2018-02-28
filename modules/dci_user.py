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
from ansible.module_utils.common import *
from ansible.module_utils.dci_base import *

try:
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
  where:
    required: false
    description: Specific criterias for search
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


class DciUser(DciBase):

    def __init__(self, params):
        super(DciUser, self).__init__(dci_user)
        self.id = params.get('id')
        self.name = params.get('name')
        self.fullname = params.get('fullname')
        self.email = params.get('email')
        self.password = params.get('password')
        self.role_id = params.get('role_id')
        self.team_id = params.get('team_id')
        self.search_criterias = {
            'embed': params.get('embed'),
            'where': params.get('where')
        }
        self.deterministic_params = ['name', 'fullname', 'email', 'password',
                                     'role_id', 'team_id']

    def do_create(self, context):
        for param in ['name', 'password', 'team_id', 'email']:
            if not getattr(self, param):
                raise DciParameterError(
                    '%s parameter must be speficied' % param
                )

        return super(DciUser, self).do_create(context)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            # Authentication related parameters
            #
            dci_login=dict(required=False, type='str',
                           fallback=(env_fallback, ['DCI_LOGIN'])),
            dci_password=dict(required=False, type='str', no_log=True,
                              fallback=(env_fallback, ['DCI_PASSWORD'])),
            dci_cs_url=dict(required=False, type='str',
                            fallback=(env_fallback, ['DCI_CS_URL']),
                            default='https://api.distributed-ci.io'),
            dci_client_id=dict(required=False, type='str',
                               fallback=(env_fallback, ['DCI_CLIENT_ID'])),
            dci_api_secret=dict(required=False, type='str', no_log=True,
                                fallback=(env_fallback, ['DCI_API_SECRET'])),
            # Resource related parameters
            #
            id=dict(type='str'),
            name=dict(type='str'),
            fullname=dict(type='str'),
            email=dict(type='str'),
            password=dict(type='str', no_log=True),
            role_id=dict(type='str'),
            team_id=dict(type='str'),
            embed=dict(type='str'),
            where=dict(type='str'),
        ),
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    context = build_dci_context(module)
    action_name = get_standard_action(module.params)

    user = DciUser(module.params)
    action_func = getattr(user, 'do_%s' % action_name)

    http_response = run_action_func(action_func, context, module)
    result = parse_http_response(http_response, dci_user, context, module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
