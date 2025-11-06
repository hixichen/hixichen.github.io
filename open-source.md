---
layout: page
title: "Open Source Projects"
permalink: /open-source/
---

# Open Source Projects I'm Interested In

As a Staff Software Engineer focused on security infrastructure and distributed systems, I'm deeply passionate about open source projects that advance the state of technology. Here are some projects that I find particularly compelling and why they resonate with my work and interests.

## Security & Identity

### **HashiCorp Vault**
**Why I'm interested**: Having worked extensively with secrets management at scale, I appreciate Vault's comprehensive approach to securing, storing, and controlling access to secrets. Its dynamic secrets capability and robust audit logging make it essential for modern cloud-native architectures. The plugin architecture and API-first design align perfectly with infrastructure-as-code practices.

### **SPIFFE/SPIRE**
**Why I'm interested**: Identity is the foundation of zero-trust security. SPIFFE's workload identity framework and SPIRE's production-ready implementation solve the fundamental challenge of workload authentication in dynamic environments. Having implemented identity solutions using this technology, I'm excited about its potential to standardize workload identity across the industry.

### **Open Policy Agent (OPA)**
**Why I'm interested**: Policy-as-code is transformative for security at scale. OPA's declarative approach with Rego enables consistent policy enforcement across diverse systems. Its integration capabilities with service meshes, Kubernetes, and API gateways make it a cornerstone for implementing fine-grained access control in cloud-native environments.

## Database & Storage

### **FoundationDB**
**Why I'm interested**: The combination of ACID transactions with NoSQL scale is compelling for security infrastructure where consistency is non-negotiable. Apple's use of FoundationDB for iCloud demonstrates its production readiness. Its layered architecture and strong consistency guarantees make it ideal for building security asset databases and other critical systems.

### **etcd**
**Why I'm interested**: As the backbone of Kubernetes, etcd's Raft consensus algorithm and strong consistency model are fascinating from both theoretical and practical perspectives. Understanding distributed consensus is crucial for building reliable systems, and etcd's implementation is a masterclass in production-ready distributed systems.

## Infrastructure & Orchestration

### **Kubernetes**
**Why I'm interested**: Beyond just container orchestration, Kubernetes represents a paradigm shift in how we think about infrastructure. Its declarative model, controller pattern, and extensibility through CRDs and operators align with modern infrastructure practices. The RBAC system and service mesh integration are particularly relevant for security-focused infrastructure.

### **Istio**
**Why I'm interested**: Service mesh architecture addresses the complexity of microservice communication and security. Istio's comprehensive approach to traffic management, security policies, and observability makes it essential for enterprise-scale deployments. The integration with identity systems and policy engines creates powerful security capabilities.

### **ArgoCD**
**Why I'm interested**: GitOps represents the natural evolution of infrastructure management. ArgoCD's declarative continuous delivery model aligns with the principles of infrastructure-as-code and provides the auditability and reliability required for production systems. The integration with Kubernetes and support for multi-cluster deployments are particularly compelling.

## Programming Languages & Tools

### **Go Ecosystem**
**Why I'm interested**: Go's simplicity, concurrency model, and excellent standard library make it ideal for system programming and cloud-native development. Projects like Kubernetes, Docker, etcd, and Vault are all written in Go, demonstrating its effectiveness for building robust, scalable systems.

### **Terraform**
**Why I'm interested**: Infrastructure-as-code is fundamental to modern operations. Terraform's provider ecosystem and state management capabilities enable declarative infrastructure across multiple cloud platforms. The HCL language strikes a good balance between expressiveness and simplicity.

## AI & Machine Learning for Security

### **TensorFlow/PyTorch**
**Why I'm interested**: As AI becomes increasingly important for security applications, these frameworks enable sophisticated threat detection, anomaly analysis, and intelligent access control systems. The potential for AI agents to enhance security posture through pattern recognition and automated response is particularly exciting.

### **OpenTracing**
**Why I'm interested**: Distributed tracing is crucial for understanding complex system behavior and detecting anomalies. OpenTracing's vendor-neutral approach to instrumentation enables comprehensive observability across heterogeneous systems, which is essential for security monitoring and incident response.

## Emerging Technologies

### **WebAssembly (WASM)**
**Why I'm interested**: WASM's sandboxing capabilities and cross-platform execution model have interesting security implications. The ability to run untrusted code safely and the potential for WASM-based plugin architectures in security tools make it worth watching.

### **eBPF**
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

## Additional Projects of Interest

### **OpenBao**
**Website**: [openbao.org](https://openbao.org/)
**Why I'm interested**: OpenBao represents the community-driven evolution of HashiCorp Vault, maintaining the open-source principles that made Vault successful. As someone who has extensive experience with Vault in production, I'm excited about OpenBao's potential to continue advancing secrets management while remaining truly open source. The project's commitment to backward compatibility and community governance makes it a compelling alternative.

### **Ory Kratos**
**Repository**: [ory/kratos](https://github.com/ory/kratos)
**Why I'm interested**: Identity and user management is a critical component of any security architecture. Kratos takes a headless, API-first approach to identity management that aligns with modern cloud-native applications. Its support for various authentication methods, self-service flows, and privacy-focused design makes it particularly interesting for building user-centric security systems.

### **VMware Go KCL (Broader Project)**
**Repository**: [vmware/vmware-go-kcl](https://github.com/vmware/vmware-go-kcl)
**Why I'm interested**: Beyond my specific contributions, the broader project represents an important piece of infrastructure for real-time data processing. Kinesis is crucial for building event-driven architectures, and having a robust Go client library enables better integration with Go-based microservices and data pipelines.

---

## Contributing Philosophy

I believe in contributing back to the open source ecosystem that powers modern technology. Whether through code contributions, documentation improvements, or sharing operational knowledge, participating in these communities helps advance the state of the art and benefits everyone.

My approach to open source contribution focuses on:
- **Security-first thinking**: Bringing security expertise to projects that may not have dedicated security resources
- **Production readiness**: Contributing knowledge from running systems at scale
- **Documentation**: Making complex technologies more accessible through clear documentation and examples
- **Best practices**: Sharing lessons learned from real-world deployments

*If you're working on any of these technologies or have ideas for collaboration, I'd love to connect!*