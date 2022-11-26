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

import os

try:
    from dciclient.v1.api import component as dci_component
    from dciclient.v1.api import topic as dci_topic
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_component
short_description: module to interact with the components endpoint of DCI
description:
  - DCI module to manage the component resources
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
  dest:
    required: true
    description: Path where to drop the retrieved component
  active:
    required: false
    description: Wether of not the resource should be active
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

- name: list components and sort result
  dci_component:
    state: search
    topic_id: '{{ topic_id }}'
    sort: name
    register: list_components
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

    resource_argument_spec = dict(
        state=dict(
            default='present',
            choices=['present', 'absent', 'search'],
            type='str'),
        id=dict(type='str'),
        dest=dict(type='str'),
        name=dict(type='str'),
        type=dict(type='str'),
        canonical_project_name=dict(type='str'),
        url=dict(type='str'),
        data=dict(type='dict'),
        topic_id=dict(type='str'),
        team_id=dict(type='str'),
        path=dict(type='str'),
        active=dict(default=True, type='bool'),
        embed=dict(type='str'),
        tags=dict(type='str'),
        sort=dict(type='str')
    )
    resource_argument_spec.update(authentication_argument_spec())

    module = AnsibleModule(
        argument_spec=resource_argument_spec,
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    ctx = build_dci_context(module)

    # Action required: Delete the component matching the component id
    # Endpoint called: /components/<component_id> DELETE
    #                  via dci_component.delete()
    #
    # If the component exist and it has been succesfully deleted the changed is
    # set to true, else if the file does not exist changed is set to False
    if module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_component.delete(ctx, module.params['id'])

    # Action required: Attach a file to a component
    # Endpoint called: /components/<component_id>/files/ POST
    #                  via dci_component.file_upload()
    #
    # Attach file to a component
    elif module.params['path']:
        res = dci_component.file_upload(
            ctx,
            module.params['id'],
            module.params['path'])

    # Action required: Download a component
    # Endpoint called: /components/<component_id>/files/<file_id>/content GET
    #          via dci_component.file_download()
    #
    # Download the component
    elif module.params['dest']:
        res = download_file(module, ctx)

    # Get or update
    elif module.params['id']:
        is_update = module.params['url'] or module.params['data'] or module.params['tags']

        if not is_update:
            # Action required: Get component informations
            # Endpoint called: /components/<component_id> GET
            #                  via dci_component.get()
            #
            # Get component informations
            kwargs = {}
            if module.params['embed']:
                kwargs['embed'] = module.params['embed']
            res = dci_component.get(ctx, module.params['id'], **kwargs)
        else:
            # Action required: Update an existing component
            # Endpoint called: /components/<component_id> PUT
            #                  via dci_component.update()
            #
            # Update the component with the specified parameters.
            res = dci_component.get(ctx, module.params['id'])
            if res.status_code not in [400, 401, 404, 409]:
                updated_kwargs = {
                    'id': module.params['id'],
                    'etag': res.json()['component']['etag']
                }
                if module.params['active']:
                    updated_kwargs['state'] = 'active'
                else:
                    updated_kwargs['state'] = 'inactive'
                for key in ('url', 'data', 'tags'):
                    if key in module.params:
                        if key == 'tags':
                            updated_kwargs[key] = list(set(module.params[key].split(',')))
                        else:
                            updated_kwargs[key] = module.params[key]
                res = dci_component.update(ctx, **updated_kwargs)
    # Action required: Create a new component
    # Endpoint called: /component POST via dci_component.create()
    #
    # Create a new component
    elif module.params['state'] == 'present':
        if not module.params['name']:
            module.fail_json(msg='name parameter must be speficied')
        if not module.params['type']:
            module.fail_json(msg='type parameter must be speficied')

        kwargs = {
            'name': module.params['name'],
            'type': module.params['type'],
        }

        if module.params['canonical_project_name']:
            canonical_project_name = module.params['canonical_project_name']
            kwargs['canonical_project_name'] = canonical_project_name
        if module.params['url']:
            kwargs['url'] = module.params['url']
        if module.params['data']:
            kwargs['data'] = module.params['data']
        if module.params['topic_id']:
            kwargs['topic_id'] = module.params['topic_id']
        if module.params['team_id']:
            kwargs['team_id'] = module.params['team_id']
        kwargs['state'] = 'active' if module.params['active'] else 'inactive'
        res = dci_component.create(ctx, **kwargs)

    # Action required: Search components in a topic
    # Endpoint called: /topics/<id>/components POST
    # via dci_topic.list_components()
    #
    # Search for components in a topic
    elif module.params['state'] == 'search':
        if not module.params['topic_id']:
            module.fail_json(msg='topic_id parameter must be speficied')

        clause = ""
        for key in ('name', 'type', 'canonical_project_name',
                    'team_id', 'tags'):
            if module.params[key]:
                clause += '%s:%s,' % (key, module.params[key])
        kwargs = {}
        if clause:
            kwargs = {'where': clause[:-1]}
        if module.params["sort"]:
            kwargs["sort"] = module.params["sort"]
        res = dci_topic.list_components(
            ctx, module.params['topic_id'], **kwargs)

    else:
        module.fail_json(msg='Unknown arguments')

    try:
        result = res.json()
        if res.status_code == 401:
            module.fail_json(
                msg='Not enough permissions to access the resource'
            )
        if res.status_code == 404:
            module.fail_json(msg='The resource does not exist')
        if res.status_code == 409:
            result = {
                'component': dci_topic.list_components(
                    ctx, module.params['topic_id'],
                    where='name:' + module.params['name']
                ).json()['components'][0],
            }
        if res.status_code in [400, 401, 409]:
            if module.params['state'] == 'search':
                module.fail_json(
                    msg=('The components do not exist in topic %s %s'
                         % (module.params['topic_id'], kwargs)))
            else:
                result['changed'] = False
        else:
            result['changed'] = True
    except Exception:
        result = {}
        result['changed'] = False

    module.exit_json(**result)


if __name__ == '__main__':
    main()
