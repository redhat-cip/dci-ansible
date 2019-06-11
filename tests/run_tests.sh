#!/usr/bin/env bash

set -eux

function clean_environment() {
    unset DCI_LOGIN
    unset DCI_PASSWORD
    unset DCI_API_SECRET
    unset DCI_CLIENT_ID
}

function clean_db() {
    DB_HOST="${DB_HOST:-localhost}"
    echo "
      truncate products cascade;
      delete from teams where name <> 'admin';" | \
        PGPASSWORD=dci psql -h ${DB_HOST} -U dci -d dci
}


# --- Starting unit-tests

function run_unit_tests() {
    modules='dci_user dci_team dci_topic dci_component dci_feeder dci_product dci_job dci_keys'

    source ./admin.sh
    for module in $modules; do
        ansible-playbook unit-tests/$module/playbook.yml -vvv
        clean_db
    done
    clean_environment
}


# --- Starting scenario-tests

function run_functional_tests() {

    environments='openstack rhel'
    for environment in $environments; do
        source ./admin.sh
        ansible-playbook -vvv "scenario-tests/${environment}/setup_env.yml"
        clean_environment

        source ./feeder.sh
        ansible-playbook "scenario-tests/${environment}/feeder.yml" -vvv
        clean_environment

        source ./remoteci.sh
        ansible-playbook "scenario-tests/${environment}/remoteci.yml" -vvv
        clean_environment

        rm -f feeder.sh remoteci.sh content.download
    done
}

if [[ ! -z ${1+x} ]]; then
    if [[ "$1" == "unit" ]]; then
        run_unit_tests
    elif [[ "$1" == "functional" ]]; then
        run_functional_tests
    else
        echo "Usage: run_test.sh [unit|functional]"
    fi
else
  run_unit_tests
  run_functional_tests
fi
