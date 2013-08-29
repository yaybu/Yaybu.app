#!/bin/bash

set -v
set -e

YAY_COMMITISH=${YAY_COMMITISH:=master}
YAYBU_COMMITISH=${YAYBU_COMMITISH:=master}

PYTHON_VERSION=2.7.5
CACHE_DIR=$(pwd)/cache

if [ ! -d $CACHE_DIR ]; then
    mkdir -p $CACHE_DIR
fi

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

if [ ! -f python/python/Frameworks/Python.framework/Versions/2.7/bin/easy_install ]; then
    curl https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py | ./python/bin/python
fi

if [ ! -f python/python/Frameworks/Python.framework/Versions/2.7/bin/pip ]; then
    ./python/bin/python -m easy_install pip
fi


if [ -d src/yay ]; then
    YAY_REQUIREMENT="src/yay"
else
    YAY_REQUIREMENT=git+git://github.com/yaybu/yay.git@$YAY_COMMITISH#egg=yay
fi

if [ -d src/yaybu ]; then
    YAYBU_REQUIREMENT="src/yaybu"
else
    YAYBU_REQUIREMENT=git+git://github.com/yaybu/yaybu.git@$YAYBU_COMMITISH#egg=yaybu
fi


./python/bin/python -m pip install --upgrade \
    -r requirements.txt \
    $YAY_REQUIREMENT \
    $YAYBU_REQUIREMENT

# ./python/bin/python setup.py py2app

