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
  embed:
    required: false
    description:
      - List of field to embed within the retrieved resource
  where:
    required: false
    description: Specific criterias for search
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


class DciFeeder(DciBase):

    def __init__(self, params):
        super(DciFeeder, self).__init__(dci_feeder)
        self.id = params.get('id')
        self.name = params.get('name')
        self.team_id = params.get('team_id')
        self.data = params.get('data')
        self.search_criterias = {
            'embed': params.get('embed'),
            'where': params.get('where')
        }
        self.deterministic_params = ['name', 'data', 'team_id']

    def do_create(self, context):
        if not self.name:
            raise DciParameterError('name parameter must be speficied')

        return super(DciFeeder, self).do_create(context)


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
            where=dict(type='str'),
        ),
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    context = build_dci_context(module)
    action_name = get_standard_action(module.params)

    feeder = DciFeeder(module.params)
    action_func = getattr(feeder, 'do_%s' % action_name)

    http_response = run_action_func(action_func, context, module)
    result = parse_http_response(http_response, dci_feeder, context, module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
