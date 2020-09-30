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
from ansible.module_utils.dci_common import *
from ansible.module_utils.dci_base import *

try:
    from dciclient.v1.api import test as dci_test
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_test
short_description: module to interact with the tests endpoint of DCI
description:
  - DCI module to manage the test resources
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
    description: Test name
  data:
    required: false
    description: Test data
  team_id:
    required: false
    description: Team to which the test will be attached
  active:
    required: false
    description: Wether of not the resource should be active
  embed:
    required: false
    description:
      - List of field to embed within the retrieved resource
  where:
    required: false
    description: Specific criterias for search
'''

EXAMPLES = '''
- name: Create a new test
  dci_test:
    name: 'tempest'
    data: {"url": "http://www.redhat.com"}
    team_id: XXXX


- name: Get test information
  dci_test:
    id: XXXXX


- name: Delete a test
  dci_test:
    state: absent
    id: XXXXX
'''

# TODO
RETURN = '''
'''


class DciTest(DciBase):

    def __init__(self, params):
        super(DciTest, self).__init__(dci_test)
        self.id = params.get('id')
        self.name = params.get('name')
        self.team_id = params.get('team_id')
        self.data = params.get('data')
        self.active = params.get('active')
        self.search_criterias = {
            'embed': params.get('embed'),
            'where': params.get('where')
        }
        self.deterministic_params = ['name', 'team_id', 'data', 'active']

    def do_delete(self, context):
        return self.resource.delete(context, self.id)

    def do_create(self, context):
        for param in ['name', 'team_id']:
            if not getattr(self, param):
                raise DciParameterError(
                    '%s parameter must be speficied' % param
                )

        return super(DciTest, self).do_create(context)


def main():

    resource_argument_spec = dict(
        state=dict(
            default='present',
            choices=['present', 'absent'],
            type='str'),
        id=dict(type='str'),
        name=dict(type='str'),
        data=dict(type='dict'),
        team_id=dict(type='str'),
        active=dict(default=True, type='bool'),
        embed=dict(type='str'),
        where=dict(type='str'),
    )
    resource_argument_spec.update(authentication_argument_spec())

    module = AnsibleModule(
        argument_spec=resource_argument_spec,
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    context = build_dci_context(module)
    action_name = get_standard_action(module.params)

    test = DciTest(module.params)
    action_func = getattr(test, 'do_%s' % action_name)

    http_response = run_action_func(action_func, context, module)
    result = parse_http_response(http_response, dci_test, context, module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
