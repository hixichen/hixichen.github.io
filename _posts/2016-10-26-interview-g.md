---
layout: post
title: "interview_g"
date: 2016-10-26
tags: ["interview"]
---

**1**  
判断一个string， 是否是smashable string

我后来看了，就是这个题目啊.

<http://www.geeksforgeeks.org/dynamic-programming-set-32-word-break-problem/>

follow up：  
 如何避免字典是 AAAA, AAAA,AAA, AA 这类的情况。

**2**  
给一个值和权重，random输出，要保证，结果跟权重相同。  
比如： （A ，2） （B ，3） （C ，5）  
输出很多很多次， 要有20％个A，30%B， ％50C

follow up： 如果不是int，是double  
follow up： 如何优化 （binary search）  
follow up： 如果输入 有多个（map），然后需要经常切换map，怎么办？  
//这个问题可以不关心，是因为我的代码写的烂，所以会有这个问题。

**3**

输入： ［[3.0, 1],[4.0, 4],[5.0, 5]］

输入的是： value 和weight 的组合，  
希望输出：这个例子的结果是：( 3.0*1 + 4.0*4 + 5.0\*5 )/(1+4+5)

follow up: 如果输入的类型不一致怎么办

follow up： design api

有一个网状的图，一个大的，上述的人物已经切分到各个节点了， 假设4是server， 1，2，3是做任务的client

设计一些接口， 调用一次4， 输出这个任务的结果。  
(2和3也是可以连接的)

<https://www.google.com/search?q=%E8%8A%82%E7%82%B9%E5%9B%BE&rlz=1C5CHFA_enUS692US692&source=lnms&tbm=isch&sa=X&ved=0ahUKEwikidS6ovnPAhWCShQKHdEgCFAQ_AUICCgB&biw=1365&bih=776#tbm=isch&q=%E7%BD%91%E7%8A%B6%E8%8A%82%E7%82%B9&imgrc=-mSQte-KT2fLPM%3A>

1-－－－-2  
｜ |  
｜ |  
3－－－－4

**4**

输入明文： hi , he!  
密钥是： ACE 其实相当于（0，2，4）

输出密文： 规则是h序列是0， 所以找到密钥的A的相对A的offset  
然后＋＋

比如 h+ A = H (结果要大写)  
i+C = K  
h+E = K  
e+A=E

—结果是： HKKE

followup：一些corner case，会不会加出去： z＋26？？
