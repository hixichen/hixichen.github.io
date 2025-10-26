---
layout: post
title: "kernel issue tracked in  THP huge page"
date: 2014-12-25
tags: []
---

/ *written @2014, by chen xi*/

Kernel version:2.6.32  
Checked: KSM , THP

LOG:

<4>————[ cut here ]————

<2>kernel BUG at mm/huge\_memory.c:1194!

<4>invalid opcode: 0000 [#1] SMP

<4>last sysfs file: /sys/devices/pci0000:00/0000:00:11.0/0000:06:00.0/host7/scsi\_host/host7/proc\_name

<4>CPU 1

<4>Modules linked in: nf\_conntrack bonding 8021q garp stp llc ipv6 openvswitch(U) libcrc32c iptable\_filter ip\_tables sg igb dca microcode serio\_raw i2c\_i801 i2c\_core iTCO\_wdt iTCO\_vendor\_support shpchp ext4 mbcache jbd2 sd\_mod crc\_t10dif isci libsas scsi\_transport\_sas ahci megaraid\_sas wmi dm\_mirror dm\_region\_hash dm\_log dm\_mod [last unloaded: scsi\_wait\_scan]

<4>

<4>Pid: 3084, comm: redis-server Tainted: G ————— H 2.6.32-279.19.5.el6.ucloud.x86\_64 #1 Huawei Technologies Co., Ltd. Tecal RH2288H V2-12L/BC11SRSG1

<4>RIP: 0010:[] [] split\_huge\_page+0x802/0x850

<4>RSP: 0018:ffff880c5edddbd8 EFLAGS: 00010086

<4>RAX: 00000000ffffffff RBX: ffffea0029333970 RCX: ffffc9000c06b000

<4>RDX: 0000000000000002 RSI: ffff880c61fe9c00 RDI: 0000000000000004

<4>RBP: ffff880c5edddca8 R08: 0000000000000064 R09: 0000000000000001

<4>R10: 0000000000000106 R11: ffff880c5941f300 R12: ffffea0029334000

<4>R13: 0000000000000000 R14: ffffea002932d000 R15: 00000007fcd17be1

<4>FS: 00007fcd25858720(0000) GS:ffff880053820000(0000) knlGS:0000000000000000

<4>CS: 0010 DS: 0000 ES: 0000 CR0: 000000008005003b

<4>CR2: 00007f7086a8a740 CR3: 0000000c57daf000 CR4: 00000000001406e0

<4>DR0: 0000000000000000 DR1: 0000000000000000 DR2: 0000000000000000

<4>DR3: 0000000000000000 DR6: 00000000ffff0ff0 DR7: 0000000000000400

<4>Process redis-server (pid: 3084, threadinfo ffff880c5eddc000, task ffff880c5941e940)

<4>Stack:

<4> 0000000000000002 0000000000000000 0000000000000000 ffff880c00000001

<4> ffff880c5edddc78 ffff88184155d5f0 0000000000000000 ffffffff81180f9b

<4> ffff88184155d630 ffffffff810a9f0d ffffea0052938e78 0000000180010f40

<4>Call Trace:

<4> [] ? \_\_split\_huge\_page\_pmd+0x2b/0xc0

<4> [] ? trace\_hardirqs\_on\_caller+0x14d/0x190

<4> [] \_\_split\_huge\_page\_pmd+0x80/0xc0

<4> [] unmap\_vmas+0xa34/0xc00

<4> [] zap\_page\_range+0x7d/0xe0

<4> [] sys\_madvise+0x54d/0x770

<4> [] ? thread\_return+0x4e/0x7d3

<4> [] ? trace\_hardirqs\_on\_caller+0x14d/0x190

<4> [] ? trace\_hardirqs\_on\_thunk+0x3a/0x3f

<4> [] system\_call\_fastpath+0x16/0x1b

<4>Code: 83 c1 01 e8 69 5e 38 00 0f 0b eb fe 0f 0b eb fe 0f 0b 0f 1f 80 00 00 00 00 eb f7 0f 0b eb fe 0f 0b 0f 1f 84 00 00 00 00 00 eb f6 <0f> 0b eb fe 0f 0b 0f 1f 84 00 00 00 00 00 eb f6 0f 0b eb fe 0f

<1>RIP [] split\_huge\_page+0x802/0x850

<4> RSP

结合代码： 找到的call path:

<上面的back trace中， >

```
unmap_vmas
    --unmap_page_range
        --zap_pud_range
            --zap_pmd_range
                --split_huge_page_pmd
                    --__split_huge_page_pmd
                        --split_huge_page
                            --__split_huge_page
                                --__split_huge_page_refcount
```

line: 1194行如上：

【汇编code】： objdump vmlinux之后， 因为很多函数是static inline的， 所以system map里面找到jump地址，要到调用函数里面去找。

RAX: 00000000ffffffff

RBX: ffffea0029333970

R12: ffffea0029334000

触发原因： eax的值是-1;

eax放的是： add $0x1, %eax <——-> atomic\_read(&(page)->\_mapcount) + 1;

即： \_mapcount的值是-2， 相加之后出现了-1值。

现象是 mapcount出现了理论上不应该也不能出现的值；

mapcount:

* + Count of ptes mapped in
* + mms, to show when page is
* + mapped & limit reverse map
* + searches.

start from “-1”；

经过分析， 理论上此处的mapcount值是 -1

BUG\_ON(page\_mapcount(page\_tail) < 0); 判断值是0 ，就不会出现BUG。

而改写的值不是脏值，看起来像是被减一后出现的。

都是在 put\_compound\_page中。。。

经过搜索

得到下面的一个记录：

+====== start quote =======

* mapcount 0 page\_mapcount 1
* kernel BUG at mm/huge\_memory.c:1384!  
  +  
  +At some point prior to the panic, a “bad pmd …” message similar to the  
  +following is logged on the console:  
  +
* mm/memory.c:145: bad pmd ffff8800376e1f98(80000000314000e7).  
  +  
  +The “bad pmd …” message is logged by pmd\_clear\_bad() before it clears  
  +the page’s PMD table entry.  
  +
* 143 void pmd\_clear\_bad(pmd\_t \*pmd)
* 144 {  
  +-> 145 pmd\_ERROR(\*pmd);
* 146 pmd\_clear(pmd);
* 147 }  
  +  
  +After the PMD table entry has been cleared, there is an inconsistency  
  +between the actual number of PMD table entries that are mapping the page  
  +and the page’s map count (\_mapcount field in struct page). When the page  
  +is subsequently reclaimed, \_\_split\_huge\_page() detects this inconsistency.  
  +
* 1381 if (mapcount != page\_mapcount(page))
* 1382 printk(KERN\_ERR “mapcount %d page\_mapcount %d\n”,
* 1383 mapcount, page\_mapcount(page));  
  +-> 1384 BUG\_ON(mapcount != page\_mapcount(page));  
  +  
  +The root cause of the problem is a race of two threads in a multithreaded  
  +process. Thread B incurs a page fault on a virtual address that has never  
  +been accessed (PMD entry is zero) while Thread A is executing an madvise()  
  +system call on a virtual address within the same 2 MB (huge page) range.  
  +
* virtual address space
* .———————.
* | |
* | |
* .-|———————|
* | | |
* | | |<– B(fault)
* | | |
* 2 MB | |/////////////////////|-.
* huge < |/////////////////////| > A(range)
* page | |/////////////////////|-‘
* | | |
* | | |
* ‘-|———————|
* | |
* | |
* ‘———————‘  
  +  
  +- Thread A is executing an madvise(…, MADV\_DONTNEED) system call
* on the virtual address range “A(range)” shown in the picture.  
  +  
  +sys\_madvise
* // Acquire the semaphore in shared mode.
* down\_read(&current->mm->mmap\_sem)
* …
* madvise\_vma
* switch (behavior)
* case MADV\_DONTNEED:
* madvise\_dontneed
* zap\_page\_range
* unmap\_vmas
* unmap\_page\_range
* zap\_pud\_range
* zap\_pmd\_range
* //
* // Assume that this huge page has never been accessed.
* // I.e. content of the PMD entry is zero (not mapped).
* //
* if (pmd\_trans\_huge(\*pmd)) {
* // We don’t get here due to the above assumption.
* }
* //
* // Assume that Thread B incurred a page fault and
* .———> // sneaks in here as shown below.
* | //
* | if (pmd\_none\_or\_clear\_bad(pmd))
* | {
* | if (unlikely(pmd\_bad(\*pmd)))
* | pmd\_clear\_bad
* | {
* | pmd\_ERROR
* | // Log “bad pmd …” message here.
* | pmd\_clear
* | // Clear the page’s PMD entry.
* | // Thread B incremented the map count
* | // in page\_add\_new\_anon\_rmap(), but
* | // now the page is no longer mapped
* | // by a PMD entry (-> inconsistency).
* | }
* | }
* |
* v  
  +- Thread B is handling a page fault on virtual address “B(fault)” shown
* in the picture.  
  +  
  +…  
  +do\_page\_fault
* \_\_do\_page\_fault
* // Acquire the semaphore in shared mode.
* down\_read\_trylock(&mm->mmap\_sem)
* …
* handle\_mm\_fault
* if (pmd\_none(\*pmd) && transparent\_hugepage\_enabled(vma))
* // We get here due to the above assumption (PMD entry is zero).
* do\_huge\_pmd\_anonymous\_page
* alloc\_hugepage\_vma
* // Allocate a new transparent huge page here.
* …
* \_\_do\_huge\_pmd\_anonymous\_page
* …
* spin\_lock(&mm->page\_table\_lock)
* …
* page\_add\_new\_anon\_rmap
* // Here we increment the page’s map count (starts at -1).
* atomic\_set(&page->\_mapcount, 0)
* set\_pmd\_at
* // Here we set the page’s PMD entry which will be cleared
* // when Thread A calls pmd\_clear\_bad().
* …
* spin\_unlock(&mm->page\_table\_lock)  
  +  
  +The mmap\_sem does not prevent the race because both threads are acquiring  
  +it in shared mode (down\_read). Thread B holds the page\_table\_lock while  
  +the page’s map count and PMD table entry are updated. However, Thread A  
  +does not synchronize on that lock.  
  +  
  +====== end quote =======

通过上面的分析， 和目前的情况。。。。。。

有理由判断：multi thread的情况出现（函数调用过程中，嵌套了多个循环，multi thread的执行是有各种条件的。

The mmap\_sem does not prevent the race because both threads are acquiring  
+it in shared mode (down\_read). Thread B holds the page\_table\_lock while  
+the page’s map count and PMD table entry are updated. However, Thread A  
+does not synchronize on that lock.

需要进一步判断，具体哪里触发的。。。。。

已经怎么构造测试的环境。。。。
