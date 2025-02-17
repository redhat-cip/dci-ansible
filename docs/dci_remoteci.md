# dci_remoteci module

DCI module to manage the remoteci resources

## Options

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| active | False |  | Wether of not the resource should be active |
| data | False |  | Data associated with the RemoteCI |
| dci_cs_url | False |  | DCI Control Server URL |
| dci_login | False |  | User's DCI login |
| dci_password | False |  | User's DCI password |
| embed | False |  | ['List of field to embed within the retrieved resource'] |
| id | False |  | ID of the remoteci to interact with |
| name | False |  | RemoteCI name |
| query | False |  | query language |
| state | False |  | Desired state of the resource |
| team_id | False |  | ID of the team the remoteci belongs to |
| where | False |  | Specific criterias for search |

## Examples

```yaml
- name: Create a new remoteci
  dci_remoteci:
    name: 'MyRemoteCI'
    team_id: XXXX


- name: Create a new team
  dci_remoteci:
    name: 'MyRemoteCI'
    team_id: XXXX
    data: >
      {"certification_id": "xfewafeqafewqfeqw"}


- name: Get remoteci information
  dci_remoteci:
    id: XXXXX


- name: Update remoteci informations
  dci_remoteci:
    id: XXXX
    name: New Name


- name: Delete a topic
  dci_remoteci:
    state: absent
    id: XXXXX
```
