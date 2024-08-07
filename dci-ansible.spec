Name:		dci-ansible
Version:	0.8.0
Release:	1.VERS%{?dist}
Summary:	DCI Ansible modules and callback
License:	ASL 2.0
URL:		https://github.com/redhat-cip/dci-ansible
Source0:	dci-ansible-%{version}.tar.gz

BuildArch:   noarch
Requires:    python3-dciclient
Requires:    python3-dciauth

Requires:    (ansible-core or (ansible < 2.10.0 with ansible >= 2.9.10))
Conflicts:    dci-openshift-agent < 0.5.6
Conflicts:    dci-openshift-app-agent < 0.5.5

%description
A set of Ansible modules and callback to interact with the DCI
control server


%prep
%setup -qc


%build

%install
mkdir -p %{buildroot}%{_datadir}/dci
cp -r modules module_utils callback action_plugins filter_plugins %{buildroot}%{_datadir}/dci/
chmod 755 %{buildroot}%{_datadir}/dci
chmod 755 %{buildroot}%{_datadir}/dci/*

%files
%doc README.md
%license LICENSE
%license COPYING
%{_datadir}/dci


%changelog
* Thu Jul 18 2024 Frederic Lepied <flepied@redhat.com> 0.8.0-1
- provide the dcijunit callback plugin

* Tue Jul 16 2024 Guillaume Vincent <gvincent@redhat.com> - 0.7.1-1
- Add dciauth requirement

* Mon Jun 24 2024 Tony Garcia <tonyg@redhat.com> - 0.7.0-1
- Use ansible-core or ansible depending on its versions

* Wed Sep 20 2023 Guillaume Vincent <gvincent@redhat.com> - 0.6.0-1
- Remove team_ids on topic module

* Mon Jul 17 2023 François Charlier <fcharlie@redhat.com> - 0.5.0-1
- deprecate dci_keys module

* Sun Jun  4 2023 Frederic Lepied <flepied@redhat.com> - 0.4.0-1
- requires dciclient >= 3.2.0 for job.delete_component api call

* Fri Apr 28 2023 Frederic Lepied <flepied@redhat.com> - 0.3.1-1
- Requires dciclient >= 3.1.0 for the new component fields
- Conflicts with the old versions of the OCP agents

* Thu Sep  8 2022 Tony Garcia <tonyg@redhat.com> - 0.3.0-1
- Add filter plugins

* Tue Dec 21 2021 Tony Garcia <togarcia@redhat.com> - 0.2.0-1
- Use get_or_create method from python-dciclient

* Tue Nov 10 2020 Yassine Lamgarchal <ylamgarc@redhat.com> - 0.1.0-1
- Adding action_plugins directory

* Thu Jun 04 2020 Bill Peck <bpeck@rehdat.com> - 0.0.1-3
- Rebuild for RHEL-8

* Wed Jul 05 2017 Yassine Lamgarchale <yassine.lamgarchal@redhat.com> - 0.0.1-2
- Adding module_utils feature starting from ansible version 2.3

* Thu Jan 19 2017 Yanis Guenane <yguenane@redhat.com> - 0.0.1-1
- Initial release
