---
title: "A Technical Path for Confidential Compute with GPU Inference"
date: 2026-03-04
draft: false
tags: ["confidential-computing", "gpu", "security", "machine-learning", "nvidia"]
---

# A Technical Path for Confidential Compute with GPU Inference

**Protecting Model Weights on Multi-Tenant GPU Infrastructure**

---

## 1. Problem

Inference vendors deploy model containers across multiple neocloud GPU providers. Organizations push model code to deploy — the vendor handles everything after. Enterprises with proprietary models need guarantees that their weights cannot be accessed by vendor operators or neocloud administrators. Today, weights exist as plaintext in GPU VRAM and host RAM during inference. This post explores a **Confidential Inference** architecture to close that gap.

---

## 2. Threat Model

**Threat 1: Rogue vendor employee.** Privileged operator accesses weights via host OS, hypervisor, or driver stack. Mitigated by model-owner-controlled attestation (NRAS hardware root of trust) and model-owner-managed KMS — the vendor never touches attestation or decryption keys.

**Threat 2: Compromised neocloud host.** Neocloud admin reads GPU memory. Mitigated by NVIDIA CC mode hardware VRAM encryption.

**Threat 3: Co-tenant on shared GPU.** Dedicated GPU allocation + CC mode hardware memory isolation.

**Threat 4: Attestation token replay.** Attacker intercepts valid NRAS JWT and replays before expiry. Mitigated by single-use, time-limited nonce binding (see Section 4.6).

**Threat 5: Weight lifecycle exposure.** Weights encrypted end-to-end: AES-256-GCM at rest (model-owner KMS-wrapped DEK), TLS in transit (plaintext DEK only within the organization's own infra), hardened C/Rust native extension for decryption and VRAM loading in host memory (see Section 6.3), NVIDIA CC hardware encryption in GPU memory.

**Out of scope:** Model code exfiltrating weights. NVIDIA firmware supply chain (deferred to NVIDIA attestation chain). Denial of service.

**In summary:** the model owner expects that weights are encrypted at every stage of the lifecycle, that GPU attestation is rooted in hardware and verified by the organization's own code, that KMS keys never leave the organization's control, and that the inference vendor has zero ability to decrypt weights or bypass attestation — even with full infrastructure access.

### 2.1 Threat Layers and Scope

Confidential AI has three distinct protection layers. Each requires progressively more hardware and infrastructure. This analysis addresses Layer 1 fully, and Layer 2 and 3 where the infrastructure supports it.

**Layer 1: Model Weight Protection** ← *focus of this post*

Protect proprietary weights from the inference vendor and neocloud operators. Weights encrypted at rest, in transit, and in GPU memory. The model owner controls attestation and KMS. The vendor never touches decryption keys. Requires: GPU CC (VRAM encryption + NRAS attestation) + hardened native SDK (Section 6.3).

**Layer 2: Prompt and Response Confidentiality**

Protect user data from neocloud operators. HTTP handling, tokenization, and output generation run on the CPU — without a CPU TEE, a hypervisor-level attacker can read every prompt and response in plaintext from host RAM. Requires: CPU TEE (AMD SEV-SNP / Intel TDX) so the inference process runs in encrypted memory invisible to the hypervisor.

**Layer 3: Full Application Integrity + Transit Protection**

Protect the inference server binary from runtime tampering, and encrypt data flowing between CPU and GPU. Without PCIe IDE, a physical or hypervisor-level attacker can observe tokens and activations crossing the PCIe bus. Requires: CPU TEE + GPU TEE + PCIe IDE/TDISP (full CC-On mode). See Section 9.5.

**Where this analysis sits:**

| Layer | What's protected | Hardware required | Coverage |
|---|---|---|---|
| 1 | Model weights | GPU CC + hardened SDK | **Fully addressed** |
| 2 | Prompts, responses | CPU TEE | Addressed on CC-On nodes; not protected on GPU-only CC nodes |
| 3 | App integrity, PCIe transit | CPU TEE + PCIe IDE | Addressed on CC-On nodes; not protected on GPU-only CC nodes |

Layer 1 is the deal-blocker for enterprise model owners today. Layers 2 and 3 are automatically covered when workloads are scheduled onto full CC-On infrastructure (Section 2.2) — no SDK or architecture changes needed, only hardware availability.

### 2.2 NVIDIA Confidential Computing Modes

NVIDIA's Confidential Computing has two distinct modes. This design must be understood in the context of which mode is available on the target infrastructure:

**CC-On (Full Confidential Computing)** — requires AMD SEV-SNP or Intel TDX on the host CPU. The GPU VRAM is encrypted by the GPU memory controller, PCIe traffic between CPU and GPU is encrypted via PCIe IDE/TDISP, and the entire VM runs inside a CPU TEE. This is the full stack that NVIDIA markets as "Hopper Confidential Computing." In this mode, the CPU TEE protects the network stack, tokenization, inference server code, and attestation brokering. The GPU TEE protects weights and computation. PCIe IDE protects the bridge between them.

**CC-DevTools / CC-Off with attestation** — GPU attestation (NRAS) and VRAM encryption are available without a CPU TEE, but PCIe encryption and CPU-side memory protection are lost. The host OS and hypervisor can observe CPU memory (prompts, responses, DEK during transfer) and PCIe traffic. This mode still protects weights in GPU VRAM and provides hardware-rooted attestation, but the trust boundary ends at the GPU.

**This design operates in either mode.** On infrastructure with full CC-On (CPU TEE + GPU TEE), the design provides end-to-end confidential inference. On infrastructure with only GPU attestation and VRAM encryption (no CPU TEE), the design still protects model weights — which is the primary enterprise concern — but prompts, responses, and application integrity are not protected.

---

## 3. Pre-Assumptions

- **GPU CC mode enabled.** Requires NVIDIA H100 or B200 with Confidential Computing firmware. On infrastructure with AMD SEV-SNP or Intel TDX, full CC-On mode provides CPU TEE + GPU TEE + PCIe IDE (see Section 2.2). On infrastructure without a CPU TEE, GPU attestation and VRAM encryption are still available but CPU-side memory and PCIe traffic are unprotected. This design works in either mode — full CC-On provides end-to-end confidential inference; GPU-only CC still protects model weights. The vendor maintains a registry of CC-capable nodes and their CC tier (full vs. GPU-only) across neocloud partners.
- **Dedicated GPU, no MIG.** CC mode and MIG cannot coexist. Confidential Inference workloads get a dedicated GPU at premium pricing.
- **Organization-managed KMS.** The model owner must have a KMS key (AWS KMS, GCP KMS, or Azure Key Vault). The vendor never holds the organization's encryption key.
- **Modified model code.** The model owner adds ~10 lines of attestation and decryption logic to their model's `load()` method using a confidential compute SDK. This is the core security guarantee — the organization's own code drives attestation verification and key release, not the vendor's infrastructure.
- **NRAS dependency accepted.** The model owner is willing to rely on NVIDIA's Remote Attestation Service (NRAS) as the root of trust for GPU attestation. NRAS availability directly affects model startup — if NRAS is unreachable, weights cannot be decrypted. SDK mitigates with JWT caching within TTL (default 1 hour) and retry with backoff.
- **Organization operates a KMS bridge.** For zero-trust credential isolation (Options B/C), the model owner either deploys a lightweight attestation broker (Lambda/Cloud Run) in their own cloud account, or has an existing HashiCorp Vault instance configured with JWT Auth. This bridge verifies NRAS attestation and releases decryption keys without any credential touching the vendor's infrastructure.

---

## 4. Usage Experience

### 4.1 The Confidential Compute SDK

The inference vendor provides a small, open-source Python SDK that the model owner adds to their model package. The SDK does three things: collect GPU attestation evidence, verify it against NVIDIA NRAS, and decrypt weights via the organization's KMS. The organization's own code drives the entire flow.

The SDK is intentionally thin (~200 lines of core logic) so organizations can audit it in minutes. It is published on PyPI, source available on GitHub, and independently auditable.

### 4.2 Configuration

The SDK supports three authentication modes. The model owner chooses based on their security posture.

**Option A: Direct KMS (simplest — vendor holds scoped credential)**

```yaml
# config.yaml
confidential:
  enabled: true
requirements:
  - cc-sdk
secrets:
  cc_kms_key_id: null          # organization's KMS key ARN
  cc_kms_credential: null      # scoped IAM role credential
```

```python
# model/model.py
from cc_sdk import ConfidentialModel

class Model:
    def __init__(self, **kwargs):
        self._secrets = kwargs["secrets"]
        self._data_dir = kwargs["data_dir"]
        self._cc = ConfidentialModel(
            key_provider="aws_kms",
            kms_key_id=self._secrets["cc_kms_key_id"],
            kms_credential=self._secrets["cc_kms_credential"],
        )

    def load(self):
        attestation = self._cc.attest()
        assert attestation.success
        assert attestation.cc_mode == True
        assert attestation.secure_boot == True

        self._cc.decrypt_weights(self._data_dir)
        self._model = load_model(self._data_dir)

    def predict(self, model_input):
        return self._model(model_input)
```

**Option B: Self-Hosted Attestation Broker (zero vendor credentials)**

```yaml
# config.yaml
confidential:
  enabled: true
requirements:
  - cc-sdk
secrets:
  cc_broker_url: null          # organization's broker endpoint
```

```python
# model/model.py
from cc_sdk import ConfidentialModel

class Model:
    def __init__(self, **kwargs):
        self._secrets = kwargs["secrets"]
        self._data_dir = kwargs["data_dir"]
        self._cc = ConfidentialModel(
            key_provider="broker",
            broker_url=self._secrets["cc_broker_url"],
        )

    def load(self):
        # 1. Request nonce from the organization's broker
        nonce = self._cc.request_nonce()

        # 2. Attest GPU with nonce bound into evidence
        attestation = self._cc.attest(nonce=nonce)
        assert attestation.success
        assert attestation.cc_mode == True
        assert attestation.secure_boot == True

        # 3. Send NRAS JWT to broker → broker verifies,
        #    calls its own KMS, returns plaintext DEK
        self._cc.decrypt_weights(self._data_dir, attestation=attestation)
        self._model = load_model(self._data_dir)

    def predict(self, model_input):
        return self._model(model_input)
```

**Option C: HashiCorp Vault (no OIDC needed, no broker needed)**

```yaml
# config.yaml
confidential:
  enabled: true
requirements:
  - cc-sdk
secrets:
  cc_vault_url: null           # organization's Vault address
  cc_vault_role: null          # Vault JWT auth role name
```

```python
# model/model.py
from cc_sdk import ConfidentialModel

class Model:
    def __init__(self, **kwargs):
        self._secrets = kwargs["secrets"]
        self._data_dir = kwargs["data_dir"]
        self._cc = ConfidentialModel(
            key_provider="vault",
            vault_url=self._secrets["cc_vault_url"],
            vault_role=self._secrets["cc_vault_role"],
        )

    def load(self):
        attestation = self._cc.attest()
        assert attestation.success
        assert attestation.cc_mode == True

        # NRAS JWT sent to Vault JWT Auth → Vault verifies
        # against NVIDIA JWKS (no OIDC discovery needed)
        # → issues Vault token → SDK reads encrypted DEK
        self._cc.decrypt_weights(self._data_dir, attestation=attestation)
        self._model = load_model(self._data_dir)

    def predict(self, model_input):
        return self._model(model_input)
```

### 4.3 One-Time Setup (Per Organization)

**Option A — Direct KMS:** The model owner creates a scoped IAM role restricted to `kms:Decrypt` on a single key. Stores credential in vendor secrets. See Section 5.3 for trust implications.

**Option B — Attestation Broker:** The model owner deploys a Lambda function (a Terraform/CloudFormation template can be provided). The Lambda verifies NRAS JWTs using NVIDIA's JWKS, validates nonces, and calls KMS with native IAM permissions. No credentials leave the organization's account. ~50 lines of code.

**Option C — HashiCorp Vault:** The model owner configures a [JWT Auth backend](https://developer.hashicorp.com/vault/docs/auth/jwt) pointing to NVIDIA's JWKS URL (`https://nras.attestation.nvidia.com/.well-known/jwks.json`). No OIDC discovery endpoint required — Vault accepts a direct JWKS URI. Creates a role that maps NRAS JWT claims to a Vault policy granting `transit/decrypt` or `kv/read` on the encrypted DEK.

### 4.4 Deploy

```bash
model push --confidential
```

Same command as a standard deployment. The `confidential.enabled: true` flag tells the scheduler to route to a CC-enabled GPU node.

### 4.5 Envelope Encryption

Model weights can be gigabytes. KMS has a 4KB payload limit and charges per API call. Sending raw weights to KMS is infeasible. Instead, the system uses **envelope encryption**:

**At build time (model push):**

1. Generate a random 256-bit Data Encryption Key (DEK).
2. Encrypt model weights locally using AES-256-GCM with the DEK.
3. Send only the DEK to the organization's KMS to be encrypted (wrapped).
4. Store the encrypted DEK alongside the encrypted weights in the vendor's storage.

**At runtime (`load()`):**

1. SDK sends the encrypted DEK (~256 bytes) to KMS (or broker). KMS returns the plaintext DEK.
2. SDK uses the plaintext DEK to decrypt weights directly into GPU VRAM.
3. SDK zeroes the plaintext DEK and host RAM immediately after GPU load.

This means KMS handles only a tiny key, not gigabytes of model data.

### 4.6 Runtime Flow

The SDK supports two authentication modes depending on the organization's security posture. Both use envelope encryption and nonce-bound attestation.

**Option A: Direct KMS (Tier 1 — simplest, vendor holds scoped credential)**

```
Model owner's model.py load()
using cc-sdk:

  1. cc.attest()
     → NVML collects GPU evidence
     → Sends to NRAS
     → Verifies JWT signature (ES384)
       against NVIDIA JWKS
     → Returns validated claims

  2. Model owner asserts claims
     (their code, their rules)

  3. cc.decrypt_weights(data_dir)
     → Uses scoped IAM credential (from vendor secrets)
     → Sends encrypted DEK to KMS → receives plaintext DEK
     → Decrypts weights with DEK → loads to VRAM
     → Zeroes DEK + host RAM
```

**Option B: Self-Hosted Attestation Broker (Tier 2 — zero vendor credentials)**

```
Organization's AWS Account              Vendor Pod
─────────────────────                   ──────────

                                        load():
                                          │
  Broker (Lambda/API GW)  ◄───────────  1. SDK requests nonce
  generates nonce,                         from organization's broker
  stores with short TTL   ────────────► 2. SDK receives nonce
  (DynamoDB, 30s expiry)

                                        3. cc.attest(nonce=nonce)
                                           → Passes nonce to NVML
                                             evidence collection
                                           → Nonce bound into GPU
                                             attestation report
                                           → NRAS signs JWT
                                             containing nonce
                                           → SDK verifies JWT

                                        4. Model owner asserts claims

  Broker  ◄──────────────────────────── 5. SDK sends NRAS JWT
  • Fetches NVIDIA JWKS                    to organization's broker
  • Verifies JWT signature
  • Checks nonce matches
    (reject if expired/reused)
  • Asserts CC claims
  • Calls own KMS Decrypt
    (native IAM — no external
     credential needed)
  • Returns plaintext DEK   ──────────► 6. SDK receives DEK
                                           → Decrypts weights → VRAM
                                           → Zeroes DEK + host RAM
```

**Option C: HashiCorp Vault (Tier 2 alt — no OIDC needed, no broker needed)**

```
Model owner's model.py load():

  1. cc.attest(nonce=vault_nonce)
     → Nonce-bound NRAS JWT

  2. Model owner asserts claims

  3. cc.decrypt_weights(data_dir, provider="vault")
     → SDK sends NRAS JWT to organization's Vault
     → Vault JWT Auth verifies against NVIDIA JWKS
       (Vault does NOT require OIDC discovery —
        only needs the jwks_uri directly)
     → Vault validates nonce claim
     → Vault issues short-lived token
     → SDK reads encrypted DEK from Vault KV
     → Decrypts weights → VRAM → zeroes RAM
```

### 4.7 Dashboard

The vendor adds a **Confidential Computing** section to the model dashboard: GPU CC mode status per node, attestation event history, and alerting on attestation failure.

---

## 5. Trust Model

### 5.1 Why the SDK Approach

The fundamental problem with any vendor-controlled component (init container, sidecar, admission controller) is that the vendor can modify it. If the vendor verifies attestation and calls KMS, the model owner is trusting the vendor not to skip verification. There is no way for the model owner to confirm this, since the vendor controls the infrastructure.

By moving attestation into the model owner's own `model.py` via an SDK:

- **The organization's own code** calls NRAS and verifies the JWT — not the vendor's infrastructure.
- **The organization's own code** holds the KMS credential and decides when to decrypt.
- **The NRAS JWT is signed by NVIDIA** (ES384) — the vendor cannot forge it.
- **The SDK is open-source** — anyone can read, audit, vendor, or modify it.

### 5.2 Trust Chain

| Step | What is verified | Who verifies | How |
|---|---|---|---|
| GPU is genuine, CC mode active | Hardware + firmware | NVIDIA NRAS | Evidence validated against golden measurements, signed JWT returned |
| NRAS JWT is authentic | JWT signature | Organization's code (via SDK) | Verified against NVIDIA's published public certificate |
| Attestation claims meet policy | CC mode, secure boot, driver version | Organization's code | Model owner writes their own assertions in `load()` |
| Key released only when attested | Decrypt timing | Organization's code | `decrypt_weights()` only called after attestation passes |
| KMS access scoped to CC role | IAM identity | Organization's KMS policy | Key policy restricts decrypt to the vendor CC role (Option A) or credential never leaves the organization's account (Options B/C) |

### 5.3 Remaining Trust Assumptions

**The model owner still trusts the vendor for:**

- **The Python runtime.** The vendor could theoretically patch the interpreter or swap the SDK at runtime. This is an extremely sophisticated attack — modifying a running process's imports. Runtime self-hash checks provide limited protection here (if the attacker controls the interpreter, they can bypass any in-process check). The real defense is supply chain: Sigstore/Fulcio signed releases, reproducible builds, and the model owner ensuring their base container image is immutable and verified before the vendor orchestrates it.
- **The GPU driver / NVML.** The vendor could theoretically spoof NVML responses. However, spoofed evidence would fail NRAS verification because the attestation report must be signed by the GPU's hardware root of trust, which the vendor cannot access.

**The model owner does NOT need to trust the vendor for:**

- Attestation verification — their code does it.
- KMS key release timing — their code controls it.
- Attestation policy — their code defines it.
- NRAS JWT integrity — NVIDIA's signature guarantees it.
- KMS credential access (Options B/C) — credential never enters vendor infrastructure.

---

## 6. Concerns, Challenges, and Attack Vectors

### 6.1 SDK Supply Chain

The model owner imports `cc-sdk` from PyPI. A compromised package could skip verification. Mitigations: the package is open-source with reproducible builds and Sigstore/Fulcio signed releases. Organizations can pin the version, vendor the source, or build from source. Note: runtime self-integrity checks (e.g., the SDK hashing its own modules at import) provide limited value — if an attacker controls the container or Python interpreter, they can bypass any in-process check. The real defense is supply chain verification before deployment, not runtime self-checks.

### 6.2 Attestation Broker Availability and Clock Skew (Option B)

The broker adds an external dependency to the model startup path. If the broker Lambda is down, `load()` fails. Mitigations: API Gateway + Lambda have high native availability, broker is stateless so horizontal scaling is automatic, SDK retries with jittered backoff.

Nonce TTL should be tuned to balance security vs. reliability. Recommended: 60–90 second TTL to accommodate clock skew between the inference pod, NRAS, and the organization's AWS environment. Distributed systems are prone to clock drift — tight TTLs (e.g., 30s) combined with NRAS API latency can trigger spurious attestation failures and container crash loops. The JWT verification logic should also include an explicit clock skew tolerance (e.g., 60 seconds on `iat`/`exp` validation).

### 6.3 Host Memory Exposure and Hardening

Without a CPU TEE (see Section 2.2), the plaintext DEK and decrypted weights briefly exist in host RAM during VRAM loading. This is the most frequently cited concern.

**How realistic is this attack?**

A root user on the host can read process memory via `/proc/<pid>/mem`, `gcore`, or `ptrace`. However, finding a 32-byte DEK in a multi-gigabyte inference server heap requires knowing the exact memory layout and timing the dump to the brief decryption window. This is not a trivial "run one command" attack — it requires specialized tooling, timing, and knowledge. A hypervisor-level attacker (neocloud admin) has stronger capabilities and can read physical pages without guest OS awareness, but this requires custom hypervisor modifications or memory forensics tools.

**The native extension hardening approach:**

The SDK's decryption path is implemented as a compiled C/Rust extension, not Python. Python's garbage collector, immutable byte objects, and reference counting make secure memory handling impossible — plaintext can linger in heap for seconds or be copied invisibly. The native extension provides deterministic control over every byte.

The following hardening primitives are applied to all memory regions that touch the plaintext DEK or decrypted weight buffers:

**`MADV_DONTDUMP`** — tells the kernel to exclude these pages from core dumps. Defeats `gcore`, `/proc/<pid>/coredump_filter`, and crash dump collection. A root user running `gcore` on the inference process gets a dump with the sensitive pages missing.

**`prctl(PR_SET_DUMPABLE, 0)`** — marks the process as non-dumpable. Prevents `ptrace` attach and `/proc/<pid>/mem` reads, even from root. Note: root *can* override this via `/proc/sys/kernel/yama/ptrace_scope` or by loading a kernel module, but it blocks all standard Linux debugging tools.

**`mlock` / `mlock2`** — pins pages in physical RAM, preventing swap to disk. Without this, the kernel could write plaintext pages to swap and they'd persist on disk indefinitely.

**`explicit_bzero` / `OPENSSL_cleanse`** — zeroes memory after use in a way the compiler cannot optimize away. Standard `memset` can be elided by the compiler if it determines the buffer is unused afterward. In Rust, the `zeroize` crate with `Zeroizing<T>` provides the same guarantee integrated with Rust's ownership model — memory is zeroed on drop.

**Guard pages** — allocate read/write-protected pages immediately before and after the sensitive buffer. Any over-read or buffer overflow segfaults instead of leaking adjacent data.

**Minimal lifetime** — the native extension allocates the sensitive buffer, receives the DEK, decrypts weights directly into a GPU-bound staging buffer, initiates the DMA transfer to VRAM, zeroes both the DEK and the staging buffer, and frees the memory — all within a single function call. The plaintext exists for microseconds, not seconds.

**What this defends against:**

| Attack vector | Pure Python | Hardened C/Rust extension | CPU TEE (SEV-SNP) |
|---|---|---|---|
| `/proc/<pid>/mem` read | Exposed | Blocked (`PR_SET_DUMPABLE`) | Encrypted |
| `gcore` / core dump | Exposed | Excluded (`MADV_DONTDUMP`) | Encrypted |
| `ptrace` attach | Exposed | Blocked (`PR_SET_DUMPABLE`) | Encrypted |
| Swap to disk | Possible | Blocked (`mlock`) | Encrypted |
| Root override of `PR_SET_DUMPABLE` | N/A | Exposed (requires kernel config or custom module) | Encrypted |
| Custom kernel module reading physical pages | Exposed | Exposed | Encrypted |
| Hypervisor physical memory read | Exposed | Exposed | Encrypted |

**Honest assessment:** The hardened native extension raises the attack bar from "trivial with standard Linux tools" to "requires custom kernel modules, hypervisor access, or a microsecond-precision timing attack." It does not provide the cryptographic guarantee of a CPU TEE. For organizations that require provable host memory protection, full CC-On mode (Section 9.5) is the answer. For organizations whose primary concern is weight protection from vendor employees using standard tooling, the hardened extension is a meaningful and practical defense layer.

---

## 7. Inference Vendor Requirements

For an inference vendor to support Confidential Inference, the following capabilities are required:

### 7.1 Infrastructure

- **CC-capable GPU fleet.** Vendor must provision and maintain NVIDIA H100/B200 nodes with Confidential Computing firmware enabled. CC mode must be verifiable at the hardware level — not just a config flag.
- **Dedicated GPU scheduling.** Scheduler must route `confidential: true` workloads exclusively to CC-enabled nodes. Must never silently fall back to non-CC hardware. Fail loudly if no CC capacity is available.
- **Envelope encryption in the build pipeline.** During model push, the vendor's build pipeline generates a DEK, encrypts weights with AES-256-GCM, wraps the DEK via the organization's KMS, and stores both the encrypted weights and encrypted DEK. The vendor never sees the plaintext DEK.
- **Secret management integration.** Vendor's secret store must support organization-provided values (KMS key ARNs, broker URLs, Vault addresses) mounted into the model container at runtime.

### 7.2 SDK and Tooling

- **Confidential compute SDK.** Open-source Python library providing: NVML GPU evidence collection, nonce-bound NRAS attestation, JWT verification against NVIDIA JWKS, and multi-provider auth. The decryption and VRAM loading path must be implemented as a compiled C/Rust native extension (not pure Python) with hardened memory management: `MADV_DONTDUMP`, `PR_SET_DUMPABLE(0)`, `mlock`, `explicit_bzero`, and guard pages (see Section 6.3). Supply chain integrity via Sigstore/Fulcio signed releases and reproducible builds.
- **Multi-provider auth support.** SDK must support at minimum: direct cloud KMS (AWS/GCP/Azure), self-hosted attestation broker, and HashiCorp Vault JWT Auth.
- **Attestation broker deployment template.** Terraform and/or CloudFormation templates that organizations can deploy in their own cloud account with minimal configuration. The broker must be stateless, serverless, and handle nonce generation, NRAS JWT verification, and KMS decryption.

### 7.3 Observability

- **Attestation dashboard.** Per-model view of CC mode status, attestation event history (success/failure), and alerting on attestation failures.
- **Exportable audit logs.** Attestation events (NRAS JWT claims, timestamps, GPU identifiers) must be exportable to the organization's own SIEM/logging infrastructure.

### 7.4 Documentation

- **KMS policy templates** per cloud provider (AWS, GCP, Azure).
- **Broker deployment guide** with step-by-step instructions.
- **Vault JWT Auth configuration guide** with role and policy examples.
- **CloudTrail/audit monitoring guide** for organizations using Option A.
- **Example model.py** per authentication option (A, B, C).

---

## 8. Opportunities: Open Source and Ecosystem

The components required for GPU Confidential Inference are not vendor-specific. The attestation protocol, cryptographic verification, and KMS bridge patterns are universal to any environment running NVIDIA CC-enabled GPUs. This creates a significant opportunity to build and open-source foundational tooling that benefits the entire ecosystem.

### 8.1 Open-Source Attestation SDK

A standalone, vendor-neutral SDK for NVIDIA GPU attestation and verified weight decryption:

```
cc-attest/
├── evidence.py        # NVML GPU evidence collection
├── nras.py            # NRAS API client + JWT verification against NVIDIA JWKS
├── nonce.py           # Cryptographic nonce generation and binding
├── envelope.py        # Python wrapper around native decryption extension
├── _native/           # C/Rust extension — guarded memory, AES-256-GCM decrypt, VRAM load, secure wipe
├── providers/
│   ├── aws_kms.py     # AWS KMS envelope key unwrap
│   ├── gcp_kms.py     # GCP Cloud KMS envelope key unwrap
│   ├── azure_kv.py    # Azure Key Vault envelope key unwrap
│   ├── vault.py       # HashiCorp Vault JWT Auth + Transit/KV
│   └── broker.py      # Generic attestation broker client (nonce + JWT exchange)
└── types.py           # AttestationResult, EnvelopeKey, NonceChallenge
```

This SDK would be useful to any organization running model inference on third-party GPU infrastructure — not just tenants of a single vendor. It could become the standard client library for NVIDIA NRAS-based attestation workflows.

### 8.2 Open-Source Attestation Bridge Service

A deployable, self-contained attestation broker that organizations run in their own cloud:

```
cc-bridge/
├── handler.py         # Lambda/Cloud Run entry point
├── verify.py          # NRAS JWT verification (fetches NVIDIA JWKS, validates signature + claims)
├── nonce.py           # Nonce issuance, storage (DynamoDB/Redis), expiry enforcement
├── kms.py             # KMS Decrypt call (AWS/GCP/Azure) — runs with native IAM, no external creds
├── policy.py          # Configurable attestation policy (required claims, CC mode, secure boot, driver version)
├── terraform/
│   ├── aws/           # Lambda + API Gateway + DynamoDB for nonce store
│   └── gcp/           # Cloud Run + Firestore
├── cloudformation/
│   └── template.yaml  # One-click AWS deployment
└── README.md          # Setup guide, architecture diagram, security model
```

The bridge is ~200 lines of core logic. It verifies NRAS JWTs, enforces nonce freshness, checks attestation policy, and releases decryption keys — all running inside the organization's own cloud account with zero credentials exposed externally.

This solves the NVIDIA NRAS OIDC gap (NRAS lacks `/.well-known/openid-configuration`, so native AWS `AssumeRoleWithWebIdentity` federation is blocked). The bridge bypasses this entirely — a Lambda can verify a JWT against a JWKS URL without OIDC discovery.

### 8.3 Why Open Source

- **Trust through transparency.** The entire security model depends on organizations trusting the attestation and decryption code. Open source makes this auditable by anyone.
- **Ecosystem adoption.** A standard SDK accelerates Confidential Inference adoption across the GPU inference ecosystem, not just one vendor. More adoption pressures NVIDIA to improve NRAS (e.g., adding OIDC discovery) and cloud providers to add native NRAS support in KMS policies.
- **Community hardening.** Security-critical code benefits from broad review. Reproducible builds, signed releases, and community CVE reporting make the SDK more trustworthy over time.
- **Competitive moat through execution, not secrecy.** The value is in the infrastructure that runs Confidential Inference reliably at scale — not in the attestation library itself.

---

## 9. The North Star

### 9.1 In-GPU Decryption ("Dumb Pipe" Architecture)

The current design has one acknowledged gap: the plaintext DEK and decrypted weights briefly exist in host RAM during the GPU transfer window (seconds). The mitigations (`mlock`, immediate zeroing, no swap) reduce the window but do not eliminate it. The ideal architecture would move all decryption inside the GPU so the host CPU never sees plaintext.

**How it would work:**

1. The GPU's CC firmware generates an ephemeral keypair inside the secure enclave. The public key is embedded in the attestation report, cryptographically bound to the hardware state.
2. The organization's broker wraps the DEK to the GPU's ephemeral public key before returning it.
3. A CUDA extension (`cc_decrypt_cuda`) pushes the wrapped DEK + encrypted weights into VRAM. The GPU unwraps the DEK using its private key, then runs AES-256-GCM decryption entirely in VRAM. The plaintext never touches host memory.

This would fully close Threat 1 and Threat 5 (host memory exposure) without requiring the vendor to migrate to host-side Confidential VMs (AMD SEV-SNP / Intel TDX), which breaks standard observability and orchestration tooling.

**Why this is not feasible today:**

NVIDIA's current CC implementation (H100/B200) is a transparent memory encryption and boot-measurement engine. It does not provide a programmable secure enclave that exposes internal key generation or unwrapping APIs to user-space code. Specifically:

- The GPU memory controller performs AES encryption transparently — this is not programmable by CUDA kernels.
- The attestation report has a fixed schema for platform measurements. There is no API to generate a keypair inside the GPU's secure boundary and embed the public key in the report.
- The `nonce` field in attestation evidence can carry arbitrary user data (used today for replay prevention), but binding a public key to a nonce is different from the GPU *generating and holding* the private key inside a secure enclave.
- The GPU's CC firmware is a measurement and isolation engine, not a general-purpose HSM.

**What NVIDIA would need to add:**

- `GenerateEphemeralKeyPair()` — create an asymmetric keypair inside the GPU secure enclave, return the public key in the attestation report.
- `UnwrapKey(wrapped_dek)` — unwrap a DEK inside the enclave using the ephemeral private key, making the plaintext DEK available only within VRAM.
- Alternatively, expose AES-GCM unwrap as a secure enclave primitive that CUDA kernels can invoke.

This is analogous to the evolution of Intel SGX (sealing/unsealing APIs took years to mature) and AWS Nitro Enclaves (which expose `kms:Decrypt` inside the enclave boundary). Until NVIDIA exposes these primitives, in-GPU decryption remains a north star architecture, not a shippable design.

**Recommendation:** Track NVIDIA's CC roadmap. When enclave key generation ships, the SDK and broker architecture are already designed to adopt it — the change is internal to `cc.decrypt_weights()`, transparent to the model owner's code.

### 9.2 Offline NRAS Verification

The current design hits the NVIDIA Remote Attestation Service (NRAS) API during every pod startup. At scale, this creates a latency bottleneck and a runtime dependency on an external service.

NRAS is fundamentally a PKI. The attestation report is signed by the GPU's hardware key, chained to NVIDIA's CA. Verification requires only the certificate chain, Certificate Revocation Lists (CRLs), and Reference Integrity Manifests (RIMs) — all of which can be cached.

**The optimization:**

- Run a background job that periodically downloads NVIDIA's CRLs, RIMs, and certificate chains. Cache them in S3 or an internal Redis cluster.
- The broker (or SDK in Option A) verifies the GPU's attestation report locally using the cached collateral and standard cryptographic libraries.
- No synchronous NRAS API call during model load. Cold-start latency drops significantly.

**Trust boundary:** If the vendor caches the collateral, the vendor controls the cache — a rogue operator could serve stale CRLs (hiding a revoked GPU) or tampered RIMs. The organization's SDK or broker must always perform the actual cryptographic verification itself, not trust pre-verified results from the vendor. The vendor exposes a caching endpoint; the organization's code does the math. CRL propagation delay is also a concern — cached CRLs may not reflect recent revocations. The cache refresh interval should be tunable (recommended: hourly) with a fallback to live NRAS for high-sensitivity deployments.

### 9.3 NRAS OIDC Federation

NVIDIA NRAS currently publishes a JWKS endpoint but lacks a `/.well-known/openid-configuration` discovery document. This blocks native AWS `AssumeRoleWithWebIdentity` federation — the cleanest possible credential-free architecture where the NRAS JWT itself becomes the AWS credential.

NVIDIA would need to add one static JSON file. This would unlock direct OIDC federation for the entire GPU CC ecosystem, eliminating the need for a self-hosted broker or Vault entirely. Until then, the broker and Vault patterns bypass this gap.

### 9.4 Cloud KMS Native Attestation

The ultimate endgame: cloud KMS providers (AWS, GCP, Azure) natively validate NRAS JWT claims as key policy conditions — similar to how AWS KMS already supports Nitro Enclave attestation conditions (`kms:RecipientAttestation:PCR0`). The organization's KMS policy would enforce GPU attestation directly, with zero code and zero intermediary. This requires joint partnership between NVIDIA and cloud providers.

### 9.5 Full Stack Confidential Inference (CPU TEE + GPU TEE + PCIe IDE)

This post covers model weight protection. The complete north star is **full confidential inference** — protecting weights, prompts, responses, and application integrity simultaneously. This requires three hardware TEEs working together:

**CPU TEE (AMD SEV-SNP / Intel TDX)** — the entire VM runs inside an encrypted memory enclave. The host hypervisor cannot read or tamper with CPU memory. This protects:

- The network stack and HTTP/gRPC handling (user prompts and responses in plaintext)
- Tokenization and detokenization (prompt processing before GPU, output processing after)
- The inference server binary (vLLM, Triton, FastAPI) — cannot be tampered with at runtime
- The attestation brokering path — the CPU mediates between GPU and external KMS; without a CPU TEE, a rogue hypervisor could MITM this exchange
- The plaintext DEK during the envelope decryption window

**GPU TEE (NVIDIA CC)** — VRAM encryption protects model weights and intermediate computation. GPU attestation (NRAS) provides hardware-rooted proof of GPU identity and CC state.

**PCIe IDE / TDISP** — encrypts data flowing between CPU and GPU over the PCIe bus. Without this, a physical attacker or hypervisor with DMA access could observe tokens, activations, and weights in transit between the two TEEs.

**Why this is the north star, not the Day 1 design:**

- **Infrastructure availability.** Full CC-On mode requires AMD SEV-SNP or Intel TDX on the host CPU. Not all neocloud partners provision servers with CPU TEE support. The GPU fleet is more widely CC-capable than the CPU fleet.
- **Operational impact.** Confidential VMs break standard observability and orchestration tooling — host-level metrics, debugging, live migration, and some Kubernetes features do not work inside SEV-SNP VMs. Vendors need to rebuild their operations stack.
- **Performance overhead.** CPU TEE adds memory encryption overhead (AMD SEV-SNP: ~2-5% for compute, higher for memory-intensive workloads). PCIe IDE adds latency to every CPU-GPU transfer. For inference workloads that are GPU-bound, this may be acceptable; for workloads with heavy CPU preprocessing, the impact is measurable.
- **The primary enterprise ask today is weight protection.** Most organizations asking for Confidential Inference are protecting proprietary model weights from the vendor, not protecting end-user prompts from the neocloud. Prompt confidentiality is a separate (and valid) concern, but weight protection is the deal-blocker.

**Progression:**

| Tier | What's Protected | Hardware Required | Status |
|---|---|---|---|
| **Weight protection** (this post) | Model weights at rest, in transit, in GPU memory | GPU CC (VRAM encryption + NRAS attestation) | Shippable today on GPU-only CC nodes |
| **Weight + prompt protection** | Above + user prompts, responses, application integrity | CPU TEE + GPU CC + PCIe IDE (full CC-On) | Available where neocloud partners provision SEV-SNP/TDX hosts |
| **Zero-trust confidential inference** | Above + in-GPU decryption (no host RAM exposure at all) | CPU TEE + GPU TEE with enclave key generation + PCIe IDE | Blocked on NVIDIA exposing enclave key primitives (see 9.1) |

**Recommendation:** Ship weight protection now on GPU-only CC nodes. Expand to full CC-On as neocloud partners provision SEV-SNP/TDX infrastructure. The SDK and broker architecture are compatible with both tiers — the same model owner code works on GPU-only CC and full CC-On, with the latter providing strictly stronger guarantees.
