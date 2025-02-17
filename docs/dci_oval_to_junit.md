# dci_oval_to_junit module

DCI module to convert oval file format to junit

## Options

| Parameter | Required | Default | Description |
| --------- | -------- | ------- | ----------- |
| junit_dest | True |  | Junit file destination path |
| oval_result_src | True |  | Oval file source path |

## Examples

```yaml
- name: Convert oval file to junit file
  dci_oval_to_junit:
    oval_result_src: {{ oval_src_path }}
    junit_dest: {{ junit_dest_path }}
```
