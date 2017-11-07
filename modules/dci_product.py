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
            label=dict(type='str'),
            description=dict(type='str'),
            embed=dict(type='list'),
        ),
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    ctx = build_dci_context(module)

    # Action required: List all products
    # Endpoint called: /products GET via dci_product.list()
    #
    # List all products
    if module_params_empty(module.params):
        res = dci_product.list(ctx)

    # Action required: Delete the product matching product id
    # Endpoint called: /products/<product_id> DELETE via dci_product.delete()
    #
    # If the product exists and it has been succesfully deleted the changed is
    # set to true, else if the product does not exist changed is set to False
    elif module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_product.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['product']['etag']
            }
            res = dci_product.delete(ctx, **kwargs)

    # Action required: Retrieve product informations
    # Endpoint called: /products/<product_id> GET via dci_product.get()
    #
    # Get product informations
    elif module.params['id'] and not module.params['name'] and not module.params['label'] and not module.params['team_id'] and not module.params['description']:

        kwargs = {}
        if module.params['embed']:
            kwargs['embed'] = module.params['embed']

        res = dci_product.get(ctx, module.params['id'], **kwargs)

    # Action required: Update an existing product
    # Endpoint called: /products/<product_id> PUT via dci_product.update()
    #
    # Update the product with the specified characteristics.
    elif module.params['id']:
        res = dci_product.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['product']['etag']
            }
            if module.params['name']:
                kwargs['name'] = module.params['name']
            if module.params['description']:
                kwargs['description'] = module.params['description']
            if module.params['team_id']:
                kwargs['team_id'] = module.params['team_id']
            res = dci_product.update(ctx, **kwargs)

    # Action required: Create a product with the specified content
    # Endpoint called: /products POST via dci_product.create()
    #
    # Create the new product.
    else:
        if not module.params['name']:
            module.fail_json(msg='name parameter must be specified')

        kwargs = {'name': module.params['name']}
        if module.params['label']:
            kwargs['label'] = module.params['label']
        if module.params['description']:
            kwargs['description'] = module.params['description']
        if module.params['team_id']:
            kwargs['team_id'] = module.params['team_id']

        res = dci_product.create(ctx, **kwargs)

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
