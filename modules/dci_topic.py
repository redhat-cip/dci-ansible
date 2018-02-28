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
    from dciclient.v1.api import topic as dci_topic
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_topic
short_description: An ansible module to interact with the /topics endpoint of DCI
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
    description: ID of the topic to interact with
  name:
    required: false
    description: Topic name
  label:
    required: false
    description: Topic label
  component_types:
    required: false
    description: Topic component_types
  product_id:
    required: false
    description: The product the topic belongs to
  team_ids:
    required: false
    description: List of Teams attach to this topic
  embed:
    required: false
    description:
      - List of field to embed within the retrieved resource
  where:
    required: false
    description: Specific criterias for search
'''

EXAMPLES = '''
- name: Create a new topic
  dci_topic:
    name: 'Soft21'


- name: Create a new topic
  dci_topic:
    name: 'Soft42'
    label: 'The latest version of Soft with the 42 feature'
    product_id: XXX


- name: Get topic information
  dci_topic:
    id: XXXXX


- name: Update topic informations
  dci_topic:
    id: XXXX
    name: 'Soft42-Final'


- name: Delete a topic
  dci_topic:
    state: absent
    id: XXXXX
'''

# TODO
RETURN = '''
'''


class DciTopic(DciBase):

    def __init__(self, params):
        super(DciTopic, self).__init__(dci_topic)
        self.id = params.get('id')
        self.name = params.get('name')
        self.label = params.get('label')
        self.product_id = params.get('product_id')
        self.component_types = params.get('component_types')
        self.team_ids = params.get('team_ids')
        self.search_criterias = {
            'embed': params.get('embed'),
            'where': params.get('where')
        }
        self.deterministic_params = ['name', 'label', 'product_id',
                                     'component_types']

    def do_create(self, context):
        if not self.name:
            raise DciParameterError('name parameter must be speficied')

        return super(DciTopic, self).do_create(context)

    def do_delete(self, context):
        return self.resource.delete(context, self.id)

    def do_attach_team(self, context):
        for team in self.team_ids:
            res = dci_topic.attach_team(context, self.id, team)
        return res


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
            label=dict(type='str'),
            product_id=dict(type='str'),
            component_types=dict(type='list'),
            team_ids=dict(type='list'),
            embed=dict(type='str'),
            where=dict(type='str'),
        ),
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    context = build_dci_context(module)
    action_name = get_standard_action(module.params)
    if action_name == 'update':
        if module.params['team_ids']:
            action_name = 'attach_team'

    topic = DciTopic(module.params)
    action_func = getattr(topic, 'do_%s' % action_name)

    http_response = run_action_func(action_func, context, module)
    result = parse_http_response(http_response, dci_topic, context, module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
