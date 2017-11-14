#!/bin/sh

set -eux

export DCI_LOGIN='admin'
export DCI_PASSWORD='admin'
export DCI_CS_URL='http://127.0.0.1:5000'

modules='dci_user dci_team dci_topic dci_component dci_feeder dci_product dci_role'

for module in $modules; do
    ansible-playbook unit-tests/$module/playbook.yml -vvv
    dcictl purge
done
