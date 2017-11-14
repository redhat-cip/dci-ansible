#!/bin/sh

set -eux


function clean_environment() {
    unset DCI_LOGIN
    unset DCI_PASSWORD
    unset DCI_API_SECRET
    unset DCI_CLIENT_ID
    unset DCI_CS_URL
}


# --- Starting unit-tests

# source ./admin.sh
# modules='dci_user dci_team dci_topic dci_component dci_feeder dci_product dci_role'

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

exit 0

source ./remoteci.sh
ansible-playbook scenario-tests/remoteci.yml -vvv
clean_environment

source ./admin.sh
ansible-playbook scenario-ests/teardown_env.yml
clean_environment

rm -f feeder.sh remoteci.sh
