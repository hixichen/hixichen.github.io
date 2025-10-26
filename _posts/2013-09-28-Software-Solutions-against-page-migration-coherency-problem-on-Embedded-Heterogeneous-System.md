---
layout: post
title: "Software Solutions against page migration coherency problem on Embedded Heterogeneous System @2013"
date: 2013-09-28
tags: ["trustzone"]
---

Author: chen xi,jianlong ye, cheng liang  
Date: 09/2013

**(Abstract)**  
Page migration is a valid strategy of operation system’s memory management for enhancing flexibility and performance. However, for Embedded Heterogeneous Systems, it will result in data inconsistency when sharing large data among Multi-OSes because of physical memory page migration. In this paper, three software solutions are presented to ensure data coherency on the Embedded Heterogeneous Systems.

**1. INTRODUCTION**

Embedded Heterogeneous Systems support multiple Operating Systems running on top of MPSoC, sharing resources like CPU, memory and peripherals, etc. On these systems, memory needs to be managed efficiently due to limited resource. Modern operating systems provide Page Migration (PM) mechanism by merging and sorting the physical pages for memory manager module.

Page migration strategy, like page swap, page merging & combination, CMA/HDMA using Hardware IP memory, can be enabled for each operating system to improve memory mange efficiency [1]. For example, when OS running after a period of time, memory manager will try to force target pages migrate to other appropriate location in order to combine nearby free pages to a continuous chunk.

The advantage of PM including (1) The OS can handle the request for memory allocation faster and more efficiently; (2) Memory fragmentation can be reduced by merging the adjacent physical pages; (3) The OS can increase the memory usage by swapping pages which are not frequently used out to the lower-cost storage. Because of these benefits, PM is widely used in modern Embedded Heterogeneous Systems running multi-OSes.

On the other hand, physical memory pages can be shared among OSes to improve data exchange efficiency. For example, user application’s heap memory pages or dynamic allocated pages will be re-mapped as Shared Memory into target OS, for the purpose of zero-copy data exchange. However, the infrastructure system needs to handle Shared Memory pages properly in each OS, as these pages may be virtually shared but physically distributed [2], and miss-matched caused by PM. Under the circumstance, the data coherency problem happens.

In this paper, page migration cases and data coherency problems are exploited, and three software solutions are presented to avoid data coherency problems among multiple OSes in the Heterogeneous Systems.

**2. PAGE MIGRATION ISSUES AND SOLUTIONS**  
To improve the efficiency of large data exchange among multi OSes, physical memory should be set as shared pages. However, when page migration happened on these shared pages, it results in data inconsistencies among multi-OSes.

2.1 Page migration problem description

On Embedded Heterogeneous systems, each OS manages continuous physical memories in its own memory pool. Beside program’s individual memory mapped inside each OS, Share Memory can also be mapped for data exchange among all OSes. In this section, share memory usage is clarified only with Host OS and Target OS example; In essence, it could be any other Heterogeneous System models.

As below figure shows, Host OS attempts to share data with target OS with the pages set as shared memory. Host OS will fetch these shared memory pages, and send the page locations to Target OS; Target OS do remaps for these pages in accordance, thereafter, can access the data in the share memory. The remap size can be configured, depending on the size of share memory requested by user programs. Fig. 1 A scenario of Page Migration

However, when page migration happens for some reasons, such as constructing continuous memory pages, decreasing memory fragmentation, Host OS moves data contents to new physical pages. This migration does not impact its own user program within the OS, since the virtual address is associated with physical page by MMU. Due to Host OS’s page migration activity is not captured by target OS, target OS still acquires the shared data from original pages. Take above Figure.1 as example, both Host and Target OS map Page A as Shared memory firstly, then Host OS move data content from page A to page B for previous reasons mentioned. After Host OS page migration, Target OS fetches the shared data from page A as before. In this case, page migration leads to data consistency problem in multi-OSes

**2.2 Solutions of Page Migration problems**

To avoid consistency problem described above and ensure smooth data shared channel between the multi-OSes, three methods are proposed in this section.

2.2.1 Dedicated Memory

Set a continuous dedicated memory as shared memory between multi-OSes[3]. In this way, the dedicated memory is managed by the infrastructure system instead of belonging to any OS. That also means, such dedicated region should be mapped by each OS at the booting stage, and must be separated from memory manager to keep away from page migration. In most cases, infrastructure system should support multi-clients use the same shared memory concurrently. To achieve this goal, every client who wants to exchange data must do copy action. Such non-zero copy is unacceptable for some cases like media playback. Another issue is that to support multiple shared memories for one client at one time, infrastructure system must do additional synchronization processing which could lead to performance descends. In conclusion, such solution is only suitable for non-real time environment.

2.2.2 Specially Managed Dedicated Memory

Specify a continuous memory region which is reserved and mapped by both Host OS and Target OS as the shared memory. Thus, each OS has independent virtual address space but on the same physical pages for data sharing. The region cannot be used for any other purpose except memory sharing. Such memory can be effectively managed with particular memory management algorithm and synchronized between Host OS and Target OS.

When memory sharing is needed by user, Host OS will allocate pages from the reserved region according to the required size. Then user programs can put the data directly into the memory allocated by Host OS. The pages of shared memory will be notified to Target OS, thus data contents within these pages can be access by Target OS without any memory copy. Due to the reserved attribute of this memory, physical pages in this area will not be migrated, and data inconsistency issue resulted by page migration is prevented. This solution allows each OS to manage reserved memory region with simple implementations, provides zero-copy performance for data sharing [4], but has the limitation of shared memory region sizes.

2.2.3 Page Migration Event Mechanism

Another way is that, Target OS is notified whenever share memory page is migrated in Host OS. In this method, each OS manages its own memory mappings. When dynamic memory is to be shared, Host OS sends the page address to Target OS for mapping. Thereafter, if page migration occurs, Host OS needs to send real-time notification to Target OS. Then target OS should remap with the latest page address before accessing.

Because of page migration can be triggered by a variety of possible reasons, the real-time detection and notification of page migration are complicated and difficult. In extreme cases, when pages migration occurred and also Target OS had been notified, Host OS may migrate these informed pages to a new address even before Target OS can access the remapped physical pages yet. In order to ensure the data synchronization and notification have been completed, the page migration action should be atomic and protected. This solution provides a data sharing channel which can improve efficiency and guarantee zero-copy performance, while the share memory size is only limited by OS managed memory theoretically. However, this approach brings share memory management overhead, and may have a huge scheduling and communication cost.

**3. IMPLEMENTATION**

　　/*according to the rule : this is the internal tachnical information of the SCRC(samsung china R&D center.)*/

**4. CONCLUSION**  
In this paper, three solutions are proposed to prevent data inconsistency happen under page migration mechanism on Embedded Heterogeneous system. For Dedicated Memory solution, data share among multi-OSes can be achieved, but it needs memory copy during data exchange, which may be unacceptable in real-time scenarios; Specially Managed Dedicated Memory solution can provide zero-copy performance for Multi-OS data sharing, while the maximum sharable memory is limited by dedicated memory size. Page Migration Event Mechanism is valid way for zero-copy and large data sharing, but with the complexity of implementation, and have heavy resource cost.

In conclusion, solution should be select carefully depends on user’s requirements and implementation complexity in practice.

**REFERENCES**

[1]D.Nikolopoulos et.al. UPMlib: A Runtime System for Tuning the Memory Performance of OpenMP Programs on Cache-Coherent NUMA Multiprocessors. pro. Of the 5th ACM Workshop on languages, Compilers and Runtime Systems for Scalable Computers,Rochester,NY,May 2000.

[2] Xavier Martorell, PhD “Dynamic Scheduling of Parallel Applications on Shared-Memory Multiprocessors”, Universitat Politecnica de Catalunya 1999, <http://www.ac.upc.es/homes/xavim/dynsched.pdf>.

[3]M.Bienkowski and M.Korzeniowski. Dynamic page migration under Brownian motiom.In Proc. Of the European Conf.in Parallel Processing (Euro-Par0), 2005.

[4] D. Jiang and J.P. Singh, “Scaling Application Performance on a Cache-Coherent Multiprocessor”, Proceedings of the 26th International Symposium on Computer Architecture, pp. 305-316, Atlanta, USA, 1999.
