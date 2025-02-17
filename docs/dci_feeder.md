# dci_feeder module

DCI module to manage the feeder resources

## Options

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| active | False |  | Wether of not the resource should be active |
| data | False |  | Data field of a feeder |
| dci_cs_url | False |  | DCI Control Server URL |
| dci_login | False |  | User's DCI login |
| dci_password | False |  | User's DCI password |
| embed | False |  | ['List of field to embed within the retrieved resource'] |
| id | False |  | ID of the team to interact with |
| name | False |  | Teams name |
| query | False |  | query language |
| state | False |  | Desired state of the resource |
| team_id | False |  | ID of the team the feeder belongs to |
| where | False |  | Specific criterias for search |

## Examples

```yaml
- name: Create a new feeder
  dci_feeder:
    name: 'A-Feeder'
    team_id: XXX


- name: Create a new feeder
  dci_feeder:
    name: 'A-Feeder'
    team_id: XXX
    data:
      key: value


- name: Get feeder information
  dci_feeder:
    id: XXXXX


- name: Update feeder informations
  dci_feeder:
    id: XXXX
    name: 'B-Feeder'


- name: Delete a feeder
  dci_feeder:
    state: absent
    id: XXXXX
```
