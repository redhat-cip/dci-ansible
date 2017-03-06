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
import yaml

try:
    from dciclient.v1.api import context as dci_context
    from dciclient.v1.api import job as dci_job
    from dciclient.v1.api import remoteci as dci_remoteci
    from dciclient.v1.api import topic as dci_topic
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_job
short_description: An ansible module to interact with the /jobs endpoint of DCI
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
  topic:
    required: false
    description: Topic for which the job will be schedule
  remoteci:
    required: false
    description: RemoteCI for which the job will be schedule
  id:
    required: false
    description: ID of the job
  comment:
    required: false
    description: Comment attached to the job
  status:
    required: false
    description: Status the job should be entitled
  configuration:
    required: false
    description: Configuration attached to the job
  metadata:
    required: false
    description: Metadatas attached to the job
'''

EXAMPLES = '''
- name: Schedule a new job
  dci_job:
    remoteci: 'MyRCI'


- name: Update job
  dci_job:
    id: '{{ job_id }}'
    comment: 'New comment for my job'

- name: Remove a job
  dci_job:
    state: absent
    id: '{{ job_id }}'
'''

# TODO
RETURN = '''
'''


def module_params_empty(module_params):

    for item in module_params:
        if item != 'state' and module_params[item] is not None:
            return False

    return True


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
            topic=dict(required=False, type='str'),
            remoteci=dict(required=False, type='str'),
            comment=dict(type='str'),
            status=dict(type='str'),
            configuration=dict(type='dict'),
            metadata=dict(type='dict'),
        ),
    )
    config = get_config(module)

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    if not set(['login', 'password']).issubset(config):
        module.fail_json(msg='login and/or password have not been specified')

    ctx = dci_context.build_dci_context(
        config['cs_url'], config['login'],
        config['password'], 'Ansible')

    # Action required: List all jobs
    # Endpoint called: /jobs GET via dci_job.list()
    #
    # List all jobs
    if module_params_empty(module.params):
        res = dci_job.list(ctx)

    # Action required: Delete the job matching the job id
    # Endpoint called: /jobs/<job_id> DELETE via dci_job.delete()
    #
    # If the job exist and it has been succesfully deleted the changed is
    # set to true, else if the file does not exist changed is set to False
    elif module.params['state'] == 'absent':
        if not module.params['id']:
            module.fail_json(msg='id parameter is required')
        res = dci_job.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['job']['etag']
            }
            res = dci_job.delete(ctx, **kwargs)

    # Action required: Retrieve job informations
    # Endpoint called: /jobs/<job_id> GET via dci_job.get()
    #
    # Get job informations
    elif module.params['id'] and not module.params['comment'] and not module.params['status'] and not module.params['configuration'] and not module.params['metadata']:
        res = dci_job.get(ctx, module.params['id'])

    # Action required: Update an existing job
    # Endpoint called: /jobs/<job_id> PUT via dci_job.update()
    #
    # Update the job with the specified characteristics.
    elif module.params['id']:
        res = dci_job.get(ctx, module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            kwargs = {
                'id': module.params['id'],
                'etag': res.json()['job']['etag']
            }
            if module.params['comment']:
                kwargs['comment'] = module.params['comment']
            if module.params['status']:
                kwargs['status'] = module.params['status']
            if module.params['configuration']:
                kwargs['configuration'] = module.params['configuration']
            if module.params['metadata']:
                for k, v in module.params['metadata'].items():
                    dci_job.set_meta(ctx, module.params['id'], k, v)
            res = dci_job.update(ctx, **kwargs)

    # Action required: Schedule a new job
    # Endpoint called: /jobs/schedule POST via dci_job.schedule()
    #
    # Schedule a new job against the DCI Control-Server
    else:
        topic_id = dci_topic.list(ctx, where='name:' + module.params['topic']).json()['topics'][0]['id']
        remoteci_id = dci_remoteci.list(ctx, where='name:' + module.params['remoteci']).json()['remotecis'][0]['id']

        res = dci_job.schedule(ctx, remoteci_id, topic_id=topic_id)
        if res.status_code not in [400, 401, 404, 409]:
            res = dci_job.get_full_data(ctx, ctx.last_job_id)

    try:
        result = res.json()
        if res.status_code == 404:
            module.fail_json(msg='The resource does not exist')
        if res.status_code in [400, 401, 409]:
            result['changed'] = False
        else:
            result['changed'] = True
    except AttributeError:
        # Enter here if new job has been schedule, return of get_full_data is already json.
        result = res
        result['changed'] = True
        result['job_id'] = ctx.last_job_id
    except:
        result = {}
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
