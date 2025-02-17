# dci_topic module

DCI module to manage the topic resources

## Options

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| active | False |  | Wether of not the resource should be active |
| component_types | False |  | Topic component_types |
| data | False |  | Data field of a topic |
| dci_cs_url | False |  | DCI Control Server URL |
| dci_login | False |  | User's DCI login |
| dci_password | False |  | User's DCI password |
| embed | False |  | ['List of field to embed within the retrieved resource'] |
| export_control | False |  | wether or not the topic is export_control restricted |
| id | False |  | ID of the topic to interact with |
| label | False |  | Topic label |
| name | False |  | Topic name |
| next_topic_id | False |  | The next topic id to upgrade to. |
| product_id | False |  | The product the topic belongs to |
| query | False |  | query language |
| state | False |  | Desired state of the resource |
| where | False |  | Specific criterias for search |

## Examples

```yaml
- name: Create a new topic
  dci_topic:
    name: 'Soft21'


- name: Create a new topic
  dci_topic:
    name: 'Soft42'
    label: 'The latest version of Soft with the 42 feature'
    product_id: XXX


- name: Get topic information
  dci_topic:
    id: XXXXX


- name: Update topic informations
  dci_topic:
    id: XXXX
    name: 'Soft42-Final'


- name: Delete a topic
  dci_topic:
    state: absent
    id: XXXXX


- name: Search a topic by name
  dci_topic:
    state: search
    name: YYYY
```
