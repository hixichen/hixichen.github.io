---
title: "use native docker checkpoint/restore on Ubuntu 14.04"
date: 2016-06-10
draft: false
tags: ["Docker live migration"]
---

writen by chen xi.  
From: xichenpro.com

**[docker version]:**

As we try to use native docker checkpoint, you may need to use this specification version of Docker.  
thanks to Ross Boucher’s great work.

<https://github.com/boucher/docker/releases>  
<https://github.com/boucher/docker/releases/tag/v1.9.0-experimental-cr.1>  
download: docker-1.9.0-dev

$mv docker-1.9.0-dev /usr/bin/docker

$ docker daemon &

$ docker -v  
Docker version 1.9.0-dev, build 59c375a, experimental

**[kernel:]**

#3.13 must be patched, you’d better try to use 3.19.  
That means, you’d better use Ubunt15.04 or higher.

**[CRIU:]**

$ git clone –b v2.2 <https://github.com/xemul/criu.git>  
$ cd criu/

dependecies:  
apt-get install -y libprotobuf-dev libprotobuf-c0-dev protobuf-c-compiler \  
protobuf-compiler python-protobuf libnl-3-dev pkg-config libcap-dev asciidoc

change the version ,mark as hijacked if you want.  
$ vim Makefile.versions  
$ make && make install

$ criu -V  
Version: 2.2  
GitID: v2.2

note: 2.3 had been released on Jun,14.

If you have question, send mail to me : xichen0425@gmail.com  
I have the whole environment in virtual machine.
