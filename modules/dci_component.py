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
from ansible.module_utils.dci_base import *

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
  where:
    required: false
    description: Specific criterias for search
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


class DciComponent(DciBase):

    def __init__(self, params):
        super(DciComponent, self).__init__(dci_component)
        self.id = params.get('id')
        self.name = params.get('name')
        self.dest = params.get('dest')
        self.path = params.get('path')
        self.export_control = params.get('export_control')
        self.type = params.get('type')
        self.canonical_project_name = params.get('canonical_project_name')
        self.url = params.get('url')
        self.data = params.get('data')
        self.topic_id = params.get('topic_id')
        self.search_criterias = {
            'embed': params.get('embed'),
            'where': params.get('where')
        }
        self.deterministic_params = ['name', 'dest', 'path', 'export_control',
                                     'type', 'canonical_project_name', 'url',
                                     'data', 'topic_id']

    def do_download(self, context):
        if os.path.isdir(self.dest):
            dest_file = os.path.join(self.dest, self.id + '.tar')
        else:
            dest_file = self.dest

        if os.path.isfile(dest_file):
            #TODO(DO NOT MERGE YET)
            module.exit_json(changed=False)
        else:
            component_files = dci_component.file_list(
                context,
                self.id).json()['component_files']
            component_file_id = component_files[0]['id']
            return dci_component.file_download(
                context, self.id, component_file_id, dest_file
            )

    def do_delete(self, context):
        return dci_component.delete(context, self.id)

    def do_upload(self, context):
        return dci_component.file_upload(context, self.id, self.path)

    def do_create(self, context):
        for param in ['name', 'type']:
            if not getattr(self, param):
                raise DciParameterError(
                    '%s parameter must be speficied' % param
                )

        return super(DciComponent, self).do_create(context)


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
            where=dict(type='str'),
        ),
        required_if=[['state', 'absent', ['id']]],
        mutually_exclusive=[['dest', 'path']]
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    context = build_dci_context(module)
    action_name = get_action(module.params)

    component = DciComponent(module.params)
    action_func = getattr(component, 'do_%s' % action_name)

    try:
        res = action_func(context)
    except DciResourceNotFoundException as exc:
        module.fail_json(msg=exc.message)
    except DciServerErrorException as exc:
        module.fail_json(msg=exc.message)
    except DciUnexpectedErrorException as exc:
        module.fail_json(msg=exc.message)
    except DciParameterError as exc:
        module.fail_json(msg=exc.message)
    except (KeyError, IndexError):
        module.fail_json(
            msg='Failed to get the component_files from the server.'
        )

    try:
        result = res.json()
        if res.status_code == 404:
            module.fail_json(msg='The resource does not exist')
        if res.status_code == 409:
            result = {
                'component': dci_topic.list_components(
                             context,
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
