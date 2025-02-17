# dci_product module

DCI module to manage the remoteci product resources

## Options

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| active | False |  | Wether of not the resource should be active |
| dci_cs_url | False |  | DCI Control Server URL |
| dci_login | False |  | User's DCI login |
| dci_password | False |  | User's DCI password |
| description | False |  | Description of a product |
| id | False |  | ID of the team to interact with |
| label | False |  | Label of a product |
| name | False |  | Teams name |
| query | False |  | query language |
| state | False |  | Desired state of the resource |
| team_ids | False |  | List of Teams to detach from this topic |
| where | False |  | Specific criterias for search |

## Examples

```yaml
- name: Create a new product
  dci_product:
    name: 'product-A'


- name: Create a new product
  dci_product:
    name: 'product-A'
    label: PRODUCTA-PKI
    description: This is the description of product A


- name: Get product information
  dci_product:
    id: XXXXX


- name: Update product informations
  dci_product:
    id: XXXX
    name: 'newproduct-A'


- name: Delete a product
  dci_product:
    state: absent
    id: XXXXX
```
