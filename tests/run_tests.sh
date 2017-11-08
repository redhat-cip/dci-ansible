#!/bin/sh

set -eux

function clean_environment() {
    unset DCI_LOGIN
    unset DCI_PASSWORD
    unset DCI_API_SECRET
    unset DCI_CLIENT_ID
}


# --- Starting unit-tests

# modules='dci_user dci_team dci_topic dci_component dci_feeder dci_product dci_role'

# source ./admin.sh
# for module in $modules; do
#     ansible-playbook unit-tests/$module/playbook.yml -vvv
#     dcictl purge
# done
# clean_environment


# --- Starting scenario-tests

source ./admin.sh
ansible-playbook scenario-tests/setup_env.yml -vvv
clean_environment

source ./feeder.sh
ansible-playbook scenario-tests/feeder.yml -vvv
clean_environment

source ./remoteci.sh
ansible-playbook scenario-tests/remoteci.yml -vvv
clean_environment

rm -f feeder.sh remoteci.sh content.download
