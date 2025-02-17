# dci_user module

DCI module to manage the user resources

## Options

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| active | False |  | Wether of not the resource should be active |
| dci_cs_url | False |  | DCI Control Server URL |
| dci_login | False |  | User's DCI login |
| dci_password | False |  | User's DCI password |
| email | False |  | User email |
| embed | False |  | ['List of field to embed within the retrieved resource'] |
| fullname | False |  | User fullname |
| id | False |  | ID of the user to interact with |
| name | False |  | User name |
| password | False |  | User password |
| query | False |  | query language |
| state | False |  | Desired state of the resource |
| where | False |  | Specific criterias for search |

## Examples

```yaml
- name: Create a new user
  dci_user:
    name: jdoe
    fullname: John Doe
    email: jdoe@example.tld
    password: 'APassw0rd!'


- name: Get user information
  dci_user:
    id: XXXXX


- name: Update user informations
  dci_user:
    id: XXXX
    email: jdoe@newcompany.org


- name: Delete a user
  dci_user:
    state: absent
    id: XXXXX
```
