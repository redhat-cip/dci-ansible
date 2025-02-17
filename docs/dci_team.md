# dci_team module

DCI module to manage the team resources

## Options

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| active | False |  | Wether of not the resource should be active |
| country | False |  | Team country |
| dci_cs_url | False |  | DCI Control Server URL |
| dci_login | False |  | User's DCI login |
| dci_password | False |  | User's DCI password |
| embed | False |  | ['List of field to embed within the retrieved resource'] |
| has_pre_release_access | False |  | Wether of not the team should have access to pre release content |
| id | False |  | ID of the team to interact with |
| name | False |  | Teams name |
| query | False |  | query language |
| state | False |  | Desired state of the resource |
| where | False |  | Specific criterias for search |

## Examples

```yaml
- name: Create a new team
  dci_team:
    name: 'A-Team'
    country: 'USA'


- name: Create a new team
  dci_team:
    name: 'A-Team'
    country: 'USA'
    email: 'mrt@a-team.com'
    notification: True


- name: Get team information
  dci_team:
    id: XXXXX


- name: Update team informations
  dci_team:
    id: XXXX
    name: 'B-Team'


- name: Delete a team
  dci_team:
    state: absent
    id: XXXXX
```
