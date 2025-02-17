# Ansible modules to interact with Distributed-CI (DCI)

A set of [Ansible](https://www.ansible.com) modules and callbacks to ease the interaction with the [Distributed-CI](https://docs.distributed-ci.io) platform.

## Get Started

### Installation

There are two ways to install [dci-ansible](https://github.com/redhat-cip/dci-ansible), either via rpm packages or directly via Github source code.

Unless you are looking to contribute to this project, we recommend you use the rpm packages.

#### Packages

Officially supported platforms:

- CentOS (latest version)
- RHEL (latest version)
- Fedora (latest version)

If you're looking to install those modules on a different Operating System, please install it from [source]()

First, you need to install the official Distributed-CI package repository

```shellsession
# dnf install https://packages.distributed-ci.io/dci-release.el8.noarch.rpm
```

Then, install the package

```shellsession
# dnf install dci-ansible
```

#### Sources

Define a folder where you want to extract the code and clone the repository.

```shellsession
# cd /usr/share/dci && git clone https://github.com/redhat-cip/dci-ansible.git
```

### How to use it

#### Authentication

The modules provided by this project cover all the endpoints Distributed-CI offers.

This means that this project allows one to interact with Distributed-CI for various use-cases:

- To act as an agent: Scheduling jobs, uploading logs, and test results.
- To act as a feeder: Creating Topics, Components and uploading Files.
- To complete administrative tasks: Creating Teams, Users, RemoteCIs.
- And more...

For any of the modules made available to work with the Distributed-CI API, one needs to authenticate itself first.

Each module relies on three environment variables to authenticate the author of the query:

- `DCI_CLIENT_ID`: The ID of the resource that wishes to authenticate (RemoteCI, User, Feeder)
- `DCI_API_SECRET`: The API Secret of the resource that wishes to authenticate
- `DCI_CS_URL`: The API address (default to https://api.distributed-ci.io)

The recommended way is to retrieve the `dcirc.sh` file directly from https://www.distributed-ci.io or create it yourself in the same folder as your playbook:

```shellsession
$ cat > dcirc.sh <<EOF
export DCI_CLIENT_ID=<resource_id>
export DCI_API_SECRET=<resource_api_secret>
export DCI_CS_URL=https://api.distributed-ci.io
EOF
```

And then run the playbook the following way:

```shellsession
$ source dcirc.sh && ansible-playbook playbook.yml
```

By now my `dci-test/` folder looks like this:
```shellsession
$ ls -l dci-test/
total 837
-rw-rw-r--. 1 jdoe jdoe 614 Oct 19 14:51 dcirc.sh
-rw-rw-r--. 1 jdoe jdoe 223 Oct 19 14:51 playbook.yml
```

#### File organization

Since the modules of dci-ansible are not part of Ansible, one needs to tell Ansible where to look for the extra modules and callbacks this project is providing.
This is done via the [Ansible configuration file](http://docs.ansible.com/ansible/latest/intro_configuration.html).

The Distributed-CI team recommends that you place an `ansible.cfg` file in the same folder as your playbook with the following content:

```ini
[defaults]
library            = /usr/share/dci/modules/
module_utils       = /usr/share/dci/module_utils/
callback_whitelist = dci,dcijunit
callback_plugins   = /usr/share/dci/callback/
```

**Note**: If you installed the modules from source, please update the paths accordingly.

By now, my `dci-test/` folder looks like this:

```shellsession
$ ls -l dci-test/
total 1014
-rw-rw-r--. 1 jdoe jdoe 177 Oct 19 14:51 ansible.cfg
-rw-rw-r--. 1 jdoe jdoe 614 Oct 19 14:51 dcirc.sh
-rw-rw-r--. 1 jdoe jdoe 223 Oct 19 14:51 playbook.yml
```

### Modules

The following modules are available to use with Distributed-CI in your playbooks:

  * [dci_component: module to interact with the components endpoint of DCI](docs/dci_component.md)
  * [dci_feeder: module to interact with the feeders endpoint of DCI](docs/dci_feeder.md)
  * [dci_file: module to interact with the files endpoint of DCI](docs/dci_file.md)
  * [dci_format_puddle_component: module to format the puddle output](docs/dci_format_puddle_component.md)
  * [dci_job: An ansible module to interact with the /jobs endpoint of DCI](docs/dci_job.md)
  * [dci_job_component: module to interact with the components of a job](docs/dci_job_component.md)
  * [dci_oval_to_junit: module to convert oval file format to junit](docs/dci_oval_to_junit.md)
  * [dci_product: module to interact with the products endpoint of DCI](docs/dci_product.md)
  * [dci_remoteci: module to interact with the remotecis endpoint of DCI](docs/dci_remoteci.md)
  * [dci_team: module to interact with the teams endpoint of DCI](docs/dci_team.md)
  * [dci_topic: module to interact with the topics endpoint of DCI](docs/dci_topic.md)
  * [dci_user: module to interact with the users endpoint of DCI](docs/dci_user.md)

### Samples

The following examples will highlight how to interact with a resource. The remoteci resource will be taken as an example. The same pattern applies to all Distributed-CI resources,

- Create a RemoteCI

```yaml
---
- hosts: localhost
  tasks:
    - name: Create a RemoteCI
      dci_remoteci:
        name: MyRemoteCI
```

- List all RemoteCI

```yaml
---
- hosts: localhost
  tasks:
    - name: List all RemoteCIs
      dci_remoteci:
```

- Update a RemoteCI

```yaml
---
- hosts: localhost
  tasks:
    - name: Update a RemoteCIs
      dci_remoteci:
        id: <remoteciid>
        name: NewName
```

- Delete a RemoteCI

```yaml
---
- hosts: localhost
  tasks:
    - name: Delete a RemoteCIs
      dci_remoteci:
        id: <remoteciid>
        state: absent
```

Examples of real-life scenarios are available in the [samples/](samples/) directory.

## Contributing

We'd love to get contributions from you!

If you'd like to report a bug or suggest new ideas, you can do it [here](https://github.com/redhat-cip/dci-ansible/issues/new).

If you'd like to contribute code back to dci-ansible, our code is hosted on [Software Factory](https://softwarefactory-project.io/sf/welcome.html) and then mirrored on GitHub.
[Software Factory](https://softwarefactory-project.io/sf/welcome.html) is Gerrit-based. Please contact us if you feel uncomfortable with the workflow or have any questions.

### Running tests

Before running tests, you must familiarize yourself with the [dci-dev-env](https://github.com/redhat-cip/dci-dev-env) project.

[dci-dev-env](https://github.com/redhat-cip/dci-dev-env) is a Docker-based environment that will deploy a Distributed-CI Control Server API, the UI, and more.
Once deployed locally, you can run the test suite against this deployment.

To run the test, ensure the API is running by running `docker ps` and then simply run `./run_tests.sh` in the [tests/](tests/) folder

### Generating modules doc

If you change or add any documentation for modules, use this command to generate the Markdown documents out of the `DOCUMENTATION` and `EXAMPLES` variables from the modules:

```shellsession
$ make clean doc
```

## License

Apache License, Version 2.0 (see [LICENSE](LICENSE) file)

## Contact

Email: Distributed-CI Team <distributed-ci@redhat.com>
