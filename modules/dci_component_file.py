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
import shutil
import tarfile

try:
    from dciclient.v1.api import context as dci_context
    from dciclient.v1.api import component as dci_component
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_component_file
short_description: Interact with the files associated to a DCI component
options:
  dci_login:
    required: false
    description: User's DCI login
  dci_password:
    required: false
    description: User's DCI password
  dci_cs_url:
    required: false
    description: DCI Control Server URL
  file_id:
    required: false
    description: The ID of the file.
  dest:
    required: false
    description: Directory where to store the downloaded file. If file_id is defined, only the given file will be download, otherwise, all the files are downloaded.
  cache:
    required: false
    description: Directory where to cache the downloaded files.
  src:
    required: false
    description: Location of the local file during the upload
  mime:
    required: false
    description: The name of the file
  size:
    required: false
    description: The size of the file
  component_id:
    required: false
    description: The ID of the component associated to the file
  state:
    required: true
    description: the state of the file
    choices: [ 'present', 'absent' ]
'''

EXAMPLES = '''
- name: Download all the files from a component and extract them
  dci_component_file:
    component_id: foo
    dest: /srv/dci/components/
    cache: /root/.cache/dci/
    extract: true

- name: Download one file from a component
  dci_component_file:
    component_id: foo
    file_id: bar
    dest: /srv/dci/components/

- name: Add a component
  dci_component_file:
    component_id: foo
    src: /tmp/by_tarball.tar

- name: Remove all the files for a component
  dci_component_file:
    component_id: foo
    state: absent

- name: Remove one file for a component
  dci_component_file:
    component_id: foo
    file_id: bar
    state: absent

- name: List all the files from a component
  dci_component_file:
    component_id: foo

- name: Get detail of just one file
  dci_component_file:
    component_id: foo
    file_id: bar
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


def check_http_code(module, response, expectation):
    if str(response.status_code) not in expectation:
        module.fail_json(msg='Unexpected error code (%s): %s' % (
            response.status_code, response.text))


def get_file_ids(module, ctx):
    if module.params.get('file_id'):
        file_ids = [module.params.get('file_id')]
    else:  # we take all the files of the component
        res = dci_component.file_list(
            ctx,
            module.params['component_id'])
        component_files = res.json()['component_files']
        check_http_code(module, res, ('200'))
        file_ids = [i['id'] for i in component_files]
    return file_ids


def main():
    changed = False
    result = {}
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
            file_id=dict(type='str'),
            dest=dict(type='str'),
            src=dict(type='str'),
            mime=dict(type='str'),
            cache=dict(type='str'),
            extract=dict(type='str'),
            size=dict(type='int'),
            component_id=dict(type='str'),
        ),
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    login, password, url = get_details(module)
    if not login or not password:
        module.fail_json(msg='login and/or password have not been specified')
    dest_dir = module.params.get('dest')

    ctx = dci_context.build_dci_context(url, login, password, 'Ansible')

    # delete
    if module.params.get('state') == 'absent':
        for file_id in get_file_ids(module, ctx):
            res = dci_component.file_delete(
                ctx,
                module.params['component_id'],
                file_id)
            check_http_code(module, res, ('202'))
            changed = True
    # create
    elif module.params.get('src'):
            res = dci_component.file_list(
                ctx,
                module.params['component_id'])
            check_http_code(module, res, ('200'))
            # NOTE(Goneri): we don't have yet a way to know if a
            # file a already upload
            if len(res.json()['component_files']) == 0:
                res = dci_component.file_upload(
                    ctx,
                    module.params['component_id'],
                    module.params['src'])
                check_http_code(module, res, ('201'))
                changed = True
                result = res.json()
            else:
                result = {'component_file': res.json()['component_files'][0]}
    # download (and extract)
    elif module.params.get('dest'):
        for file_id in get_file_ids(module, ctx):
            cache_dir = module.params.get('cache')
            if cache_dir:
                target = cache_dir + '/' + file_id + '.tar'
            else:
                target = dest_dir + '/' + file_id + '.tar'
            # Since we have a cache, we only download the missing files
            if not os.path.exists(target):
                res = dci_component.file_download(
                    ctx,
                    module.params['component_id'],
                    file_id,
                    target)
            if module.params.get('extract'):
                with tarfile.open(name=target, mode='r:') as tf:
                    tf.extractall(path=dest_dir)
            elif cache_dir:
                shutil.copyfile(target, cache_dir)
    # get information
    else:
        result['component_files'] = []
        for file_id in get_file_ids(module, ctx):
            res = dci_component.file_get(
                ctx,
                module.params['component_id'],
                file_id)
            check_http_code(module, res, ('200'))
            changed = True
            result['component_files'].append(res.json()['component_file'])


    result['changed'] = changed

    module.exit_json(**result)


if __name__ == '__main__':
    main()
