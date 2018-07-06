#!/bin/sh

sed -i 's#dciclient#-e ../python-dciclient#g' /opt/dci-ansible/test-requirements.txt

exec "$@"
