# dci_job_component module

DCI module to interact with the components of a job

## Options

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| component_id | True |  | the component id |
| dci_cs_url | False |  | DCI Control Server URL |
| dci_login | False |  | User's DCI login |
| dci_password | False |  | User's DCI password |
| job_id | True |  | the job id |
| state | False | present | Desired state of the resource |

## Examples

```yaml
- name: Associate a component to a job
  dci_job_component:
    job_id: {{ job_id }}
    component_id: {{ component_id }}

- name: Remove a component from a job
  dci_job_component:
    job_id: {{ job_id }}
    component_id: {{ component_id }}
    state: absent
```
