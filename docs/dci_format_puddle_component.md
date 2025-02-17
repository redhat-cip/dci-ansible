# dci_format_puddle_component module

DCI module to manage the dci puddle component

## Options

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| state | False |  | Desired state of the resource |
| url | True |  | URL to parse |

## Examples

```yaml
- name: Format puddle component
  dci_format_puddle_component:
    url: 'https://url/mypuddle.repo'
```
