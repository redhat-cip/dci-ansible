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
    from dciclient.v1.api import product as dci_product
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_product
short_description: module to interact with the products endpoint of DCI
description:
  - DCI module to manage the remoteci product resources
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
    description: Label of a product
  description:
    required: false
    description: Description of a product
  team_ids:
    required: false
    description: List of Teams to detach from this topic
  active:
    required: false
    description: Wether of not the resource should be active
  where:
    required: false
    description: Specific criterias for search
  query:
    required: false
    description: query language
'''

EXAMPLES = '''
- name: Create a new product
  dci_product:
    name: 'product-A'


- name: Create a new product
  dci_product:
    name: 'product-A'
    label: PRODUCTA-PKI
    description: This is the description of product A


- name: Get product information
  dci_product:
    id: XXXXX


- name: Update product informations
  dci_product:
    id: XXXX
    name: 'newproduct-A'


- name: Delete a product
  dci_product:
    state: absent
    id: XXXXX
'''

# TODO
RETURN = '''
'''


class DciProduct(DciBase):

    def __init__(self, params):
        super(DciProduct, self).__init__(dci_product)
        self.id = params.get('id')
        self.name = params.get('name')
        self.label = params.get('label')
        self.description = params.get('description')
        self.team_ids = params.get('team_ids')
        self.active = params.get('active')
        self.search_criterias = {
            'embed': params.get('embed'),
            'where': params.get('where'),
            'query': params.get('query')
        }
        self.deterministic_params = ['name', 'label', 'description', 'active']

    def do_create(self, context):
        if not self.name:
            raise DciParameterError('name parameter must be speficied')

        return super(DciProduct, self).do_create(context)

    def do_attach_teams(self, context):
        for team in self.team_ids:
            res = dci_product.attach_team(context, self.id, team)
        return res


def main():

    resource_argument_spec = dict(
        state=dict(
            default='present',
            choices=['present', 'absent'],
            type='str'),
        id=dict(type='str'),
        name=dict(type='str'),
        label=dict(type='str'),
        description=dict(type='str'),
        team_ids=dict(type='list'),
        active=dict(default=True, type='bool'),
        embed=dict(type='str'),
        where=dict(type='str'),
        query=dict(type='str')
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
    if action_name == 'update':
        if module.params['team_ids']:
            action_name = 'attach_teams'

    product = DciProduct(module.params)
    action_func = getattr(product, 'do_%s' % action_name)

    http_response = run_action_func(action_func, context, module)
    result = parse_http_response(http_response, dci_product, context, module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
