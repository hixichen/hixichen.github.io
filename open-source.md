---
layout: page
title: "Open Source Projects"
permalink: /open-source/
---

# Open Source Projects I'm Interested In

As a Staff Software Engineer focused on security infrastructure and distributed systems, I'm deeply passionate about open source projects that advance the state of technology. Here are some projects that I find particularly compelling and why they resonate with my work and interests.

## Security & Identity

### **SPIFFE/SPIRE**

**Why I'm interested**: Identity is the foundation of zero-trust security. SPIFFE's workload identity framework and SPIRE's production-ready implementation solve the fundamental challenge of workload authentication in dynamic environments. Having implemented identity solutions using this technology, I'm excited about its potential to standardize workload identity across the industry.

### **Open Policy Agent (OPA)**

**Why I'm interested**: Policy-as-code is transformative for security at scale. OPA's declarative approach with Rego enables consistent policy enforcement across diverse systems. Its integration capabilities with service meshes, Kubernetes, and API gateways make it a cornerstone for implementing fine-grained access control in cloud-native environments.

### **SpiceDB**

**Repository**: [authzed/spicedb](https://github.com/authzed/spicedb)
**Why I'm interested**: SpiceDB is a Zanzibar-inspired authorization system that brings Google's relationship-based access control to the open source world. Its ability to model complex permission relationships and provide real-time authorization decisions at scale makes it particularly compelling for building fine-grained access control systems. The graph-based approach to permissions enables more intuitive security modeling compared to traditional RBAC systems.

## Database & Storage

### **FoundationDB**

**Why I'm interested**: The combination of ACID transactions with NoSQL scale is compelling for security infrastructure where consistency is non-negotiable. Apple's use of FoundationDB for iCloud demonstrates its production readiness. Its layered architecture and strong consistency guarantees make it ideal for building security asset databases and other critical systems.

### **CockroachDB**

**Repository**: [cockroachdb/cockroach](https://github.com/cockroachdb/cockroach)
**Why I'm interested**: CockroachDB's approach to building a distributed SQL database that combines the familiarity of SQL with the scalability of NoSQL is fascinating. Its implementation of distributed transactions using a hybrid logical clock and its ability to survive datacenter failures while maintaining strong consistency make it an excellent choice for mission-critical applications that require both scale and reliability.

### **etcd**

**Repository**: [etcd-io/etcd](https://github.com/etcd-io/etcd)
**Why I'm interested**: As the backbone of Kubernetes, etcd's Raft consensus algorithm and strong consistency model are fascinating from both theoretical and practical perspectives. Understanding distributed consensus is crucial for building reliable systems, and etcd's implementation is a masterclass in production-ready distributed systems.

## Secrets Management

### **OpenBao**

**Website**: [openbao.org](https://openbao.org/)
**Repository**: [openbao/openbao](https://github.com/openbao/openbao)
**Why I'm interested**: OpenBao represents the community-driven evolution of HashiCorp Vault, maintaining the open-source principles that made Vault successful. As someone who has extensive experience with Vault in production, I'm excited about OpenBao's potential to continue advancing secrets management while remaining truly open source. The project's commitment to backward compatibility and community governance makes it a compelling alternative.

## Identity & Access Management

### **Ory Kratos**

**Repository**: [ory/kratos](https://github.com/ory/kratos)
**Why I'm interested**: Identity and user management is a critical component of any security architecture. Kratos takes a headless, API-first approach to identity management that aligns with modern cloud-native applications. Its support for various authentication methods, self-service flows, and privacy-focused design makes it particularly interesting for building user-centric security systems.

## DevOps & Infrastructure

### **ArgoCD**

**Repository**: [argoproj/argo-cd](https://github.com/argoproj/argo-cd)
**Why I'm interested**: GitOps represents the natural evolution of infrastructure management. ArgoCD's declarative continuous delivery model aligns with the principles of infrastructure-as-code and provides the auditability and reliability required for production systems. The integration with Kubernetes and support for multi-cluster deployments are particularly compelling.

## Observability

### **OpenTelemetry**

**Repository**: [open-telemetry/opentelemetry-specification](https://github.com/open-telemetry/opentelemetry-specification)
**Why I'm interested**: OpenTelemetry (the successor to OpenTracing) provides vendor-neutral observability through metrics, logs, and traces. Its unified approach to instrumentation enables comprehensive observability across heterogeneous systems, which is essential for security monitoring and incident response. The project's momentum and industry adoption make it the de facto standard for observability.

## Emerging Technologies

### **WebAssembly (WASM)**

**Repository**: [WebAssembly/spec](https://github.com/WebAssembly/spec)
**Why I'm interested**: WASM's sandboxing capabilities and cross-platform execution model have interesting security implications. The ability to run untrusted code safely and the potential for WASM-based plugin architectures in security tools make it worth watching.

### **eBPF**

**Repository**: [libbpf/libbpf](https://github.com/libbpf/libbpf)
**Why I'm interested**: The ability to run sandboxed programs in kernel space opens up new possibilities for security monitoring, network filtering, and performance optimization. Projects like Cilium and Falco demonstrate eBPF's potential for building next-generation security and networking tools.

## Projects I've Contributed To

### **VMware Go KCL**

**Repository**: [vmware/vmware-go-kcl](https://github.com/vmware/vmware-go-kcl)
**My contribution**: [Client Library Implementation](https://github.com/vmware/vmware-go-kcl/tree/master/clientlibrary)
**Why I contributed**: Kinesis Client Library for Go fills a crucial gap in the AWS ecosystem for Go developers. Having worked with distributed systems and event streaming, I understand the importance of reliable client libraries for processing real-time data streams. Contributing to the client library helps ensure robust Kinesis integration for Go applications.

### **OpenBao OAuth App Secrets Plugin**

**Repository**: [openbao/openbao-plugin-secrets-oauthapp](https://github.com/openbao/openbao-plugin-secrets-oauthapp)
**My contribution**: [Pull Request #31](https://github.com/openbao/openbao-plugin-secrets-oauthapp/pull/31)
**Why I contributed**: As someone deeply involved in secrets management, contributing to OpenBao's OAuth application secrets plugin aligns with my expertise in secure credential handling. This plugin enables dynamic OAuth token management, which is essential for modern API integrations and follows the principle of least privilege access.

### **CAEP SSF Hub**

**Repository**: [hixichen/caep.dev](https://github.com/hixichen/caep.dev/tree/main/ssf-hub)
**My contribution**: SSF Hub implementation
**Why I contributed**: Continuous Access Evaluation Protocol (CAEP) and Shared Signals Framework (SSF) represent the future of real-time security event sharing. Building the SSF Hub demonstrates my commitment to advancing identity security standards and enabling better threat response across federated systems.

---

## Contributing Philosophy

I believe in contributing back to the open source ecosystem that powers modern technology. Whether through code contributions, documentation improvements, or sharing operational knowledge, participating in these communities helps advance the state of the art and benefits everyone.

My approach to open source contribution focuses on:

- **Security-first thinking**: Bringing security expertise to projects that may not have dedicated security resources
- **Production readiness**: Contributing knowledge from running systems at scale
- **Documentation**: Making complex technologies more accessible through clear documentation and examples
- **Best practices**: Sharing lessons learned from real-world deployments

_If you're working on any of these technologies or have ideas for collaboration, I'd love to connect!_
