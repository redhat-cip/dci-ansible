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
    description: ID of the topic to interact with
  name:
    required: false
    description: Topic name
  label:
    required: false
    description: Topic label
'''

EXAMPLES = '''
- name: Create a new topic
  dci_topic:
    name: 'Soft21'


- name: Create a new topic 
  dci_topic:
    name: 'Soft42'
    label: 'The latest version of Soft with the 42 feature'


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
            label=dict(type='str'),
        ),
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    login, password, url = get_details(module)
    if not login or not password:
        module.fail_json(msg='login and/or password have not been specified')

    ctx = dci_context.build_dci_context(url, login, password, 'Ansible')

    # Action required: Delete the topic matching topic id
    # Endpoint called: /topics/<topic_id> DELETE via dci_topic.delete()
    #
    # If the topic exists and it has been succesfully deleted the changed is
    # set to true, else if the topic does not exist changed is set to False
    if module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_topic.delete(ctx, module.params['id'])

    # Action required: Retrieve topic informations
    # Endpoint called: /topic/<topic_id> GET via dci_topic.get()
    #
    # Get topic informations
    elif module.params['id'] and not module.params['name'] and not module.params['label']:
        res = dci_topic.get(ctx, module.params['id'])

    # Action required: Update an existing topic
    # Endpoint called: /topics/<topic_id> PUT via dci_topic.update()
    #
    # Update the topic with the specified characteristics.
    elif module.params['id']:
        res = dci_topic.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 422]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['topic']['etag']
            }
            if module.params['name']:
                kwargs['name'] = module.params['name']
            if module.params['label']:
                kwargs['label'] = module.params['label']
            res = dci_topic.update(ctx, **kwargs)


    # Action required: Creat a topic with the specified content
    # Endpoint called: /topics POST via dci_topic.create()
    #
    # Create the new topic.
    else:
        if not module.params['name']:
            module.fail_json(msg='name parameter must be specified')

        kwargs = {'name': module.params['name']}
        if module.params['label']:
            kwargs['label'] = module.params['label']

        res = dci_topic.create(ctx, **kwargs)

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
