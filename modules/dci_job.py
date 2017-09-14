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
from ansible.module_utils.common import build_dci_context, module_params_empty

import os

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
  id:
    required: false
    description: ID of the job
  comment:
    required: false
    description: Comment attached to the job
  status:
    required: false
    description: Status the job should be entitled
  metadata:
    required: false
    description: Metadatas attached to the job
  upgrade:
    required: false
    description: Schedule an upgrade job
  components:
    required: false
    description: list of ID to associated to the new job
  team_id:
    required: false
    description: team of the new job
  embed:
    required: false
    description:
      - List of field to embed within the retrieved resource
'''

EXAMPLES = '''
- name: Schedule a new job
  dci_job:
    topic: 'OSP10'

- name: Update job
  dci_job:
    id: '{{ job_id }}'
    comment: 'New comment for my job'

- name: Remove a job
  dci_job:
    state: absent
    id: '{{ job_id }}'

- name: Schedule an upgrade job
  dci_job:
    id: '{{ job_id }}'
    upgrade: true

- name: Manually create a job
  dci_job:
    topic: 'OSP8'
    comment: 'job created manually'
    components: ['4c282108-5086-454b-8d49-4b1d0345acd9', '4c8ec5c8-ec24-4253-abbf-63a4daddba8b']

 - name: Notify for a specific reason
   dci_job:
     notify: "Specific comment"
'''

# TODO
RETURN = '''
'''


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
            topic=dict(required=False, type='str'),
            comment=dict(type='str'),
            status=dict(type='str'),
            metadata=dict(type='dict'),
            notify=dict(type='dict'),
            upgrade=dict(type='bool'),
            components=dict(type='list', default=[]),
            team_id=dict(type='str'),
            embed=dict(type='list'),
        ),
    )

    if not dciclient_found:
        module.fail_json(msg='The python dciclient module is required')

    ctx = build_dci_context(module)

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
    elif (module.params['id'] and
          not module.params['comment'] and
          not module.params['status'] and
          not module.params['metadata'] and
          not module.params['upgrade']):
        kwargs = {}
        if module.params['embed']:
            kwargs['embed'] = module.params['embed']
        res = dci_job.get(ctx, module.params['id'], **kwargs)

    # Action required: Update an existing job
    # Endpoint called: /jobs/<job_id> PUT via dci_job.update()
    #
    # Update the job with the specified characteristics.
    elif module.params['id'] and not module.params['upgrade']:
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
            if module.params['metadata']:
                for k, v in module.params['metadata'].items():
                    dci_job.set_meta(ctx, module.params['id'], k, str(v))
            res = dci_job.update(ctx, **kwargs)

    # Action required: Schedule an upgrade job
    # Endpoint called: /jobs/upgrade POST via dci_job.upgrade()
    #
    # Schedule an upgrade job using the next topic
    elif module.params['id'] and module.params['upgrade']:
        res = dci_job.upgrade(ctx, job_id=module.params['id'])
        if res.status_code not in [400, 401, 404, 409]:
            res = dci_job.get_full_data(ctx, ctx.last_job_id)

    # Send a notification
    elif module.params['notify']:
        res = dci_job.notify(ctx, ctx.last_job_id, mesg=module.params['notify'])

    # Manually create the job
    elif module.params['components']:
        topic_id = dci_topic.list(ctx, where='name:' + module.params['topic']).json()['topics'][0]['id']
        res = dci_job.create(
            ctx,
            remoteci_id=ctx.session.auth.client_id,
            team_id=module.params['team_id'],
            topic_id=topic_id,
            components=module.params['components'],
            comment=module.params['comment'])
        if res.status_code == 201:
            res = dci_job.get_full_data(ctx, ctx.last_job_id)

    # Action required: Schedule a new job
    # Endpoint called: /jobs/schedule POST via dci_job.schedule()
    #
    # Schedule a new job against the DCI Control-Server
    else:
        topic_id = dci_topic.list(ctx, where='name:' + module.params['topic']).json()['topics'][0]['id']

        res = dci_job.schedule(
            ctx,
            remoteci_id=ctx.session.auth.client_id,
            topic_id=topic_id)
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
