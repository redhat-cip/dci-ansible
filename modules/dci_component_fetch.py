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
import os.path

try:
    from dciclient.v1.api import context as dci_context
    from dciclient.v1.api import component as dci_component
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_component
short_description: An ansible module to download a component
version_added: 2.2
options:
  state:
    required: false
    default: present
    description: Desired state of the resource
  login:
    required: false
    description: User's DCI login
  password:
    required: false
    description: User's DCI password
  component:
    required: false
    description: The component to retrive
  dest:
    required: true
    description: Path where to drop the retrieved component
  reuse:
    required: false
    description: Reuse an existing local copy of the file

'''

EXAMPLES = '''
- name: Download a component
  dci_component_fetch:
    component: {{ component }}
    dest: /srv/dci/components/{{ component_id }}
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
            component=dict(type='dict'),
            dest=dict(type='str'),
            reuse=dict(type='bool'),
        ),
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    login, password, url = get_details(module)
    if not login or not password:
        module.fail_json(msg='login and/or password have not been specified')

    ctx = dci_context.build_dci_context(url, login, password, 'Ansible')

    component_id = module.params['component']['id']

    # Action required: Download a component
    # Endpoint called: /components/<component_id>/files/<file_id>/content GET via dci_component.file_download()
    #
    # Download the component
    if not os.path.exists(module.params['dest']):
        component_file = dci_component.file_list(ctx, component_id).json()['component_files'][0]
        res = dci_component.file_download(ctx, component_id, component_file['id'], module.params['dest'])

    try:
        result = res.json()
        if res.status_code == 404:
            module.fail_json(msg='The resource does not exist')
        if res.status_code == 422:
            result =  dci_component.get(ctx, module.params['name']).json()
        if res.status_code in [400, 401, 422]:
            result['changed'] = False
        else:
            result['changed'] = True
    except:
        result = {}
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
