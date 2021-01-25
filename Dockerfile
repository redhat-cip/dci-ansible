FROM centos:7

LABEL name="DCI ANSIBLE" version="0.0.1"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

ENV LANG en_US.UTF-8

RUN yum -y install https://packages.distributed-ci.io/dci-release.el7.noarch.rpm epel-release && \
    yum -y install git \
    python python2-devel python2-pip python2-setuptools python36 \
    postgresql ansible python-dciclient && \
    yum clean all

RUN pip install -U "pip<21.0" && \
# python-tox is broken, install tox with pip instead
    pip install -U tox

WORKDIR /opt/dci-ansible
ADD . /opt/dci-ansible/

ENV PYTHONPATH /opt/dci-ansible

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["tail", "-f", "/dev/null"]
