from ubuntu:trusty
maintainer Mixadx



# *************************************************************************
# Install Python 3.6
# *************************************************************************
# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
run apt-get update \
    && apt-get install -y wget \
    && apt-get install -y unzip \
    && apt-get install -y g++ \
    && apt-get install -y gcc \
    && apt-get install -y cmake \
    && apt-get install -y pkg-config

ENV LANG C.UTF-8

# runtime dependencies
run apt-get update && apt-get install -y --no-install-recommends \
		tcl \
		tk \
		openssl \
		libssl-dev \
	&& rm -rf /var/lib/apt/lists/*

ENV GPG_KEY 0D96DF4D4110E5C43FBFB17F2D347EA6AA65421D
ENV PYTHON_VERSION 3.6.5

# if this is called "PIP_VERSION", pip explodes with "ValueError: invalid truth value '<VERSION>'"
ENV PYTHON_PIP_VERSION 18.0

run set -ex \
	&& buildDeps=' \
		tcl-dev \
		tk-dev \
	' \
	&& apt-get update && apt-get install -y $buildDeps --no-install-recommends && rm -rf /var/lib/apt/lists/* \
	\
	&& wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz" \
	&& wget -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc" \
	&& export GNUPGHOME="$(mktemp -d)" \
	&& gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$GPG_KEY" \
	&& gpg --batch --verify python.tar.xz.asc python.tar.xz \
	&& rm -r "$GNUPGHOME" python.tar.xz.asc \
	&& mkdir -p /usr/src/python \
	&& tar -xJC /usr/src/python --strip-components=1 -f python.tar.xz \
	&& rm python.tar.xz \
	\
	&& cd /usr/src/python \
	&& ./configure \
		--enable-loadable-sqlite-extensions \
		--enable-shared \
	&& make -j$(nproc) \
	&& make install \
	&& ldconfig \
	\
# explicit path to "pip3" to ensure distribution-provided "pip3" cannot interfere
	&& if [ ! -e /usr/local/bin/pip3 ]; then : \
		&& wget -O /tmp/get-pip.py 'https://bootstrap.pypa.io/get-pip.py' \
		&& python3 /tmp/get-pip.py "pip==$PYTHON_PIP_VERSION" \
		&& rm /tmp/get-pip.py \
	; fi \
# we use "--force-reinstall" for the case where the version of pip we're trying to install is the same as the version bundled with Python
# ("Requirement already up-to-date: pip==8.1.2 in /usr/local/lib/python3.6/site-packages")
# https://github.com/docker-library/python/pull/143#issuecomment-241032683
	&& pip3 install --no-cache-dir --upgrade --force-reinstall "pip==$PYTHON_PIP_VERSION" \
# then we use "pip list" to ensure we don't have more than one pip version installed
# https://github.com/docker-library/python/pull/100
	&& [ "$(pip list |tac|tac| awk -F '[ ()]+' '$1 == "pip" { print $2; exit }')" = "$PYTHON_PIP_VERSION" ] \
	\
	&& find /usr/local -depth \
		\( \
			\( -type d -a -name test -o -name tests \) \
			-o \
			\( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
		\) -exec rm -rf '{}' + \
	&& apt-get purge -y --auto-remove $buildDeps \
	&& rm -rf /usr/src/python ~/.cache

# make some useful symlinks that are expected to exist
run cd /usr/local/bin \
	&& { [ -e easy_install ] || ln -s easy_install-* easy_install; } \
	&& ln -s idle3 idle \
	&& ln -s pydoc3 pydoc \
	&& ln -s python3 python \
	&& ln -s python3-config python-config
# *************************************************************************
# End of Python 3.6 Installation
# *************************************************************************

run apt-get update \
    && apt-get install -y tcl8.6-dev tk8.6-dev python-tk libmysqlclient-dev \
    && apt-get install -y mysql-client \
    && apt-get install -y python-mysqldb \
    && rm -rf /var/lib/apt/lists/*

run pip install --no-cache-dir Django==2.0.4 \
    && pip install --no-cache-dir dynaconf==1.0.2 \
    && pip install --no-cache-dir mysqlclient==1.3.12 \
    && pip install --no-cache-dir djangorestframework==3.8.2 \
    && pip install --no-cache-dir django-redis==4.9.0 \
    && pip install --no-cache-dir django-ipware==2.1.0 \
    && pip install --no-cache-dir Faker==0.8.16 \
    && pip install --no-cache-dir qiniu==7.2.2 \
    && pip install --no-cache-dir doclink==1.1.0 \
    && pip install --no-cache-dir coreapi==2.3.3 \
    && pip install --no-cache-dir pycryptodome==3.6.4 \
    && pip install --no-cache-dir rsa==3.4.2 \
    && pip install --no-cache-dir https://github.com/twisted/twisted/archive/twisted-18.7.0.zip \
    && pip install --no-cache-dir channels==2.1.2 \
    && pip install --no-cache-dir channels-redis==2.2.1 \
    && pip install --no-cache-dir daphne==2.2.1 \
    && pip install --no-cache-dir celery==4.2.1 \
    && pip install --no-cache-dir requests-mock==1.5.2 \
    && pip install --no-cache-dir https://github.com/Supervisor/supervisor/archive/master.zip
