Name:		dci-ansible
Version:	0.0.VERS
Release:	1%{?dist}
Summary:	DCI Ansible modules and callback
License:	ASL 2.0
URL:		https://github.com/Spredzy/dci-ansible
Source0:	dci-ansible-%{version}.tar.gz

BuildArch:	noarch
Requires:	python-dciclient

%description
A set of Ansible modules and callback to interact with the DCI
control server


%prep
%setup -q


%build

%install
mkdir -p %{buildroot}/usr/share/dci
cp -r modules %{buildroot}/usr/share/dci/
cp -r callback %{buildroot}/usr/share/dci/
chmod 755 %{buildroot}/usr/share/dci
chmod 755 %{buildroot}/usr/share/dci/modules
chmod 755 %{buildroot}/usr/share/dci/callback


%files
%doc README.md
%license LICENSE
%{_datadir}/dci


%changelog
* Thu Jan 19 2017 Yanis Guenane <yguenane@redhat.com> - 0.0.1-1
- Initial release
