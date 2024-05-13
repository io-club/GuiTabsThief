FROM phusion/baseimage:jammy-1.0.4
MAINTAINER D-Jy <duan@d-jy.net>

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

RUN echo 'APT::Get::Clean=always;' >> /etc/apt/apt.conf.d/99AutomaticClean

RUN apt-get update -qqy \
    && DEBIAN_FRONTEND=noninteractive apt-get -qyy install \
	--no-install-recommends \
	python3-venv \
	python3-dev \
	python3-lxml \
	python3-pip \
	libssl-dev \
	pkg-config \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY . /opt/thief/

RUN chown -R www-data:www-data /opt/thief

# Setup openchat
WORKDIR /opt/thief
RUN python3 -m venv venv && \
	. venv/bin/activate && \
 	pip3 install -U pip && \
	pip3 install wheel && \
	pip3 install --upgrade  -r requirements.txt && \
	pip3 cache purge && \
	chown -R www-data:www-data /opt/thief

# Register services to runit
RUN mkdir /etc/service/thief
COPY server.sh /etc/service/thief/run
RUN chmod a+x /etc/service/thief/run

# Define mountable directories.
#VOLUME []

WORKDIR /opt/thief
