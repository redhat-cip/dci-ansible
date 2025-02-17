# dci_file module

DCI module to manage the file resources

## Options

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| content | False |  | Contentn of the file to upload |
| dci_cs_url | False |  | DCI Control Server URL |
| dci_login | False |  | User's DCI login |
| dci_password | False |  | User's DCI password |
| embed | False |  | ['List of field to embed within the retrieved resource'] |
| job_id | False |  | ID of the job to attach the file to |
| jobstate_id | False |  | ID of the jobstate to attach the file to |
| mime | False | text/plain | mime-type of the document to upload |
| name | False |  | Name under which the file will be saved on the control-server |
| path | True |  | Path of the document to upload |
| query | False |  | query language |
| state | False |  | Desired state of the resource |

## Examples

```yaml
- name: Attach files to job
  dci_file:
    job_id: '{{ job_id }}'
    path: '{{ item.path }}'
    name: '{{ item.name }}'
  with_items:
    - {'name': 'SSHd config', 'path': '/etc/ssh/sshd_config'}
    - {'name': 'My OpenStack config', 'path': '/etc/myown.conf'}


- name: Get file information
  dci_file:
    id: XXXXX


- name: Attach content to a file to a job
  dci_file:
    job_id: '{{ job_id }}'
    content: 'This is the content of the file I want to create'
    name: 'My test file'


- name: Remove file
  dci_file:
    state: absent
    id: XXXXX


- name: Attach junit result
  dci_file:
    path: '{{ item }}'
    job_id: '{{ job_id }}'
    mime: 'application/junit'
  with_items:
    - '/tmp/result.xml'
```
