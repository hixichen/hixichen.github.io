---
title: "docker_import_error"
date: 2016-07-25
draft: false
tags: ["Docker"]
---

When you face this issue while do “docker import”, please check your image.

tar cvf image.tar image/  
**$cd image/** #you must enter into the directory to get the tar ball.

$tar cvf image.tar \*

check the directory !!I faced the similar log but finally I found it had included the extra directory!

my answer on github:  
<https://github.com/docker/docker/issues/9245>
