#
# spec file for package fow 
#
# Copyright (c) 2021 Christian Schulzendorff 
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

Name: 		fow
Version: 	1.8.0
Release:        0 
Summary:        Script for file based photographers workflow 
Group: 		TecAdmin
License:        MIT
URL:		https://github.com/chs8691/fow
Source0:        fow.tar.gz

%description
fow

%prep
%setup -q

%build

%install
install -m 0755 -d $RPM_BUILD_ROOT/usr/lib/fow
install -m 0755 lib/* $RPM_BUILD_ROOT/usr/lib/fow
install -m 0755 -d $RPM_BUILD_ROOT/usr/bin
install -m 0755 bin/* $RPM_BUILD_ROOT/usr/bin/
install -m 0755 -d $RPM_BUILD_ROOT/usr/share/man/man1
install -m 0755 man/* $RPM_BUILD_ROOT/usr/share/man/man1

%files
/usr/lib
/usr/bin/fow
/usr/share/man/man1

%changelog
* Fri Apr 16 2021 Christian Schulzendorff 1.8.0
  - Initial rpm release
