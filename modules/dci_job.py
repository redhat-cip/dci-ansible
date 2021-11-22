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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dci_common import (authentication_argument_spec,
                                             build_dci_context,
                                             get_standard_action,
                                             parse_http_response,
                                             run_action_func)
from ansible.module_utils.dci_base import (
    DciBase,
    DciResourceNotFoundException,
    DciUnauthorizedAccessException,
    DciUnexpectedErrorException,
    DciServerErrorException,
)

try:
    from dciclient.v1.api import job as dci_job
    from dciclient.v1.api import topic as dci_topic
    from dciclient.v1.api import jobstate as dci_jobstate
except ImportError:
    dciclient_found = False
else:
    dciclient_found = True


DOCUMENTATION = '''
---
module: dci_job
short_description: An ansible module to interact with the /jobs endpoint of DCI
description:
  - DCI module to manage the job resources
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
  tags:
    required: false
    description: Tags attached to the job
  update:
    required: false
    description: Schedule an update job
  upgrade:
    required: false
    description: Schedule an upgrade job
  components:
    required: false
    description: list of ID to associated to the new job
  team_id:
    required: false
    description: team of the new job
  url:
    required: false
    description: URL attached to the job
  name:
    required: false
    description: name of the job
  configuration:
    required: false
    description: configuration name of the job
  previous_job_id:
    required: false
    description: previous job
  status_reason:
    required: false
    description: explanation of the status
  embed:
    required: false
    description:
      - List of field to embed within the retrieved resource
  where:
    required: false
    description: Specific criterias for search
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

- name: Schedule an update job
  dci_job:
    id: '{{ job_id }}'
    update: true

- name: Manually create a job
  dci_job:
    topic: 'OSP8'
    comment: 'job created manually'
    components: [
      '4c282108-5086-454b-8d49-4b1d0345acd9',
      '4c8ec5c8-ec24-4253-abbf-63a4daddba8b']

- name: Manually create a job with query
  dci_job:
    topic: 'OCP-4.4'
    components_by_query: [
      'name:4.4.5']

'''

# TODO
RETURN = '''
'''


def _nonify(value):
    return None if not value else value


class DciJob(DciBase):

    def __init__(self, params):
        super(DciJob, self).__init__(dci_job)
        self.id = params.get('id')
        self.topic = params.get('topic')
        self.comment = params.get('comment')
        self.status = params.get('status')
        self.tags = params.get('tags')
        self.update = params.get('update')
        self.upgrade = params.get('upgrade')
        self.components = params.get('components', [])
        self.components_by_query = params.get('components_by_query', [])
        self.team_id = params.get('team_id')
        self.url = _nonify(params.get('url'))
        self.name = _nonify(params.get('name'))
        self.configuration = _nonify(params.get('configuration'))
        self.previous_job_id = _nonify(params.get('previous_job_id'))
        self.status_reason = _nonify(params.get('status_reason'))
        self.search_criterias = {
            'embed': params.get('embed'),
            'where': params.get('where')
        }
        self.deterministic_params = ['topic', 'comment', 'status',
                                     'tags', 'team_id', 'url', 'name',
                                     'configuration', 'status_reason',
                                     'previous_job_id']

    def do_set_tags(self, context):
        for tag_name in self.tags:
            res = dci_job.add_tag(context, self.id, tag_name)
            if res.status_code != 200:
                self.raise_error(res)

        return dci_job.get(context, self.id)

    def do_job_update(self, context):
        res = dci_job.job_update(context, job_id=self.id)

        if res.status_code == 201:
            return dci_job.get(
                context, context.last_job_id,
                embed='topic,remoteci,components')
        else:
            self.raise_error(res)

    def do_upgrade(self, context):
        res = dci_job.upgrade(context, job_id=self.id)

        if res.status_code == 201:
            return dci_job.get(
                context, context.last_job_id,
                embed='topic,remoteci,components')
        else:
            self.raise_error(res)

    def do_schedule(self, context):
        topic_res = dci_topic.list(context, where='name:' + self.topic)

        if topic_res.status_code == 200:
            topics = topic_res.json()['topics']
            if len(topics) == 0:
                raise DciResourceNotFoundException(
                    'Not found or not enough permissions for topic %s' %
                    self.topic
                )

            topic_id = topics[0]['id']
            res = dci_job.schedule(context, topic_id,
                                   comment=self.comment,
                                   configuration=self.configuration,
                                   name=self.name,
                                   url=self.url,
                                   previous_job_id=self.previous_job_id,
                                   )
            if res.status_code == 201:
                return dci_job.get(
                    context, context.last_job_id,
                    embed='topic,remoteci,components')
            else:
                self.raise_error(res)

        else:
            self.raise_error(topic_res)

    def do_get(self, context):
        return dci_job.get(
            context, self.id,
            **self.search_criterias)

    def find_components(self, context, topic_id):
        components = []
        for component in self.components_by_query:
            components_res = dci_topic.list_components(context,
                                                       topic_id,
                                                       where=component)
            if components_res.status_code < 400:
                if components_res.status_code == 200:
                    _components = components_res.json()['components']
                    if len(_components) == 0:
                        raise DciResourceNotFoundException(
                            'Not found or not enough permissions '
                            'for component %s' % component
                        )
                    components.append(_components[0]['id'])
            elif components_res.status_code in [401, 412]:
                raise DciUnauthorizedAccessException(
                    'Not enough permissions for component %s' % component
                )
            elif components_res.status_code >= 400 and \
                    components_res.status_code < 500:
                raise DciUnexpectedErrorException(
                    'Received unexpected error while retrieving %s' % component
                )
            else:
                raise DciServerErrorException('Server error')

        return components

    def do_create(self, context):
        topic_res = dci_topic.list(context, where='name:' + self.topic)

        if topic_res.status_code == 200:
            topics = topic_res.json()['topics']
            if len(topics) == 0:
                raise DciResourceNotFoundException(
                    'Not found or not enough permissions for topic %s' %
                    self.topic
                )

            topic_id = topics[0]['id']

            if self.components_by_query:
                self.components.extend(self.find_components(context, topic_id))

            res = dci_job.create(
                context, topic_id,
                comment=self.comment,
                components=self.components,
                configuration=self.configuration,
                name=self.name,
                team_id=self.team_id,
                url=self.url,
                previous_job_id=self.previous_job_id,
            )
            if res.status_code == 201:
                return dci_job.get(
                    context, context.last_job_id,
                    embed='topic,remoteci,components')
            else:
                self.raise_error(res)

        else:
            self.raise_error(topic_res)

    def do_status(self, context):
        res = dci_jobstate.create(context,
                                  status=self.status,
                                  comment=self.comment,
                                  job_id=self.id)
        if res.status_code != 201:
            self.raise_error(res)

        return res


def main():

    resource_argument_spec = dict(
        state=dict(
            default='present',
            choices=['present', 'absent'], type='str'),
        id=dict(type='str'),
        topic=dict(required=False, type='str'),
        comment=dict(type='str'),
        status=dict(type='str'),
        tags=dict(type='list'),
        upgrade=dict(type='bool'),
        update=dict(type='bool'),
        components=dict(type='list'),
        components_by_query=dict(type='list'),
        team_id=dict(type='str'),
        url=dict(type='str'),
        name=dict(type='str'),
        configuration=dict(type='str'),
        previous_job_id=dict(type='str'),
        embed=dict(type='str'),
        where=dict(type='str'),
        get=dict(type='str'),
    )
    resource_argument_spec.update(authentication_argument_spec())

    module = AnsibleModule(
        argument_spec=resource_argument_spec,
        required_if=[['state', 'absent', ['id']]]
    )

    if not dciclient_found:
        module.fail_json(msg='The python-dciclient module is required')

    context = build_dci_context(module)
    action_name = get_standard_action(module.params)

    if action_name == 'update':
        # for readability
        if module.params['update']:
            action_name = 'job_update'
        if module.params['upgrade']:
            action_name = 'upgrade'
        if module.params['tags']:
            action_name = 'set_tags'

    elif action_name == 'create':
        if not module.params['components'] and \
           not module.params['components_by_query']:
            action_name = 'schedule'

    job = DciJob(module.params)
    action_func = getattr(job, 'do_%s' % action_name)

    http_response = run_action_func(action_func, context, module)
    result = parse_http_response(http_response, dci_job, context, module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
