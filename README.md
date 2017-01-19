# dci-ansible

This project aims to provide the necessary Ansible actions and an Ansible callback
so a user can freely interact with DCI.

## Installation

1. Create the necessary folder.

```
#> mkdir /usr/share/dci/
```

2. Copy the modules and callback folders in the previously created folder.

```
#> git clone https://github.com/Spredzy/dci-ansible.git
#> cd dci-ansible
#> cp -r modules /usr/share/dci
#> cp -r callback /usr/share/dci
```

3. Create a folder where the ansible related items will be located, copy the ansible.cfg file and proceed as usual with your ansible stuff.

```
#> mkdir ~/dci_agent
#> cp ansible.cfg ~/dci_agent
```

**Note:** Some samples are available in the samples directory to get you started with.


## Usage

### dcirc.sh

In order to run your playbook with the DCI ansible modules and callback one needs to source a file to export ones credentials.

The file should look like:

```
export DCI_LOGIN=jdoe
export DCI_PASSWORD=p4ssw0rd!
export DCI_CS_URL=https://api.distributed-ci.io
```

`DCI_CS_URL` will default to 'https://api.distributed-ci.io' if not specified.


### dci_new_job

`dci_new_job` is an ansible module to schedule a new job with DCI. It will rely on the exported environment variable to authenticate and retrieve information from the DCI control server.

Its usage looks like:

```
- name: Schedule a new job
  dci_new_job:
    topic: RDO-Ocata
    remoteci: dci-env-ovb-1
  register: job_informations
```

This sample will schedule a new job for the remoteci `dci-env-ovb-1` and with the topic `RDO-Ocata`. The json result returned by the API will be available in the job_informations variable, to be used freely by the user.


### dci_component

`dci_component` is an ansible module to download a component from DCI. It will rely on the exported environment variable to authenticate and retrieve information from the DCI control server.

Its usage looks like:

```
- hosts: localhost
  vars:
    components: "{{ job_informations['components'] }}"
  tasks:
    - name: retrieve components
      dci_component:
        dest: '/srv/data/{{ item["id"] }}.tar'
        component_id: '{{ item["id"] }}'
      with_items: "{{ components }}"
```

This sample will download the components from the DCI control-server and write them to the `dest` path.

### dci_upload

`dci_upload` is an ansible module to attach a file to a job. It will rely on the exported environment variable to authenticate and retrieve information from the DCI control server.

Its usage looks like:

```
- hosts: localhost
  vars:
    job_id: "{{ job_informations['job_id'] }}"
  tasks:
    - name: attach files to job
      dci_upload:
        path: '{{ item.path }}'
        name: '{{ item.name }}'
        job_id: '{{ job_id }}'
      with_items:
        - {'name': 'SSHd Config', 'path': '/etc/ssh/sshd_config'}
        - {'name': 'My OpenStack Conf', 'path': '/etc/openstack/my.conf'}
```

This sample will attach the two files listed to this specific job.

### Basic sample

```
---
- hosts: localhost
  tasks:
    - name: Schedule a new job
      dci_new_job:
        topic: 'OSP8'
        remoteci: 'dci-env-ovb-1'
      register: job_informations

- hosts: localhost
  vars:
    dci_status: 'new'
  tasks:
    - name: echo 'New'
      shell: echo 'New'

- hosts: localhost
  vars:
    dci_status: 'pre-run'
    dci_comment: 'Pre-run state commands'
  tasks:
    - name: echo 'Pre-run'
      shell: echo 'pre-run'

- hosts: localhost
  vars:
    dci_status: 'running'
    dci_comment: 'Running state commands'
  tasks:
    - name: echo 'Running'
      shell: echo 'Running'

- hosts: localhost
  vars:
    dci_status: 'post-run'
    dci_comment: 'Post-run state commands'
  tasks:
    - name: echo 'Post-run'
      shell: echo 'Post-run'

- hosts: localhost
  vars:
    dci_status: 'success'
    dci_comment: 'Success state commands'
  tasks:
    - name: echo 'Success'
      shell: echo 'Succes'
```

This basic sample aims to highlight the overall workflow of a run.

  * Schedule a new job
  * Each new play create a new status
  * Each command output is send to the DCI CS attach with a new jobstate

The above exemple isn't really usefull to use with DCI as it does nothing related
to components.

### More complicated sample

```
---
- hosts: localhost
  tasks:
    - name: Schedule a new job
      dci_new_job:
        topic: 'OSP8'
        remoteci: 'dci-env-ovb-1'
      register: job_informations

- hosts: localhost
  vars:
    dci_status: 'new'
    dci_comment: 'Creating OSP 8 local mirrors and synchronizing them'
    components: "{{ job_informations['components'] }}"
    job_id: "{{ job_informations['job_id'] }}"
  tasks:
    - name: Ensure proper directories are created
      file:
        path: '/srv/data/{{ job_id }}'
        state: directory
      with_items: "{{ components }}"

    - name: Retrieve component
      dci_component:
        dest: '/srv/data/{{ item["id"] }}.tar'
        component_id: '{{ item["id"] }}'
      with_items: "{{ components }}"

    - name: Unarchive component
      unarchive:
        src: '/srv/data/{{ item["id"] }}.tar'
        dest: '/srv/data/{{ job_id }}'
        remote_src: True
      with_items: "{{ components }}"

- hosts: localhost
  vars:
    dci_status: 'pre-run'
    dci_comment: 'Pre-run state commands'
  tasks:
    - name: echo 'Pre-run'
      shell: echo 'pre-run'

[...]
```

This sample shows how one can actually retrieve the component and create the needed local repository to benefit
from the latest snapshots.

More example are available in `samples/`
