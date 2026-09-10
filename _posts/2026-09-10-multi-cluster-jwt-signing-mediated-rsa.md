---
title: "One Key, a Hundred Clusters: Multi-Cluster JWT Signing with Mediated RSA"
date: 2026-09-10
draft: false
tags: ["security", "kubernetes", "cryptography", "jwt", "oidc", "workload-identity", "multi-cluster"]
---

# One Key, a Hundred Clusters: Multi-Cluster JWT Signing with Mediated RSA

## TL;DR

If you run a handful of Kubernetes clusters, service account tokens just work. Each cluster is its own OIDC issuer, it publishes a JWKS endpoint, and you register that issuer with your cloud provider so pods can assume IAM roles. Simple.

Somewhere past a few dozen clusters, that model quietly falls apart. This post walks through why, why the obvious fixes don't hold up, and how a 25-year-old cryptographic idea — **Mediated RSA (mRSA)** — lets hundreds of clusters issue perfectly ordinary RS256 tokens from what looks like a single key, without any one of them ever holding that key.

---

## 1. The Wall You Hit at Scale

Every Kubernetes cluster that mints its own tokens is, from the outside world's perspective, a separate identity provider with a separate public key. Cloud IAM systems need to trust each one individually. At 100+ clusters, that produces two problems at once.

**Provider quotas.** AWS IAM caps OIDC identity providers at 100 per account. GCP Workload Identity and Azure AD have their own ceilings on trusted issuers and federated credentials. Once you cross those lines, no amount of Terraform will help you — the limit is a hard one.

**Trust sprawl.** Even below the quota, every new cluster means another trust relationship to create, audit, rotate, and eventually tear down. The number of things that can be misconfigured grows linearly with your fleet, and each misconfiguration is a potential identity bug.

```
              ┌────────────────────────────────┐
              │      AWS IAM / Cloud OIDC      │
              └───────────────┬────────────────┘
                              │  hard quota: ~100 providers
        ┌──────────┬──────────┼──────────┬──────────┐
        ▼          ▼          ▼          ▼          ▼
   [Cluster 1] [Cluster 2] [Cluster 3]   ...   [Cluster 100+]
      JWKS        JWKS        JWKS                 JWKS
```

---

## 2. Why the Obvious Fixes Don't Work

Three workarounds come up in every design review. None of them survive contact with production.

### 2.1 Merge all the JWKS files into one endpoint

Publish a single `/.well-known/jwks.json` that aggregates every cluster's public key. This technically presents one issuer, but it requires a synchronization pipeline spanning every cluster. If key rotation fails in one cluster, or the aggregator lags, tokens from that cluster start failing verification everywhere.

> You've traded a quota problem for a distributed-consistency problem.

### 2.2 Embed the certificate chain in the token header

JWTs support an `x5c` header carrying a full certificate chain, so a verifier could in principle validate any cluster's key against a shared root. The catch: **AWS IAM, GCP Workload Identity, and Azure AD do not perform `x5c` verification.** They resolve the `kid` header against a JWKS endpoint and nothing else. Any design built on `x5c` is dead on arrival for cloud federation.

### 2.3 Sign everything centrally with an HSM

Give every cluster a network path to one HSM that holds the single signing key. Now you have one JWKS and one key — and one latency bottleneck on every token issuance, plus one extraordinarily attractive target. Compromise the HSM's access path and you can forge tokens for the entire fleet.

---

What we actually want is the **external simplicity** of the HSM approach (one key, one JWKS) with the **internal isolation** of the per-cluster approach (a breach in one cluster stays in that cluster). Mediated RSA delivers exactly that.

---

## 3. Mediated RSA: Splitting the Private Key

Mediated RSA comes from the **Boneh–Ding–Tsudik–Wong (BDTW)** scheme, originally designed for fast certificate revocation. The idea is disarmingly simple.

A central authority generates a standard RSA key pair — say 3072-bit, with public key `(N, e)` and private exponent `d`. Instead of handing `d` to anyone, it splits it additively:

```
d = d_A + d_C  (mod λ(N))
```

- `d_A` goes to the Kubernetes cluster.
- `d_C` stays with a central **Mediator** service (backed by Vault, an HSM, or similar).

Each cluster gets its own `d_A`, paired with its own `d_C` on the Mediator side, all derived from the same `d`. Critically, **neither party ever reconstructs `d`**. The full private exponent exists only transiently at generation time and is then discarded.

### 3.1 Signing a token

When a cluster needs to issue a JWT, it prepares the encoded message `EM` (the PKCS#1 v1.5 padded hash of the header and payload, exactly as normal RS256 would) and raises it to its share:

```
[ Cluster A  (holds d_A) ]                     [ Mediator  (holds d_C) ]
          │                                                 │
          ├── 1. s_A = EM^(d_A) mod N  ─────────────────────►│
          │      + JWT header/payload + metadata             │
          │                                                  ├── 2. Recompute EM from the payload
          │                                                  │      Check policy: is this cluster
          │                                                  │      allowed to issue these claims?
          │                                                  │
          │                                                  ├── 3. s_C = EM^(d_C) mod N
          │                                                  │
          │◄── 4. s = (s_A · s_C) mod N  ────────────────────┤
          │                                                  │
          └── 5. Emit standard RS256 JWS                     │
```

The final signature is just the product of the two partial signatures:

```
s = s_A · s_C = EM^(d_A) · EM^(d_C) = EM^(d_A + d_C) = EM^d   (mod N)
```

That last equality is the whole point. The result is **byte-for-byte a standard RS256 signature** under `(N, e)`. Any verifier — AWS STS, an Istio sidecar, a third-party API — validates it with the ordinary public key and has no idea two parties were involved.

### 3.2 Why this beats a central HSM

It looks superficially similar to the central-HSM design: the cluster still makes a network call per signature. The difference is in **what each party can do alone**.

| Party | Holds | Can it forge a token alone? |
|---|---|---|
| Cluster | `d_A` | **No** — `d_A` is a useless number without the Mediator |
| Mediator | `d_C` | **No** — it never holds `d_A` |
| Attacker with both | `d_A + d_C` | Yes — but that requires breaching two independent trust domains |

A compromised Mediator can *refuse* to co-sign, but it cannot mint tokens on a cluster's behalf. And because the Mediator sees the full payload before co-signing, it can enforce policy: refuse to sign a token claiming a namespace this cluster doesn't own, an audience it shouldn't target, or a lifetime beyond what's permitted.

---

## 4. What You Get Operationally

**One issuer, one JWKS.** Every cluster in the fleet signs under the same `(N, e)`. You register one OIDC provider with AWS, one workload identity pool with GCP, one federated credential with Azure. Quotas stop being a concern at 100 clusters, or 1,000.

**Instant, offline-proof revocation.** If Cluster A is compromised, the Mediator deletes its `d_C` share for that cluster. From that moment, Cluster A cannot produce a single valid signature — and because the attacker never had the full `d`, they can't forge tokens offline either. Compare this to conventional key compromise, where the stolen key stays valid until the JWKS is rotated everywhere and all cached copies expire.

**Zero blast radius.** Revoking Cluster A's share has no effect on Clusters B through Z. Their `d_A` shares are different, their Mediator shares are different, and nothing about the public key changes. No coordinated rotation, no JWKS republish, no cache-invalidation dance.

**Standard tooling end-to-end.** Because the output is plain RS256, nothing downstream needs to change. Existing JWT libraries, API gateways, service meshes, and cloud IAM all keep working.

---

## 5. Could You Do This with HS256 or ECDSA Instead?

RS256 isn't the only algorithm in the JWT toolbox, so it's worth asking whether the same trick generalizes.

### 5.1 HS256 (HMAC-SHA256)

You can split an HMAC key additively — `K = K_A ⊕ K_B` — and reconstruct it inside a secure enclave for signing. But HS256 is **symmetric**: every service that verifies a token must hold the full secret `K`. In a fleet with hundreds of verifiers, the first compromised downstream service hands an attacker global forgery capability. Key splitting on the signing side does nothing about that. For public, multi-party verification, HS256 is the wrong tool regardless of how you manage the key.

### 5.2 ES256 / ES384 (ECDSA)

Here the math gets in the way. RSA signing is a single modular exponentiation, and exponents add — which is exactly what makes `EM^(d_A) · EM^(d_C) = EM^d` work. ECDSA is different:

```
s = k⁻¹ · (H(m) + r · x)  (mod q)
```

Every signature needs a fresh secret nonce `k` and its modular inverse. To split the private key `x = x_A + x_B` across two parties, you also have to compute `(k_A + k_B)⁻¹` without either side learning the other's nonce share. That's a genuine multi-party computation problem, not a one-line identity.

Solutions exist — this is the same problem crypto-asset custodians solve every day:

- **Lindell's 2PC-ECDSA** uses Paillier homomorphic encryption to co-sign in 2–3 network rounds.
- **CGGMP20 / CMP** are the modern threshold ECDSA protocols used in production custody systems.
- Go implementations include [`ing-bank/threshold-signatures`](https://github.com/ing-bank/threshold-signatures), [`coinbase/kryptology`](https://github.com/coinbase/kryptology), and [`near/threshold-signatures`](https://github.com/near/threshold-signatures).

These work, but they carry zero-knowledge proofs, multi-round state machines, and a much larger surface area to get subtly wrong.

### 5.3 Ed25519 (FROST)

If you must use an elliptic curve and can choose Ed25519, the Schnorr-style structure of EdDSA makes threshold signing far simpler — **FROST** gives you single-round threshold signatures without homomorphic encryption. The trade-off is that cloud IAM support for EdDSA-signed OIDC tokens is still spotty.

### 5.4 Side by side

| Algorithm | Split-signing complexity | Verification model | Cloud IAM compatibility |
|---|---|---|---|
| **RS256 (BDTW mRSA)** | Low — one round, one modular product | Asymmetric | Universal (AWS, GCP, Azure) |
| **HS256 (HMAC)** | Low — XOR shares | Symmetric — every verifier holds the secret | Unsafe for large fleets |
| **ES256 (2PC-ECDSA)** | High — Paillier/MPC, multi-round, ZK proofs | Asymmetric | Supported via JWKS |
| **Ed25519 (FROST)** | Medium — Schnorr threshold, single round | Asymmetric | Limited |

---

## 6. Takeaways

The multi-cluster identity problem is really two problems wearing one coat: an **external** problem (cloud providers want to see one issuer) and an **internal** problem (you want a breach in one cluster to stay in one cluster). Most designs solve one at the expense of the other.

Mediated RSA solves both with a single modular addition:

- Each cluster gets a private-key share that is useless alone.
- A central Mediator co-signs after checking policy.
- The output is a stock RS256 token under one public key.

Revocation is instant and surgical, the cloud sees one trust relationship, and nothing downstream has to change.

If you're bound to RS256 by your cloud provider — and most Kubernetes fleets are — mRSA is the sweet spot: simple enough to implement and audit in an afternoon, strong enough to give you real key isolation across hundreds of clusters.
