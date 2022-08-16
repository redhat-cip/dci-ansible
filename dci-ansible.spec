Name:		dci-ansible
Version:	0.2.0
Release:	1.VERS%{?dist}
Summary:	DCI Ansible modules and callback
License:	ASL 2.0
URL:		https://github.com/redhat-cip/dci-ansible
Source0:	dci-ansible-%{version}.tar.gz

BuildArch:	noarch
# Python2 for < Rhel 8
%if 0%{?rhel} && 0%{?rhel} < 8
Requires:    python2-dciclient >= 2.2.0
%else
Requires:    python3-dciclient >= 2.2.0
%endif

# Ansible 2.9 for Rhel 8 and older
%if 0%{?rhel} && 0%{?rhel} <= 8
Requires:	ansible >= 2.3, ansible < 2.10
Conflicts:	ansible-core
%else
Requires:	ansible
%endif

%description
A set of Ansible modules and callback to interact with the DCI
control server


%prep
%setup -qc


%build

%install
mkdir -p %{buildroot}%{_datadir}/dci
cp -r modules module_utils callback action_plugins %{buildroot}%{_datadir}/dci/
chmod 755 %{buildroot}%{_datadir}/dci
chmod 755 %{buildroot}%{_datadir}/dci/*

%files
%doc README.md
%license LICENSE
%{_datadir}/dci


%changelog
* Tue Dec 21 2021 Tony Garcia <togarcia@redhat.com> - 0.2.0-1.VERS
- Use get_or_create method from python-dciclient

* Tue Nov 10 2020 Yassine Lamgarchal <ylamgarc@redhat.com> - 0.1.0-1.VERS
- Adding action_plugins directory

* Thu Jun 04 2020 Bill Peck <bpeck@rehdat.com> - 0.0.1-3
- Rebuild for RHEL-8

* Wed Jul 05 2017 Yassine Lamgarchale <yassine.lamgarchal@redhat.com> - 0.0.1-2
- Adding module_utils feature starting from ansible version 2.3

* Thu Jan 19 2017 Yanis Guenane <yguenane@redhat.com> - 0.0.1-1
- Initial release
