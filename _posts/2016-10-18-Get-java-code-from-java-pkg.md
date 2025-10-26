---
layout: post
title: "Get java code from java pkg"
date: 2016-10-18
tags: ["Java"]
---

working on this for homework of mobile security course.

**$mv app-debug.pkg app-debug.zip**  
use zip to uncompress and get the class.dex file.

**$brew install dex2jar**  
d2j-dex2jar classes.dex to get the jar file.

**$d2j-dex2jar classes.dex**  
dex2jar classes.dex -> ./classes-dex2jar.jar

**use jd-gui to get the source code**  
**$ brew install Caskroom/cask/jd-gui**

open the app “jd-gui”:

import the file and we get the code now:
