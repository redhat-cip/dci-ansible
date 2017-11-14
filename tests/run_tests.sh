#!/bin/sh

set -eux

modules='dci_user dci_team dci_topic dci_component dci_feeder dci_product dci_role'

source ./admin.sh
for module in $modules; do
    ansible-playbook unit-tests/$module/playbook.yml -vvv
    dcictl purge
done
