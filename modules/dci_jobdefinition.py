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
    from dciclient.v1.api import jobdefinition as dci_jobdefinition
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_jobdefinition
short_description: An ansible module to interact with the /jobdefinitions endpoint of DCI
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
    description: ID of the jobdefinition to interact with
  name:
    required: false
    description: Jobdefinition name
  priority:
    required: false
    description: Jobdefinition priority
  topic_id:
    required: false
    description: ID of the topic the jobdefinition will be attached to
  active:
    required: false
    description: Wether or not the jobdefinition is active
  comment:
    required: false
    description: A comment to attach to the job definition
  component_types:
    required: false
    description: Jobdefinition's component_types
'''

EXAMPLES = '''
- name: Create a new jobdefinition
  dci_jobdefinition:
    name: 'jobdef-1'
    topic_id: XXXX
    component_types: {""}


- name: Get jobdefinition information
  dci_jobdefinition:
    id: XXXXX


- name: Update jobdefinition informations
  dci_jobdefinition:
    id: XXXX
    active: False


- name: Delete a jobdefinition
  dci_jobdefinition:
    state: absent
    id: XXXXX
'''

# TODO
RETURN = '''
'''


def get_config(module):
    from_file = {}
    if os.path.exists('/etc/dci/dci.yaml'):
        with open('/etc/dci/dci.yaml') as fd:
            from_file = yaml.load(fd)

    return {
        'login':
            module.params.get('dci_login')
            or os.getenv('DCI_LOGIN')
            or from_file.get('login'),
        'password':
            module.params.get('dci_password')
            or os.getenv('DCI_PASSWORD')
            or from_file.get('password'),
        'cs_url':
            module.params.get('dci_cs_url')
            or os.getenv('DCI_CS_URL')
            or from_file.get('cs_url')
            or 'https://api.distributed-ci.io',
        'remoteci':
            module.params.get('remoteci')
            or os.getenv('DCI_REMOTECI')
            or from_file.get('remoteci'),
        'topic':
            module.params.get('topic')
            or os.getenv('DCI_TOPIC')
            or from_file.get('topic')
        }


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
            dci_password=dict(required=False, type='str'),
            dci_cs_url=dict(required=False, type='str'),
            # Resource related parameters
            #
            id=dict(type='str'),
            name=dict(type='str'),
            priority=dict(type='int'),
            topic_id=dict(type='str'),
            active=dict(type='bool'),
            comment=dict(type='str'),
            component_types=dict(type='list'),
        ),
    )
    config = get_config(module)

    if not dciclient_found:
        module.fail_json(msg='the python dciclient module is required')

    if not set(['login', 'password']).issubset(config):
        module.fail_json(msg='login and/or password have not been specified')

    ctx = dci_context.build_dci_context(
        config['cs_url'], config['login'],
        config['password'], 'ansible')

    # Action required: List all jobdefinitions
    # Endpoint called: /jobdefinitions GET via dci_jobdefinition.list()
    #
    # List all jobdefinitions
    if module_params_empty(module.params):
        res = dci_jobdefinition.list(ctx)

    # Action required: Delete the jobdefinition matching jobdefinition id
    # Endpoint called: /jobdefinitions/<jobdefinition_id> DELETE via dci_jobdefinition.delete()
    #
    # If the jobdefinition exists and it has been succesfully deleted the changed is
    # set to true, else if the jobdefinition does not exist changed is set to False
    elif module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_jobdefinition.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 422]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['jobdefinition']['etag']
            }
            res = dci_jobdefinition.delete(ctx, **kwargs)

    # Action required: Retrieve jobdefinition informations
    # Endpoint called: /jobdefinitions/<jobdefinition_id> GET via dci_jobdefinition.get()
    #
    # Get jobdefinition informations
    elif module.params['id'] and not module.params['comment'] and not module.params['component_types'] and module.params['active'] is None:
        res = dci_jobdefinition.get(ctx, module.params['id'])

    # Action required: Update an existing jobdefinition
    # Endpoint called: /jobdefinitions/<jobdefinition_id> PUT via dci_jobdefinition.update()
    #
    # Update the jobdefinition with the specified characteristics.
    elif module.params['id']:
        res = dci_jobdefinition.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 422]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['jobdefinition']['etag']
            }
            if module.params['comment']:
                kwargs['comment'] = module.params['comment']
            if module.params['component_types']:
                kwargs['component_types'] = module.params['component_types']
            if module.params['active'] is not None:
                kwargs['active'] = module.params['active']
            res = dci_jobdefinition.update(ctx, **kwargs)


    # Action required: Creat a jobdefinition with the specified content
    # Endpoint called: /jobdefinitions POST via dci_jobdefinition.create()
    #
    # Create the new jobdefinition.
    else:
        if not module.params['name']:
            module.fail_json(msg='name parameter must be specified')
        if not module.params['topic_id']:
            module.fail_json(msg='topic_id parameter must be specified')

        kwargs = {
            'name': module.params['name'],
            'topic_id': module.params['topic_id']
        }
        if module.params['priority']:
            kwargs['priority'] = module.params['priority']
        if module.params['comment']:
            kwargs['comment'] = module.params['comment']
        if module.params['component_types']:
            kwargs['component_types'] = module.params['component_types']
        if module.params['active'] is not None:
            kwargs['active'] = module.params['active']

        res = dci_jobdefinition.create(ctx, **kwargs)

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
