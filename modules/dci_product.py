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
    from dciclient.v1.api import product as dci_product
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_product
short_description: An ansible module to interact with the /products endpoint of DCI
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
  team_id:
    required: false
    description: ID of the team the product belongs to
  where:
    required: false
    description: Specific criterias for search
'''

EXAMPLES = '''
- name: Create a new product
  dci_product:
    name: 'product-A'
    team_id: XXX


- name: Create a new product
  dci_product:
    name: 'product-A'
    team_id: XXX
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
        self.team_id = params.get('team_id')
        self.label = params.get('label')
        self.description = params.get('description')
        self.search_criterias = {
            'embed': params.get('embed'),
            'where': params.get('where')
        }
        self.deterministic_params = ['name', 'team_id', 'label', 'description']

    def do_create(self, context):
        if not self.name:
            raise DciParameterError('name parameter must be speficied')

        return super(DciProduct, self).do_create(context)


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
            team_id=dict(type='str'),
            label=dict(type='str'),
            description=dict(type='str'),
            embed=dict(type='str'),
            where=dict(type='str'),
        ),
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    context = build_dci_context(module)
    action_name = get_standard_action(module.params)

    product = DciProduct(module.params)
    action_func = getattr(product, 'do_%s' % action_name)

    http_response = run_action_func(action_func, context, module)
    result = parse_http_response(http_response, dci_product, context, module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
