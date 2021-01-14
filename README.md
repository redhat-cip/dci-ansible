# hi Ansible modules to interact with Distributed-CI (DCI)

![](https://img.shields.io/badge/ansible-2.4.0-green.svg?style=flat) ![](https://img.shields.io/badge/license-Apache2.0-blue.svg?style=flat) ![](https://img.shields.io/badge/python-2.7,3.5-green.svg?style=flat)

A set of [Ansible](https://www.ansible.com) modules and callbacks to ease the interaction with the [Distributed-CI](https://docs.distributed-ci.io) platform.

[Distributed-CI (DCI)](https://docs.distributed-ci.io) is a platform that allows a company to extend its CI coverage beyond its own walls; allowing them to let third-party partners contribute back their CI results into the platform.

DCI comes as a webservice that exposes its resources via a REST API. The [dci-ansible](https://github.com/redhat-cip/dci-ansible) project aims to map each of those REST resources to an Ansible module.

## Table of Contents

- [Get Started](#get-started)
  - [Installation](#installation)
    - [Packages](#packages)
    - [Sources](#sources)
  - [How to use it](#how-to-use-it)
    - [Authentication](#authentication)
    - [File Organization](#file-organization)
- [Contributing](#contributing)
  - [Running Tests](#running-tests)
- [License](#license)
- [Contact](#contact)

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

```
#> yum install https://packages.distributed-ci.io/dci-release.el7.noarch.rpm
```

Then, install the package

```
#> yum install dci-ansible
```

#### Sources

Define a folder where you would like to checkout the code and clone the repository.

```
#> cd /usr/share/dci && git clone https://github.com/redhat-cip/dci-ansible.git
```

### How to use it

#### Authentication

The modules provided by this project covers all the endpoints Distributed-CI offers.

This means that this project allows one to interact with Distributed-CI for various use-cases:

- To act as an agent: Scheduling jobs, uploading logs and tests results.
- To act as a feeder: Creating Topics, Components and uploading Files.
- To complete adminitrative tasks: Creating Teams, Users, RemoteCIs.
- And more...

For any of the modules made available to work with the Distributed-CI API, one needs to authenticate itself first.

Each module relies on 3 environment variables to authenticate the author of the query:

- `DCI_CLIENT_ID`: The ID of the resource that wish to authenticate (RemoteCI, User, Feeder)
- `DCI_API_SECRET`: The API Secret of the resource that wish to authenticate
- `DCI_CS_URL`: The API address (default to https://api.distributed-ci.io)

The recommended way is to retrieve the `dcirc.sh` file directly from the https://www.distributed-ci.io or create it yourself in the same folder as your playbook:

```
#> cat > dcirc.sh <<EOF
export DCI_CLIENT_ID=<resource_id>
export DCI_API_SECRET=<resource_api_secret>
export DCI_CS_URL=https://api.distributed-ci.io
EOF
```

And then run the playbook the following way:

```
#> source dcirc.sh && ansible-playbook playbook.yml
```

By now my `dci-test/` folder looks like this:

```
#> ls -l dci-test/
total 837
-rw-rw-r--. 1 jdoe jdoe 614 Oct 19 14:51 dcirc.sh
-rw-rw-r--. 1 jdoe jdoe 223 Oct 19 14:51 playbook.yml
```

#### File organization

Since the modules of dci-ansible are not part of Ansible, one needs to tell Ansible where to look for the extra modules and callbacks this project is providing.
This is done via the [Ansible configuratin file](http://docs.ansible.com/ansible/latest/intro_configuration.html).

The Distributed-CI team recommends that you place an `ansible.cfg` file in the same folder as your playbook with the following content:

```
[defaults]
library            = /usr/share/dci/modules/
module_utils       = /usr/share/dci/module_utils/
callback_whitelist = dci
callback_plugins   = /usr/share/dci/callback/
```

**Note**: If you installed the modules from source, please update the pathes accordingly.

By now my `dci-test/` folder looks like this:

```
#> ls -l dci-test/
total 1014
-rw-rw-r--. 1 jdoe jdoe 177 Oct 19 14:51 ansible.cfg
-rw-rw-r--. 1 jdoe jdoe 614 Oct 19 14:51 dcirc.sh
-rw-rw-r--. 1 jdoe jdoe 223 Oct 19 14:51 playbook.yml
```

### Samples

The following examples will highlight how to interact with a resource. The remoteci resource will be taken as an example. The same pattern applies to all Distributed-CI resources,

- Create a RemoteCI

```
---
- hosts: localhost
  tasks:
    - name: Create a RemoteCI
      dci_remoteci:
        name: MyRemoteCI
```

- List all RemoteCI

```
---
- hosts: localhost
  tasks:
    - name: List all RemoteCIs
      dci_remoteci:
```

- Update a RemoteCI

```
---
- hosts: localhost
  tasks:
    - name: Update a RemoteCIs
      dci_remoteci:
        id: <remoteciid>
        name: NewName
```

- Delete a RemoteCI

```
---
- hosts: localhost
  tasks:
    - name: Delete a RemoteCIs
      dci_remoteci:
        id: <remoteciid>
        state: absent
```

Real life scenarios examples are available in the [samples/](samples/) directory.

## Contributing

We'd love to get contributions from you!

If you'd like to report a bug or suggest new ideas you can do it [here](https://github.com/redhat-cip/dci-ansible/issues/new).

If you'd like to contribute code back to dci-ansible, our code is hosted on [Software Factory](https://softwarefactory-project.io/sf/welcome.html) and then mirrored on Github.
[Software Factory](https://softwarefactory-project.io/sf/welcome.html) is Gerrit based, if you don't feel comfortable with the workflow or have any question, feel free to ping someone on [IRC](#contact).

### Running tests

Before you can run test you need to get familiarized with the [dci-dev-env](https://github.com/redhat-cip/dci-dev-env) project.

[dci-dev-env](https://github.com/redhat-cip/dci-dev-env) is a Docker based environment that will deploy a Distributed-CI Control Server API, the UI and more.
Once deployed locally, you'll be able to run the test suite against this deployment.

To run the test, ensure the api is running by running `docker ps` and then simply run `./run_tests.sh` in the [tests/](tests/) folder

## License

Apache License, Version 2.0 (see [LICENSE](LICENSE) file)

## Contact

Email: Distributed-CI Team <distributed-ci@redhat.com>

IRC: #distributed-ci on Freenode
