---
layout: post
title: "wifi_penetration"
date: 2016-09-25
tags: ["security"]
---

做了一下午的WiFi penetration,使用了工具：zANTI，dsploit, lanmitm.

太好玩了，我的实践证明一旦进入内网，机器简直就是鱼肉。  
真实机器： victim： nexus 6, with AVG security suit (free version)  
攻击机：samsung S5 with busybox.

zANTI，dsploit, lanmitm 都能够成功进行中间人攻击。  
最爱的是zANTI，操作极为简单，有完整的nmap扫描(自己选择配置脚本)

而且,在抓包之后能够进行图片抓取，http head match

lanmitm工具抓包之后，需要倒出分析。

一个教程链接： <https://jiji262.github.io/wooyun_articles/drops/%E5%85%B3%E4%BA%8EzANTI%E5%92%8Cdsploit%E4%B8%A4%E6%AC%BE%E5%AE%89%E5%8D%93%E5%AE%89%E5%85%A8%E5%B7%A5%E5%85%B7%E7%9A%84%E5%AF%B9%E6%AF%94.html>

总之，用过之后非常震惊！

**成功抓取微博访问数据，访问图片，cookie劫持登录..**

内网安全，简直，如若无物！

现在的条件是已经在同一个内网，如果没在内网呢？  
能否主动勾搭对方进入当前的局域网呢（自己配置的wifi 热点）呢？

那就妥了，问题发给在palo alto networks做安全工作的谭老师，给了这个： <https://www.wifipineapple.com/>

他说他买了这个。  
设备上有2个网卡： 一个在wifi monitor mode下进行监听，一个发送。

1. 伪造热点。
2. 主动让手机下线 ！！！！！！ 你没看错，是主动发包，让对方离开下在连接中的Wi-Fi热点。
3. 然后伪造报文进行勾搭连接
4. 鱼肉之。。

看了官网上的资料和他的描述的使用体验

整个人都不好..

这简直就是没穿“’窑裤儿” －－ 此处谭老师提醒要文明讲话。。

下周找个ios机器搞一下！
