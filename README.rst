=========
Yaybu.app
=========

This repository contains a bash script for setting up a build environment and a
py2app script for building and packaging 'Yaybu.app' as a ``.dmg``.

The primary motivation of this packaging is to support automatic updates and
easy use of Yaybu from OSX terminals.

Features include:

Get shells from the GUI
    If you start it from the dock you will be presented with an Open dialog to
    choose a ``Yaybufile``. Alternatively you can drop a ``Yaybufile`` onto the
    dock icon.
Automatic updates
    Using Sparkle.framework the bundle will update itself automatically. The
    build process emits zip files and DSA signatures so that Sparkle can verify
    the authenticity of the update.
Command line support
    The package ships with a command line wrapper which it will offer to
    symlink into ``/usr/local/bin``. It can then be used as a command line
    tool, but receive updates via Sparkle.framework implicitly.
GPG support out of box
    Enough GPG bundled to support decryption of protected secrets and assets
    out of the box.

