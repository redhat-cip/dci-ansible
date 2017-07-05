Name:		dci-ansible
Version:	0.0.VERS
Release:	2%{?dist}
Summary:	DCI Ansible modules and callback
License:	ASL 2.0
URL:		https://github.com/redhat-cip/dci-ansible
Source0:	dci-ansible-%{version}.tar.gz

BuildArch:	noarch
Requires:	ansible
Requires:	python2-dciclient

%description
A set of Ansible modules and callback to interact with the DCI
control server


%prep
%setup -qc


%build

%install
mkdir -p %{buildroot}%{_datadir}/dci
cp -r modules %{buildroot}%{_datadir}/dci/
cp -r module_utils %{buildroot}%{_datadir}/dci/
cp -r callback %{buildroot}%{_datadir}/dci/
chmod 755 %{buildroot}%{_datadir}/dci
chmod 755 %{buildroot}%{_datadir}/dci/modules
chmod 755 %{buildroot}%{_datadir}/dci/module_utils
chmod 755 %{buildroot}%{_datadir}/dci/callback


%files
%doc README.md
%license LICENSE
%{_datadir}/dci


%changelog
* Wed Jul 05 2017 Yassine Lamgarchale <yassine.lamgarchal@redhat.com> - 0.0.2-1
- Adding module_utils feature starting from ansible version 2.3

* Thu Jan 19 2017 Yanis Guenane <yguenane@redhat.com> - 0.0.1-1
- Initial release
