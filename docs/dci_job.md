# dci_job module

DCI module to manage the job resources

## Options

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| comment | False |  | Comment attached to the job |
| components | False |  | list of ID to associated to the new job |
| configuration | False |  | configuration name of the job |
| dci_cs_url | False |  | DCI Control Server URL |
| dci_login | False |  | User's DCI login |
| dci_password | False |  | User's DCI password |
| embed | False |  | ['List of field to embed within the retrieved resource'] |
| id | False |  | ID of the job |
| key | False |  | Key to attach to the job. Required if value is set. |
| name | False |  | name of the job |
| pipeline_id | False |  | pipeline id of the new job |
| previous_job_id | False |  | previous job |
| query | False |  | query language |
| state | False | present | Desired state of the resource |
| status | False |  | Status the job should be entitled |
| status_reason | False |  | explanation of the status |
| tags | False |  | Tags attached to the job |
| team_id | False |  | team of the new job |
| topic | False |  | Topic for which the job will be schedule |
| update | False |  | Schedule an update job |
| upgrade | False |  | Schedule an upgrade job |
| url | False |  | URL attached to the job |
| value | False |  | Floating point value to attach to the job. Required if key is set. |
| where | False |  | Specific criterias for search |

## Examples

```yaml
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

- name: Set a key/value pair on a job
  dci_job:
    id: '{{ job_id }}'
    key: 'answer'
    value: 42.0
```
