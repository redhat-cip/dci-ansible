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
    from dciclient.v1.api import component as dci_component
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_component
short_description: An ansible module to interact with the /components endpoint of DCI
version_added: 2.2
options:
  state:
    required: false
    default: present
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
  export_control:
    required: false
    description: Wether or not the component has been export_control approved
  dest:
    required: true
    description: Path where to drop the retrieved component
'''

EXAMPLES = '''
- name: Download a component
  dci_component:
    id: {{ component_id }}
    dest: /srv/dci/components/{{ component_id }}

- name: Retrieve component informations
  dci_component:
    id: {{ component_id }}

- name: Remove component
  dci_component:
    state: absent
    id: {{ component_id }}
'''

# TODO
RETURN = '''
'''


def get_details(module):
    """Method that retrieves the appropriate credentials. """

    login_list = [module.params['dci_login'], os.getenv('DCI_LOGIN')]
    login = next((item for item in login_list if item is not None), None)

    password_list = [module.params['dci_password'], os.getenv('DCI_PASSWORD')]
    password = next((item for item in password_list if item is not None), None)

    url_list = [module.params['dci_cs_url'], os.getenv('DCI_CS_URL')]
    url = next((item for item in url_list if item is not None), 'https://api.distributed-ci.io')

    return login, password, url


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
            dest=dict(type='str'),
            export_control=dict(type='bool'),
            name=dict(type='str'),
            type=dict(type='str'),
            canonical_project_name=dict(type='str'),
            url=dict(type='str'),
            data=dict(type='dict'),
            topic_id=dict(type='str'),
            path=dict(type='str'),
        ),
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    login, password, url = get_details(module)
    if not login or not password:
        module.fail_json(msg='login and/or password have not been specified')

    ctx = dci_context.build_dci_context(url, login, password, 'Ansible')

    # Action required: Delete the component matching the component id
    # Endpoint called: /components/<component_id> DELETE via dci_component.delete()
    #
    # If the component exist and it has been succesfully deleted the changed is
    # set to true, else if the file does not exist changed is set to False
    if module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_component.delete(ctx, module.params['id'])

    # Action required: Attach a file to a component
    # Endpoint called: /components/<component_id>/files/ POST via dci_component.file_upload()
    #
    # Attach file to a component
    elif module.params['path']:
        res = dci_component.file_upload(ctx, module.params['id'], module.params['path'])

    # Action required: Download a component
    # Endpoint called: /components/<component_id>/files/<file_id>/content GET via dci_component.file_download()
    #
    # Download the component
    elif module.params['dest']:
        component_file = dci_component.file_list(ctx, module.params['id']).json()['component_files'][0]
        res = dci_component.file_download(ctx, module.params['id'], component_file['id'], module.params['dest'])

    # Action required: Get component informations
    # Endpoint called: /components/<component_id> GET via dci_component.get()
    #
    # Get component informations
    elif module.params['id'] and module.params['export_control'] is None:
        res = dci_component.get(ctx, module.params['id'])

    # Action required: Update an existing component
    # Endpoint called: /components/<component_id> PUT via dci_component.update()
    #
    # Update the component with the specified parameters.
    elif module.params['id']:
        res = dci_component.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 422]:
            updated_kwargs = {
                'id': module.params['id'],
                'etag': res.json()['component']['etag']
            }
            if module.params['export_control'] is not None:
                updated_kwargs['export_control'] = module.params['export_control']

            res = dci_component.update(ctx, **updated_kwargs)

    # Action required: Create a new component
    # Endpoint called: /component POST via dci_component.create()
    #
    # Create a new component
    else:
        if not module.params['name']:
            module.fail_json(msg='name parameter must be speficied')
        if not module.params['type']:
            module.fail_json(msg='type parameter must be speficied')

        kwargs = {
            'name': module.params['name'],
            'type': module.params['type'],
        }

        if module.params['canonical_project_name']:
            kwargs['canonical_project_name'] = module.params['canonical_project_name']
        if module.params['url']:
            kwargs['url'] = module.params['url']
        if module.params['data']:
            kwargs['data'] = module.params['data']
        if module.params['topic_id']:
            kwargs['topic_id'] = module.params['topic_id']
        res = dci_component.create(ctx, **kwargs)

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
