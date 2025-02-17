# dci_component module

DCI module to manage the component resources

## Options

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| active | False |  | Wether of not the resource should be active |
| dci_cs_url | False |  | DCI Control Server URL |
| dci_login | False |  | User's DCI login |
| dci_password | False |  | User's DCI password |
| dest | True |  | Path where to drop the retrieved component |
| query | False |  | query language |
| state | False | present | Desired state of the resource |

## Examples

```yaml
- name: Download a component
  dci_component:
    id: {{ component_id }}
    dest: /srv/dci/components/{{ component_id }}

- name: Retrieve component informations
  dci_component:
    id: {{ component_id }}

- name: Remove component
  dci_component:
    state: absent
    id: {{ component_id }}

- name: list components and sort result
  dci_component:
    state: search
    topic_id: '{{ topic_id }}'
    sort: name
    register: list_components
```
