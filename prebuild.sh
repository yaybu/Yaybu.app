#!/bin/bash

PYTHON_VERSION=2.7.5
CACHE_DIR=$(pwd)/cache

if [ ! -f $CACHE_DIR/Python-$PYTHON_VERSION.tar.bz2 ]; then
    curl http://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tar.bz2 > $CACHE_DIR/Python-$PYTHON_VERSION.tar.bz2
fi

if [ ! -d Python-$PYTHON_VERSION ]; then
   tar -xjf $CACHE_DIR/Python-$PYTHON_VERSION.tar.bz2
fi

if [ ! -f ./python/bin/python2 ]; then
    pushd Python-$PYTHON_VERSION

    PREFIX=$(pwd)/../python

    ./configure \
        --prefix=$PREFIX \
        --datarootdir=$PREFIX/share \
        --datadir=$PREFIX/share \
        --enable-framework=$PREFIX/python/Frameworks \
        --enable-ipv6 \
        --without-gcc \
        CC="$CCACHE clang -Qunused-arguments -fcolor-diagnostics" LDFLAGS="-lsqlite3"

    make
    make install PYTHONAPPSDIR=$PREFIX
    popd
fi

curl https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | ./python/bin/python
./python/bin/python -m easy_install py2app
./python/bin/python -m easy_install pyobjc-core
./python/bin/python -m easy_install pyobjc-framework-Cocoa
./python/bin/python -m easy_install pyobjc-framework-ScriptingBridge
./python/bin/python -m easy_install ply
./python/bin/python -m easy_install https://pypi.python.org/packages/source/p/pycrypto/pycrypto-2.6.tar.gz
./python/bin/python -m easy_install https://pypi.python.org/packages/source/g/greenlet/greenlet-0.4.1.zip
./python/bin/python -m easy_install https://github.com/isotoma/yay/zipball/master
./python/bin/python -m easy_install https://github.com/isotoma/yaybu/zipball/master

