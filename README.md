pylaunch
--------

A Budgie desktop Applet

This is a straight copy/paste/port of my other desktop app quickwin
https://github.com/lachlan-00/quickwin

Usage
-----

 * This is a launcher that requires executable files. (shell scripts, binary files, etc)
 * I do intend to support desktop files as well but haven't gotten there yet.
 * Extra options like custom icons will be re-added

By default I set the base path to /usr/bin to provide guaranteed data on launch.
Set your desired path (e.g. /home/user/bin/) and relaunch the window.


Install
-------

# install build tools if you haven't already
sudo eopkg install -c system.devel
sudo eopkg install budgie-desktop-devel

# prepare the build
meson builddir --prefix=/usr

# build
cd builddir && sudo ninja install && cd ../

# to rebuild just remove the directory
rm -rf builddir/ && meson builddir --prefix=/usr && cd builddir && sudo ninja install && cd ../

www
---
https://github.com/lachlan-00/budgie-quicklaunch


