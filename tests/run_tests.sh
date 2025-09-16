#!/usr/bin/env bash

set -eux

BASEDIR="$(cd "$(dirname "$0")"||exit 1; pwd)"

export DCI_LOGIN="${DCI_LOGIN:-admin}"
export DCI_PASSWORD="${DCI_PASSWORD:-admin}"
export DCI_CS_URL="${DCI_CS_URL:-http://localhost}"

function create_venv(){
    rm -rf venv
    python3 -m venv venv
    source venv/bin/activate
    python3 -m pip install --upgrade pip
    python3 --version
    pip --version
    pip install ansible
    pip install dciclient
}

function activate_venv(){
    source venv/bin/activate
}

function debug(){
    ansible --version
    ansible-playbook --version
}

function run_modules_tests() {
    modules='dci_user dci_team dci_topic dci_component dci_feeder dci_product dci_job'

    for module in $modules; do
        ansible-playbook modules/$module/playbook.yml -v
    done
}

function run_filter_plugins_tests() {
    plugins='version_sort cmdline_to_json'

    for plugin in $plugins; do
        ansible-playbook filter_plugins/${plugin}/playbook.yml -v
    done
}

function run_callbacks_tests() {
    ansible-playbook callbacks/dci.yml -v

    rm -f junit-playbook.xml
    env JUNIT_OUTPUT_DIR=$PWD JUNIT_TEST_CASE_REGEX='(test|validate)_ ' ansible-playbook callbacks/junit-playbook.yml -vvvv
    test -r junit-playbook.xml
    grep -C 5 "All assertions passed" junit-playbook.xml
}

cd $BASEDIR
create_venv
activate_venv
debug

if [[ ! -z ${1+x} ]]; then
    if [[ "$1" == "modules" ]]; then
        run_modules_tests
    elif [[ "$1" == "plugins" ]]; then
        run_filter_plugins_tests
    elif [[ "$1" == "callbacks" ]]; then
        run_callbacks_tests
    else
        echo "Usage: run_test.sh [modules|plugins|callbacks]"
    fi
else
  run_modules_tests
  run_filter_plugins_tests
  run_callbacks_tests
fi
