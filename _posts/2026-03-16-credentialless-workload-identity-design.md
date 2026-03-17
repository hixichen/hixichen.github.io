---
title: "Credentialless Workload Identity for Multi-Tenant AI Inference Platforms"
date: 2026-03-16
draft: false
tags: ["security", "kubernetes", "workload-identity", "multi-tenant", "ai-inference", "zero-trust"]
---

# Credentialless Workload Identity for Multi-Tenant AI Inference Platforms

## TL;DR

This post captures the design thinking behind a **credentialless workload identity system** for multi-tenant Kubernetes-based AI inference platforms. The core insight: in environments where tenants provide model code but the platform controls the image build and pod spec, the **container image digest** can serve as a cryptographic tenant identity binding — and identity can be resolved entirely server-side without ever placing a credential inside the tenant's pod. A delegated hierarchical signing architecture (per-cluster keys certified by a single root) enables scalable token issuance across hundreds of clusters or more with single-cluster blast radius on key compromise.

---

## 1. Problem Statement

### The Scenario

A multi-tenant AI inference platform operates as follows:

- **Tenants** provide model code and weights
- **Platform** controls the image build pipeline, base images, pod spec, scheduling, and cluster infrastructure
- Tenant pods run on shared Kubernetes clusters (hundreds or more)
- Tenants get root access inside their containers (for debugging, custom dependencies, etc.)
- Platform deliberately disables `automountServiceAccountToken` on tenant pods to minimize attack surface

**The question**: How does a platform service know, with cryptographic certainty, which tenant a given pod belongs to — when the pod has no credential, no SA token, and the tenant has root inside the container?

### Why This Matters

Without reliable workload identity:

- Tenant A could impersonate Tenant B when calling platform APIs (metrics, logging, model registry, inference routing)
- Audit trails are unreliable
- Cross-tenant data misrouting becomes possible
- Resource accounting and billing can be gamed

### Constraints

| Constraint | Rationale |
|---|---|
| No credential in the pod | Tenant has root — anything in the pod is extractable |
| No per-node agent (no SPIRE) | Hundreds of clusters, operational overhead is prohibitive |
| No sidecar proxy | GPU inference is latency-sensitive; resource overhead unacceptable |
| No reliance on SA tokens | `automountServiceAccountToken: false` by design |
| Single-cluster blast radius | Compromise of one cluster's key must not affect other clusters |
| Microsecond-scale identity resolution | Identity cannot be on the inference hot path |

---

## 2. Prior Art Analysis

### What Exists Today

#### SPIFFE/SPIRE
- **What it does**: Per-node agent (DaemonSet) attests workloads using kernel-level signals, kubelet info, and workload selectors (namespace, SA, image digest). Issues X.509-SVIDs or JWT-SVIDs.
- **Why it doesn't fit**: Requires deploying and maintaining SPIRE agents on every node across hundreds of clusters. The SVID (credential) is delivered to the workload — a tenant with root can extract it. SPIRE solves "grant identity to the pod"; we need "verify identity of the pod without the pod knowing."
- **Key gap**: SPIRE puts the credential inside the workload. We want zero credentials in the tenant environment.

#### Kubernetes ServiceAccount Tokens + TokenReview
- **What it does**: Projected SA tokens are short-lived JWTs signed by the K8s API server. TokenReview API validates them.
- **Why it doesn't fit**: We deliberately disable `automountServiceAccountToken`. Even if enabled, the token is inside the pod and extractable by root.
- **Key gap**: Requires a credential in the pod.

#### Service Mesh Identity (Istio, Linkerd)
- **What it does**: Sidecar proxy or per-node ztunnel handles mTLS, issues certificates from a mesh CA.
- **Why it doesn't fit**: Sidecar adds latency and resource overhead on GPU inference pods. With `shareProcessNamespace: true`, tenant root can dump sidecar memory. Even with namespace isolation, the sidecar model adds operational complexity.
- **Key gap**: Still puts credentials in the pod's network namespace.

#### Image Signature Verification (Cosign, Notary, Kyverno verifyImages)
- **What it does**: Admission-time verification that an image was signed by a trusted key. Kyverno/Portieris/Connaisseur reject unsigned images.
- **Why it's related but different**: These verify "is this image allowed to run?" — a binary admission decision. They do NOT establish runtime workload identity. After admission, the image digest is not used for ongoing identity resolution.
- **Key gap**: Admission-only, no runtime identity. No token issuance. No server-side identity derivation.

#### Attestation-Based Identity (Aembit, SPIRE attestation)
- **What it does**: Collects environmental evidence (image digest, namespace, node metadata) and verifies against policy before issuing a credential.
- **Why it's related**: The evidence-gathering model is similar. But attestation systems still issue a credential to the workload.
- **Key gap**: Credential is delivered to the workload after attestation. Our model never delivers a credential to the tenant.

#### Cloud Provider Workload Identity (GKE WI, AKS WI, EKS IRSA)
- **What it does**: Federates K8s SA tokens with cloud IAM. Pod gets a projected SA token, exchanges it for a cloud access token.
- **Why it doesn't fit**: Requires SA token in the pod. Designed for workloads accessing cloud resources, not for platform-internal tenant identity.
- **Key gap**: Requires `automountServiceAccountToken: true`.

#### Binary Authorization (GCP)
- **What it does**: Admission-time policy that requires attestations (signatures) on image digests before allowing deployment.
- **Why it's related**: Uses image digest as a trust anchor for admission decisions.
- **Key gap**: Admission-only. No runtime identity. No token issuance.

#### Teleport Workload Identity
- **What it does**: Recently added `image_digest` as an attestor field for K8s, Docker, and Podman workloads.
- **Why it's related**: Shows industry movement toward using image digest for identity.
- **Key gap**: Still issues a credential (SVID-like) to the workload. Requires Teleport agent.

### The Gap We Fill

| Capability | SPIFFE | Istio | Cosign/Kyverno | Cloud WI | **Our System** |
|---|---|---|---|---|---|
| No credential in workload | ❌ | ❌ | N/A | ❌ | ✅ |
| No per-node agent | ❌ | ❌ | ✅ | ✅ | ✅ |
| No sidecar | ✅ | ❌ | ✅ | ✅ | ✅ |
| Runtime identity (not just admission) | ✅ | ✅ | ❌ | ✅ | ✅ |
| Image digest as identity anchor | Partial | ❌ | ✅ (admission only) | ❌ | ✅ |
| Split-trust (tenant + platform) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Single-cluster blast radius | ❌ | ❌ | N/A | N/A | ✅ |
| Works with `automountServiceAccountToken: false` | ✅ | ✅ | ✅ | ❌ | ✅ |

**No existing system combines all of**: credentialless pods + image-digest-as-runtime-identity + admission-time HMAC tamper protection + delegated hierarchical signing + server-side-only identity resolution.

---

## 3. Design

### 3.1 Core Insight: Image Digest as Tenant Identity

In our platform model, the build pipeline is the **identity authority**:

```
Tenant provides: model code + weights
Platform provides: base image + runtime + instrumentation
Build pipeline produces: image with unique digest sha256:abc123...

sha256:abc123... = Tenant A, Model X, Version 3
sha256:def456... = Tenant B, Model Y, Version 1
```

The digest is:
- **Immutable** — content-addressable, any change produces a different digest
- **Unique per tenant/model/version** — deterministic binding
- **Verifiable via K8s API** — the pod spec records which digest is running
- **Non-forgeable by tenant** — tenant doesn't control the build pipeline
- **Non-forgeable by platform for non-existent workloads** — digest is determined by actual image content including tenant code

This is the **split-trust property**: neither party alone can produce a valid identity binding.

### 3.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    BUILD TIME (once per image)            │
│                                                          │
│  Tenant code + Platform base → Build Pipeline            │
│       ↓                                                  │
│  Image sha256:abc123 produced                            │
│  Image manifest signed (cosign)                          │
│  Identity Registry updated:                              │
│    sha256:abc123 → {tenant: acme, model: llama3-70b}     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│             ADMISSION TIME (once per pod)                 │
│                                                          │
│  Pod CREATE → Mutating Webhook fires                     │
│    1. Extract image digest from pod spec                 │
│    2. Lookup digest in Identity Registry                 │
│    3. Reject if unknown image                            │
│    4. Compute HMAC(pod_uid + digest + tenant, secret)    │
│    5. Annotate pod:                                      │
│       platform.example.io/tenant-id: acme                         │
│       platform.example.io/model-id: llama3-70b                    │
│       platform.example.io/identity-hmac: <HMAC>                   │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              RUNTIME (per request, microseconds)          │
│                                                          │
│  Identity Proxy (platform-system namespace)               │
│    - Watches all pods via K8s informer (constant conn)   │
│    - Maintains in-memory cache: podIP → identity record  │
│                                                          │
│  On request from tenant pod:                             │
│    1. Source IP → cache lookup → get identity record     │
│    2. Recompute HMAC locally → verify match              │
│    3. Sign JWT with cluster-specific key                 │
│    4. Return/attach token                                │
│                                                          │
│  Cost: ~microseconds, zero external calls                │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│           HIERARCHICAL SIGNING (cross-cluster)           │
│                                                          │
│  Root CA (offline/HSM)                                   │
│    ├── Cluster-A cert (24h TTL) → signs JWTs             │
│    ├── Cluster-B cert (24h TTL) → signs JWTs             │
│    └── Cluster-N cert (24h TTL) → signs JWTs             │
│                                                          │
│  Verifiers trust ONLY the root public key                │
│  Revocation: stop renewing cluster cert + deny list      │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Traffic Routing: SDK-Based, Not Transparent Interception

A critical question: how does traffic from the tenant pod reach the identity proxy?

AI inference platforms typically use a **platform-controlled runtime layer** inside the container. The tenant writes model code (e.g., a `predict()` function), but the platform wraps it in a model server process that handles HTTP serving, health checks, metrics, and communication with platform APIs. This runtime is baked into the base image by the platform's build pipeline — the tenant does not control it.

This means **SDK-based routing** is the natural fit. The platform runtime is already configured to call platform APIs (for logging, metrics, model registry callbacks, weight pulling, etc.) through a known endpoint. We simply configure that endpoint to be `identity-proxy.platform-system.svc.cluster.local`. No iptables manipulation, no eBPF, no DaemonSet, no transparent interception.

```
┌─────────────────────────────────────┐
│  Tenant Pod                          │
│                                      │
│  ┌──────────────────────────────┐   │
│  │ Tenant model code            │   │
│  │   predict(), load(), etc.    │   │
│  └──────────┬───────────────────┘   │
│             │ calls platform APIs    │
│  ┌──────────▼───────────────────┐   │
│  │ Platform Runtime (base image) │   │
│  │   - HTTP server wrapper       │   │
│  │   - Metrics/logging client    │   │
│  │   - Configured endpoint:      │   │
│  │     identity-proxy.platform-  │   │
│  │     system.svc.cluster.local  │   │
│  └──────────┬───────────────────┘   │
└─────────────┼───────────────────────┘
              │
              ▼
     Identity Proxy (platform-system)
```

Key properties:
- **No interception needed** — the platform runtime knows where to call
- **Not on the inference hot path** — actual model inference requests go directly from load balancer to pod. Only platform API calls (low-frequency) route through the proxy.
- **No DaemonSet, no eBPF, no iptables** — just a regular Kubernetes Service
- **Tenant cannot bypass it** — the platform runtime is in the base image, which the tenant doesn't control. The tenant's model code calls platform APIs through the runtime's abstractions.

### 3.4 Admission-Time HMAC: Why Annotations Are Safe

Kubernetes annotations are technically mutable (`kubectl edit`, `kubectl annotate`). But:

1. **Tenants have no RBAC to patch pod objects** — only cluster admins can
2. **HMAC prevents tampering** — even if someone modifies the annotation text, they can't recompute a valid HMAC without the server-side secret
3. **HMAC inputs include pod UID** — which is immutable and globally unique

The HMAC is computed over:

```
HMAC-SHA256(secret, cluster_id | namespace | pod_uid | image_digest | tenant_id | model_id)
```

Including `cluster_id` and `namespace` (in addition to pod UID and digest) prevents any theoretical cross-namespace or cross-cluster collision and ensures the identity binding is fully scoped.

The HMAC acts as a server-side seal over the identity claims. The annotations are human-readable metadata; the HMAC is the cryptographic proof.

**HMAC key rotation**: The identity proxy must support an array of valid HMAC secrets (e.g., `[active, previous]`). During rotation: (1) the admission webhook starts signing with the new key, (2) the proxy accepts both old and new keys, (3) after all pods signed with the old key have terminated (or a maximum grace period), the old key is removed. Pod annotations are immutable by RBAC — there is no need to re-stamp running pods because they will eventually be replaced through normal deployment cycles.

**Admission webhook failure policy**: The mutating webhook must be configured with `failurePolicy: Fail`. If the webhook is unavailable and the policy is `Ignore`, pods would be created without identity annotations, bypassing the entire identity system.

### 3.5 Watch-Based Cache: Why Pod IP Lookup Works

**Concern raised**: Pod IPs are reused across namespaces.

**Why it's okay**: The IP is a *lookup key*, not the identity. The flow is:

```
Source IP 10.0.5.23
  → K8s informer cache lookup
  → Returns: Pod UID (globally unique, never reused)
           + namespace
           + image digest
           + HMAC
  → HMAC verification confirms integrity
  → Pod UID is the actual identity anchor
```

Two pods can't have the same IP simultaneously (CNI guarantees this). IP reuse over time doesn't matter because the informer removes dead pods from cache immediately via watch events.

**Pod lifecycle events and cache**:

| Event | Cache Action |
|---|---|
| Pod created | Watch event → add to cache |
| Pod gets IP | Watch event → update cache with IP |
| Pod deleted | Watch event → remove from cache |
| Pod restarted (new UID) | Old entry removed, new entry added |
| IP reused by new pod | Old entry already gone, new entry has different UID |

### 3.6 Informer Race Condition Mitigation

Kubernetes informers are eventually consistent. When a pod starts, there is a window between the CNI assigning an IP and the identity proxy's cache being updated via the watch event. If the tenant container fires a platform API call immediately on startup, the proxy may see an unknown IP.

**Mitigation strategy (layered)**:

**Layer 1: Retry with backoff in the platform SDK.** The platform runtime (which we control in the base image) retries on "unknown pod" responses with exponential backoff (100ms → 200ms → 400ms → 800ms). The informer should catch up within 1-2 seconds in the worst case. This handles the vast majority of race conditions transparently. Note: a hostile tenant can kill the SDK and call the proxy directly — this layer is a convenience, not a security control.

**Layer 2: Server-side rate-limited K8s API fallback.** If the proxy receives a request from an IP not in cache, it falls back to a synchronous `GET /api/v1/pods?fieldSelector=status.podIP=X` call against the K8s API server. **Critically, this fallback is rate-limited per source IP** (e.g., 1 lookup per IP per 2 seconds) to prevent a hostile tenant from using the proxy as a confused deputy to DoS the K8s API server. Excess requests from unknown IPs receive a 429 response. Standard HTTP/TCP retries handle the transient drop.

```
Pod starts → first platform API call → proxy cache miss
  │
  ├── SDK retries with backoff (100ms, 200ms, 400ms)  ← convenience, not security
  │     └── Cache updated via watch event? → Cache hit → Done
  │
  └── Proxy: unknown IP, not in cache
        ├── Rate limit check: seen this IP in last 2s? → 429
        └── Rate limit OK → synchronous K8s API lookup
              └── Pod found → cache populated → identity resolved
```

This ensures zero failed identity resolutions while keeping the hot path (subsequent requests) at microsecond latency with no API server calls. The rate limiter protects the K8s API server from abuse by hostile tenants who bypass the SDK.

### 3.7 Delegated Hierarchical Signing

**Problem**: Hundreds of clusters, each needs to sign identity tokens. Single shared key = single point of compromise.

**Solution**: Two-level key hierarchy with short-lived delegation.

```
Root Key (ECDSA P-256, offline/HSM)
  │
  │ Signs cluster certificates (24h TTL)
  │
  ├── Cluster-A: own key pair + cert signed by root
  ├── Cluster-B: own key pair + cert signed by root
  └── Cluster-N: own key pair + cert signed by root

JWT issued by Cluster-A:
  Header: { "alg": "ES256", "x5c": [cluster-A-cert] }
  Payload: { "iss": "platform-identity:cluster-a",
             "sub": "tenant:acme/model:llama3-70b",
             "pod_uid": "...",
             "image_digest": "sha256:abc...",
             "exp": ... }
  Signature: ECDSA_P256_sign(cluster_A_private_key, ...)

Verification (any service, any cluster):
  1. Extract cluster cert from JWT header
  2. Verify cert signature against root public key ← ONE KEY
  3. Check cert not expired, cluster not on deny list
  4. Verify JWT signature against cert's public key
  Done.
```

**Revocation**:
- Cluster-A compromised → stop renewing its cert → cert expires in ≤24h
- For immediate revocation: add "cluster-a" to deny list (tiny static list)
- No global key rotation needed
- Other clusters unaffected

### 3.8 What the Tenant Sees

**Nothing.**

The tenant pod makes HTTP calls to platform services. The identity proxy intercepts or mediates these calls, attaches the signed JWT, and the downstream service verifies it. The tenant never sees a token, never holds a credential, never knows the identity mechanism exists.

If the tenant inspects their pod:
- No SA token at `/var/run/secrets/`
- No identity-related environment variables
- No certificates on disk
- No sidecar process
- Annotations are visible via downward API, but the HMAC is useless without the server secret

---

## 4. Threat Analysis

### 4.0 Pod Threat Model: What "Tenant Has Root" Actually Means

AI inference platforms have a unique trust model. The tenant provides arbitrary code (model implementations) that runs inside the pod with root privileges. This is fundamentally different from typical multi-tenant SaaS where the platform controls all code execution.

**What the tenant CAN do inside the pod (assumed hostile)**:
- Execute arbitrary code as root
- Read/write the entire container filesystem
- Inspect all environment variables
- Kill any process in the container, including the platform runtime/SDK
- Make arbitrary outbound HTTP calls to any reachable endpoint
- Run tcpdump or packet inspection tools (unless `NET_RAW` is dropped)
- Install packages, modify binaries, run reverse shells
- Inspect the downward API (pod name, namespace, annotations, labels)

**What the tenant CANNOT do (enforced by platform)**:
- Escape the container (User Namespaces, seccomp, no `privileged: true`)
- Access the host filesystem or host network (`hostNetwork: false`, no `hostPID`)
- Forge their source IP (CNI enforcement + `NET_RAW`/`NET_ADMIN` dropped)
- Modify pod annotations via K8s API (no RBAC)
- Access pods in other namespaces (no RBAC)
- Access the `platform-system` namespace (no RBAC + NetworkPolicy)
- Dump memory of processes in other containers (no `shareProcessNamespace`)

**Why "tenant can kill the platform SDK" doesn't break the design**:
The platform SDK (in the base image) is a convenience layer for routing, retry, and metrics. If a tenant kills it and makes raw HTTP calls directly to the identity proxy, the proxy still identifies them correctly by source IP. The tenant cannot gain a *different* identity by bypassing the SDK — they just lose the SDK's retry logic and get raw HTTP responses. The identity proxy is the enforcement point, not the SDK.

**What DOES matter**: the tenant can reach the identity proxy endpoint and could spam it with requests. This is addressed by rate limiting (Section 3.6) and NetworkPolicy (Section 5.6).

### What a Malicious Tenant Can Do

| Attack | Mitigated? | How |
|---|---|---|
| Read credential from pod filesystem | ✅ | No credential exists in the pod |
| Dump environment variables | ✅ | No identity env vars |
| Dump sidecar memory | ✅ | No sidecar |
| Forge identity annotations | ✅ | No RBAC to patch pods + HMAC prevents forgery |
| Spoof source IP via raw packets | ✅ | `NET_RAW` and `NET_ADMIN` capabilities dropped (see prerequisites); CNI enforces source IP |
| Impersonate another tenant's pod | ✅ | Would need: different pod UID (can't forge) + matching HMAC (can't compute without secret) |
| Kill platform SDK and call proxy directly | ✅ | Proxy still identifies by source IP. Tenant gets same identity regardless of how they call. |
| Spam proxy to DoS K8s API via fallback lookups | ✅ | Proxy enforces per-IP rate limiting on unknown-IP fallback (Section 3.6) |
| Call platform services directly, bypassing proxy | ✅ | NetworkPolicy restricts: platform APIs only accept traffic from identity proxy (Section 5.6) |
| Read another tenant's annotations via K8s API | ✅ | No RBAC to list pods in other namespaces |
| Manipulate network namespace from within container | ✅ | `NET_ADMIN` capability dropped; User Namespaces (`hostUsers: false`) further scope capabilities |

### What a Compromised Cluster Node Can Do

| Attack | Mitigated? | How |
|---|---|---|
| Extract cluster signing key from proxy memory | Partially | Key is in proxy memory; but compromise is contained to one cluster |
| Forge identity tokens for pods on this cluster | ⚠️ | Yes, this is possible if the node is fully compromised. Blast radius = one cluster only. |
| Forge identity tokens for pods on OTHER clusters | ✅ | Different cluster keys. Would need to compromise root key (offline/HSM). |
| Launch ghost pods via compromised kubelet | ⚠️ | Out of scope. Kubelet credentials could create pods or manipulate CNI routing. Host-level compromise completely breaks IP-to-identity mapping for that node. Contained by single-cluster blast radius. See Section 4.1. |

### What a Compromised Identity Proxy Can Do

The identity proxy is the **highest-privilege component** in the system — it holds the cluster signing key and the HMAC secret. Treat it like a CA.

| Attack | Mitigated? | How |
|---|---|---|
| Issue tokens for fake pods | Partially | Proxy has the signing key + HMAC secret. But tokens would reference pod UIDs that verifiers can cross-check. |
| Issue tokens for real pods with wrong tenant | ⚠️ | Possible. This is the highest-privilege compromise in the system. Contained to one cluster. |

**Hardening for the identity proxy** (defense-in-depth):
- Run in a dedicated node pool with no tenant workloads
- Memory locking (no swap), read-only filesystem, minimal runtime
- Strict NetworkPolicy: only accepts traffic from tenant pod CIDRs, only egresses to platform APIs
- Optionally separate JWT signing into an isolated signer service or Vault Transit (reduces blast radius if proxy process is compromised but signing key is in KMS)

---

## 4.1 Out of Scope: Host-Level Node Compromise

Host-level node compromise (e.g., container escape, kubelet credential theft, kernel exploit) is **out of scope** for this design. A compromised node has access to:

- Kubelet credentials (can create/delete pods, read secrets in the node's scope)
- CNI data plane (can manipulate IP routing for pods on that node)
- Container runtime (can inspect/modify running containers)
- Identity proxy memory (if the proxy pod runs on the compromised node)

In this scenario, IP-to-identity mapping is completely broken for that node. The attacker can launch ghost pods, hijack IPs of legitimate pods, or extract the cluster signing key from the proxy's memory.

**Why this is acceptable**: The blast radius is contained to a single cluster by the hierarchical signing architecture. Tokens forged by a compromised cluster key are only valid until the cluster cert expires (≤24h) or the cluster is added to the deny list. Other clusters remain unaffected. No global key rotation is required.

**Separate workstreams that address host-level risk** (not part of this design):
- User Namespaces (`hostUsers: false`) to prevent container-to-host UID mapping
- Seccomp RuntimeDefault profiles to limit syscall surface
- Node attestation (TPM-based boot verification, confidential computing)
- Kubelet credential rotation and least-privilege node RBAC

---

## 5. Security Prerequisites

The following are **hard requirements** for this design to provide its security guarantees. If any prerequisite is not met, the system's threat model is weakened.

### 5.1 CNI Source IP Enforcement

The CNI plugin must enforce that pods cannot send packets with spoofed source IP addresses. This is the foundational network-level trust that enables IP-based pod identification.

**Validated CNI plugins**: Calico, Cilium, AWS VPC CNI, Azure CNI, GKE CNI all enforce source IP by default. For clusters on cloud partner infrastructure, CNI source IP enforcement must be verified during cluster onboarding. **If a cluster cannot guarantee CNI-level anti-spoofing, it must not join the platform.**

### 5.2 Capability Dropping: NET_RAW and NET_ADMIN

All tenant workload pods must drop the `NET_RAW` and `NET_ADMIN` Linux capabilities. Without this:
- `NET_RAW` allows crafting raw packets with arbitrary source IPs from within the container
- `NET_ADMIN` allows modifying the container's network namespace, routing tables, and iptables rules

Enforce via admission policy (e.g., Kyverno ClusterPolicy):

```yaml
spec:
  rules:
  - name: drop-dangerous-capabilities
    match:
      any:
      - resources:
          kinds: ["Pod"]
          namespaces: ["tenant-*"]
    validate:
      message: "Tenant containers must drop NET_RAW and NET_ADMIN"
      pattern:
        spec:
          containers:
          - securityContext:
              capabilities:
                drop: ["NET_RAW", "NET_ADMIN"]
```

Combined with User Namespaces (`hostUsers: false`), capabilities are scoped to the user namespace, providing defense-in-depth even if the policy is misconfigured.

### 5.3 RBAC Restrictions on Tenant Namespaces

Tenants must have **no RBAC permissions** to:
- Patch, update, or delete pod objects (prevents annotation tampering)
- List pods in other tenant namespaces (prevents cross-tenant reconnaissance)
- Access the `platform-system` namespace (prevents direct proxy/webhook interaction)

### 5.4 `automountServiceAccountToken: false`

All tenant workload pods must have `automountServiceAccountToken: false` set in the pod spec. This ensures no Kubernetes-native credential exists in the pod and is a foundational assumption of the credentialless design.

### 5.5 `shareProcessNamespace: false`

Tenant pods must not enable shared process namespaces. With `shareProcessNamespace: true`, root in a tenant container could access `/proc/<pid>/mem` of other processes in the pod (relevant if any platform-controlled process runs alongside the tenant container).

### 5.6 `hostNetwork: false` and Host Namespace Isolation

Tenant pods must have `hostNetwork: false`. A pod with host networking bypasses CNI entirely — it uses the node's IP address, breaking the IP-to-pod identity mapping. Similarly, `hostPID: false` and `hostIPC: false` must be enforced. These should be enforced via admission policy alongside the capability restrictions in Section 5.2.

### 5.7 IPv6 Anti-Spoofing

If clusters are dual-stack (IPv4 + IPv6), the CNI must enforce source IP anti-spoofing on **both** IPv4 and IPv6. Many CNI plugins enable IPv4 anti-spoofing by default but do not explicitly configure IPv6 rules. Either disable IPv6 in tenant namespaces or verify that the CNI attests to IPv6 anti-spoofing during cluster onboarding.

### 5.8 NetworkPolicy: Platform APIs Behind Identity Proxy

Platform API services (metrics, logging, model registry, etc.) must only accept traffic from the identity proxy, not directly from tenant pods. This is enforced via Kubernetes NetworkPolicy:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: platform-api-ingress
  namespace: platform-system
spec:
  podSelector:
    matchLabels:
      app: platform-api
  policyTypes: ["Ingress"]
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: identity-proxy
```

Without this, a tenant could bypass the identity proxy and call platform APIs directly. Even without a token, this could expose unauthenticated endpoints or create confusion in audit logs.

### 5.9 Admission Webhook `failurePolicy: Fail`

The mutating admission webhook that stamps identity annotations must be configured with `failurePolicy: Fail`. If set to `Ignore`, webhook unavailability would allow pods to be created without identity annotations, completely bypassing the identity system. This is a hard requirement — pods without HMAC annotations must never be allowed to run.

---

## 6. Performance Characteristics

### Per-Pod Lifecycle Cost

| Event | Operations | Latency |
|---|---|---|
| Image build | Sign manifest, register in identity DB | Offline, not on critical path |
| Pod creation | Webhook: 1 DB lookup + 1 HMAC compute + 1 annotation mutation | ~10ms added to pod creation |
| First request | Cache lookup + HMAC verify + JWT sign | ~100μs |
| Subsequent requests | Cache lookup + return cached JWT | ~10μs |
| Pod restart | New UID → new cache entry → new first request | Same as first request |

### Scaling Characteristics

| Dimension | Behavior |
|---|---|
| 1000 pods starting simultaneously | 1000 watch events (handled by K8s informer natively) + 1000 JWT signs on first request |
| Hundreds of clusters | Each cluster independently caches and signs. No cross-cluster dependency. |
| Identity proxy failure | Pods lose identity resolution. No cascading failure to other clusters. |
| Root signer failure | No impact on running clusters (certs already issued). Impact only on cert renewal (24h buffer). |

---

## 7. Implementation Roadmap

### Phase 1: Foundation
- Build pipeline registers image digests with tenant mapping in identity DB
- Deploy Kyverno mutating webhook to stamp pods with identity annotations + HMAC
- Deploy identity proxy (single replica) per cluster with informer-based cache

### Phase 2: Token Issuance
- Identity proxy signs JWTs with per-cluster ES256 (ECDSA P-256) key
- Deploy root key management (can start with Vault Transit, migrate to HSM later)
- Integrate first platform service (e.g., metrics/logging) to consume identity tokens

### Phase 3: Hardening
- Image manifest signing (cosign) at build time
- Admission webhook verifies image signatures (not just digest presence in DB)
- NetworkPolicy restricting tenant pod → platform service communication paths
- JWT audience scoping per downstream service

### Phase 4: Scale
- Automated cluster cert rotation (< 24h TTL)
- Deny list distribution to all verifiers (push-based or pull with short cache)
- Monitoring: alert on HMAC verification failures (indicates tampering attempt)
- Cross-cluster identity token verification for inter-cluster workload communication

---

## 8. Open Questions

1. **How to handle init containers that need platform access before the main container starts?**
   Init containers share the same network namespace and IP as the main container. The identity proxy will resolve them using the same identity record. This is correct behavior — init containers pulling weights or configuring the environment should have the same tenant identity. If per-container differentiation is ever needed, the HMAC can be extended to include container name.

2. **Can we extend this to customer-BYO images (not built by our pipeline)?**
   This breaks the split-trust model — we can't vouch for an image we didn't build. Would need a separate attestation path (e.g., customer signs the image with a registered public key via Cosign, webhook verifies the signature, computes the HMAC, and proceeds as normal).

3. **Patent defensibility: is the HMAC-over-immutable-attributes-at-admission-time sufficiently novel?**
   Individual components (HMAC, admission webhooks, image digest verification) are well-known. The novel combination is: credentialless + image-as-identity + HMAC tamper protection + hierarchical signing + server-side-only resolution. A patent attorney should evaluate the claims against SPIFFE and Sigstore prior art specifically.

---

## 9. OIDC Federation for Cross-Cloud B2B Trust

### 9.1 Overview

The identity tokens produced by this system can serve as OIDC-compliant JWTs for cross-cloud federation. A customer configures their AWS/GCP/Azure account to trust the platform's OIDC provider, then uses IAM conditions on the `sub` claim to scope access to their tenant and model.

This enables a powerful B2B use case: the customer's own infrastructure can verify "did this request really come from my model running on this AI inference platform?" — without the platform sharing any cloud credentials.

### 9.2 OIDC Provider Endpoints

The platform hosts a **static file server** (S3 + CloudFront, or any CDN) at a public URL:

```
https://identity.platform.example.com/
  ├── .well-known/openid-configuration    ← discovery document
  └── .well-known/jwks.json               ← root public key (ONE key)
```

The discovery document:
```json
{
    "issuer": "https://identity.platform.example.com",
    "jwks_uri": "https://identity.platform.example.com/.well-known/jwks.json",
    "response_types_supported": ["id_token"],
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["ES256"],
    "claims_supported": ["iss", "sub", "aud", "exp", "iat", "jti"]
}
```

The JWKS contains only the root public key. Cluster keys are in the `x5c` cert chain in the JWT header.

### 9.3 Algorithm: ES256, Not Ed25519

AWS STS only supports RS256, RS384, RS512, ES256, ES384, ES512. **Ed25519 (EdDSA) is not supported.** ES256 (ECDSA P-256) is the common denominator across AWS, GCP, and Azure.

This changes nothing in the architecture — the hierarchical key structure, 24h cluster cert TTL, single-root-key verification, and revocation model are all algorithm-agnostic. Only the key type changes from Ed25519 to ECDSA P-256. ES256 also has **better HSM/KMS compatibility** (AWS CloudHSM, GCP Cloud KMS, Vault Transit all support P-256 natively).

### 9.4 JWT Format for Federation

```
Header:
{
    "alg": "ES256",
    "typ": "JWT",
    "kid": "cluster-us-west-2-prod-07",
    "x5c": ["<cluster-cert-PEM-base64>"]     ← signed by root CA, 24h TTL
}

Payload:
{
    "iss": "https://identity.platform.example.com",
    "sub": "tenant:acme:model:llama3-70b:v3",
    "aud": "sts.amazonaws.com",
    "exp": 1710346500,
    "iat": 1710345600,
    "jti": "a1b2c3d4-unique-id",
    "image_digest": "sha256:abc123def...",    ← custom claim (app-level, not for IAM)
    "pod_uid": "a1b2c3d4-e5f6-...",           ← custom claim
    "cluster": "us-west-2-prod-07"            ← custom claim
}
```

The `sub` claim format `tenant:<id>:model:<id>:<version>` is designed for IAM policy wildcards:
- All models from a tenant: `"identity.platform.example.com:sub": "tenant:acme:*"`
- Specific model, any version: `"identity.platform.example.com:sub": "tenant:acme:model:llama3-70b:*"`
- Specific version: `"identity.platform.example.com:sub": "tenant:acme:model:llama3-70b:v3"`

Note: AWS IAM trust policies can only condition on `sub` and `aud`. Custom claims (`image_digest`, `pod_uid`, `cluster`) are useful for application-level verification and audit but ignored by AWS IAM conditions. GCP and Azure do support custom claim conditions.

### 9.5 Deployment Model: Platform-Mediated vs. Pod-Held Token

Two deployment options exist depending on platform design:

**Option A: Platform-mediated (credentialless end-to-end)**
The identity proxy holds the JWT and mediates all access. For cloud federation, the proxy or a backend service calls `sts:AssumeRoleWithWebIdentity`, obtains temporary cloud credentials, and performs the cloud API call on behalf of the pod. The pod never holds any token. This preserves the full credentialless property.

**Option B: Pod-held token**
The identity proxy returns the JWT to the platform SDK in the pod. The SDK uses the JWT to federate directly with the customer's cloud account. This is simpler but places a credential inside the pod. **Risk**: a hostile tenant with root can extract the JWT and exfiltrate it (e.g., via reverse shell), enabling external impersonation until the token expires (15 min). If continuous exfiltration is set up, fresh tokens can be funneled externally. Use Option B only when the operational simplicity justifies the token-exposure risk, and consider reducing JWT TTL to 5 minutes in this mode.

Both options are valid depending on platform requirements. Option A is the strongest security posture; Option B is simpler when the model code needs direct cloud access (e.g., streaming large datasets from customer S3 during inference).

### 9.6 Why Our JWT vs. Kubernetes SA Token for Federation

If the JWT is returned to the pod (Option B), one might ask: why not just use the K8s projected SA token for OIDC federation (as EKS IRSA and GKE Workload Identity do)?

| | K8s SA Token | Our JWT |
|---|---|---|
| Issuer (`iss`) | K8s cluster OIDC URL (e.g., `https://oidc.eks.us-west-2.amazonaws.com/id/ABC123`) — **reveals cloud provider, region, and cluster fingerprint** | `https://identity.platform.example.com` — **reveals nothing about infrastructure** |
| Subject (`sub`) | `system:serviceaccount:namespace:sa-name` — **exposes K8s namespace and SA naming** | `tenant:acme:model:llama3-70b:v3` — **pure business identity** |
| Custom claims | None. K8s projected tokens have fixed claims. | Full control: image digest, pod UID, cluster, version |
| What a stolen token can do | Call K8s API server (TokenReview reveals namespace, SA, cluster metadata). Potentially federate with cloud IAM if IRSA/GKE WI is configured. | Federate with the specific customer's cloud account for that tenant/model only. Cannot call K8s API. |
| Infrastructure leakage | Cluster OIDC endpoint URL reveals: which cloud (AWS/GCP), which region, cluster ID | Zero. `iss` is a generic platform URL. |
| K8s API discovery | Even denied API calls reveal information ("namespace X exists") | No K8s API interaction possible |
| Claim control | Platform operator cannot add custom claims to projected SA tokens | Platform operator fully controls all claims |
| Scope | Cluster-scoped (namespace + SA) | Tenant/model-scoped (business identity) |
| Revocation | Tied to SA lifecycle and cluster OIDC signing key | Per-cluster cert with 24h TTL + deny list |

The key differences are **infrastructure opacity** and **claim control**. K8s SA tokens leak cluster topology to the tenant. Our JWT is a clean business-identity token that reveals nothing about the underlying infrastructure. For a multi-tenant AI inference platform running on shared clusters across multiple cloud providers, this opacity is a security requirement — tenants should not know (or be able to discover) details about the platform's infrastructure.

---

## 10. Key Differentiator: "Not Granting Identity to the Pod"

Most workload identity systems follow the pattern:

```
Attest workload → Issue credential → Workload holds credential → Workload presents credential
```

Our system inverts this:

```
Platform derives identity server-side → Pod never knows → Platform attaches identity on behalf of pod
```

This is fundamentally different from SPIFFE, Istio, cloud workload identity, and every major system in the space. They all answer: **"How do we grant the pod an identity it can use?"** We answer: **"How do we know who the pod is without ever telling the pod?"**
