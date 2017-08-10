How to build an new fow version into a deb file (Debian package) 
================================================================
Set the version nr and the build nr in lib/fow/plumb.py.VERSION.
Set the version nr in make_dist for the mv command for the destination file.
Set Version in file ../dist/debian/DEBIAN/control
Call make_man, if man pages in man_source was touched.
Call make_dist. The final deb file will be found in ../dist.

How to install fow on the local computer
========================================
A new version must be build, see above.
Set the version nr in file install for the deb file name, named in ../dest. 
Call install.
