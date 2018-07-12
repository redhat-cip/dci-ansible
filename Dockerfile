FROM centos:7

LABEL name="DCI ANSIBLE" version="0.0.2"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

ENV LANG en_US.UTF-8

RUN yum -y install epel-release && \
    yum -y install git \
    python python2-devel python2-pip python2-setuptools && \
    yum clean all

RUN pip install -U pip
# python-tox is broken, install tox with pip instead
RUN pip install -U tox

WORKDIR /opt/dci-ansible
ADD . /opt/dci-ansible/

ENV PYTHONPATH /opt/dci-ansible

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["tail", "-f", "/dev/null"]
