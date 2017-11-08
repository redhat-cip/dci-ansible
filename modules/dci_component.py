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
from ansible.module_utils.common import build_dci_context, get_action

import os

try:
    from dciclient.v1.api import context as dci_context
    from dciclient.v1.api import component as dci_component
    from dciclient.v1.api import topic as dci_topic
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
  embed:
    required: false
    description:
      - List of field to embed within the retrieved resource
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

def download_file(module, ctx):
    if os.path.isdir(module.params['dest']):
        dest_file = os.path.join(
            module.params['dest'],
            module.params['id'] + '.tar')
    else:
        dest_file = module.params['dest']

    if os.path.isfile(dest_file):
        module.exit_json(changed=False)
    else:
        try:
            component_files = dci_component.file_list(
                ctx,
                module.params['id']).json()['component_files']
            component_file_id = component_files[0]['id']
        except (KeyError, IndexError):
            module.fail_json(
                msg='Failed to get the component_files from the server.')
        return dci_component.file_download(
            ctx,
            module.params['id'],
            component_file_id,
            dest_file)

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
            dest=dict(type='str'),
            export_control=dict(type='bool'),
            name=dict(type='str'),
            type=dict(type='str'),
            canonical_project_name=dict(type='str'),
            url=dict(type='str'),
            data=dict(type='dict'),
            topic_id=dict(type='str'),
            path=dict(type='str'),
            embed=dict(type='list'),
        ),
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    ctx = build_dci_context(module)
    action = get_action(module.params)

    if action == 'delete':
        res = dci_component.delete(ctx, module.params['id'])

    elif module.params['path']:
        res = dci_component.file_upload(ctx, module.params['id'], module.params['path'])

    elif module.params['dest']:
        res = download_file(module, ctx)

    elif action == 'list':
        kwargs = {}
        if module.params['embed']:
            kwargs['embed'] = module.params['embed']
        res = dci_component.get(ctx, module.params['id'], **kwargs)

    elif action == 'update':
        res = dci_component.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            updated_kwargs = {
                'id': module.params['id'],
                'etag': res.json()['component']['etag']
            }
            if module.params['export_control'] is not None:
                updated_kwargs['export_control'] = module.params['export_control']

            res = dci_component.update(ctx, **updated_kwargs)

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
        if res.status_code == 409:
            result = {
                'component': dci_topic.list_components(
                             ctx,
                             module.params['topic_id'],
                             where='name:' + module.params['name']
                             ).json()['components'][0],
            }
        if res.status_code in [400, 401, 409]:
            result['changed'] = False
        else:
            result['changed'] = True
    except:
        result = {}
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
