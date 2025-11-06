---
layout: post
title: "The Intent Collapse: Why Group-Based Access Control Systems Lose Critical Information"
date: 2025-11-05
tags: ["security", "access-control", "system-design"]
---

Groups aren't the problem. How we use them for access control is.

## The Assumption We All Make

Most organizations assume that access control is straightforward: users need permissions, groups organize users, and assigning group permissions scales efficiently. This assumption works—until it doesn't.

The assumption breaks down when:
- Organizations grow beyond 1000 people
- Groups start nesting (Engineering contains Backend, Frontend, DevOps...)
- Roles inherit permissions from multiple groups
- Permissions accumulate faster than they're removed
- People change teams but keep their old group memberships

In large organizations with nested groups and inherited roles, the problem compounds exponentially. A user in the "Backend-Team-Project-X" group inherits permissions from Backend, Engineering, and Company-Wide groups—each with their own accumulated permissions.

## The Pattern Everyone Recognizes

In every organization using Group-Based Access Control (GBAC), a predictable pattern emerges: Alice needs to deploy code to staging, so she joins the "Engineering" group. Six months later, nobody can explain why the Engineering group has access to production logs, incident management systems, and cost dashboards. The original intent—Alice's simple need to deploy to staging—has been irreversibly lost, buried under layers of group memberships and permission associations.

This isn't a minor inconvenience. It's a fundamental information collapse that makes access control systems progressively less secure, less auditable, and less maintainable over time.

## The Anatomy of Intent Loss

When a user needs access to a resource, they start with clear intent:

- "I need to deploy this feature to staging"
- "All engineers should be able to view staging logs for debugging"
- "Project Orion team needs access to these 50 documents for Q4"
- "Contractors should never touch production systems"

This intent is rich with context: **WHY** the access is needed, **WHICH** specific resources matter, **WHEN** it's needed, and **FOR HOW LONG** it should last.

But in GBAC systems, this intent gets translated into a crude approximation:

```
Intent: Alice needs to deploy to staging
Translation: Create "Engineering" group → Grant staging access → Add Alice
Result: Alice → Engineering → [staging, prod_logs, incidents, costs, ...]
```

The problem isn't the group. The problem is that **the group becomes a semantic container that loses the original intent and accumulates permissions over time.**

## The Three Dimensions of Information Loss

### 1. Context Loss: The "Why" Disappears

When you look at an access control list months later, you see:
- Engineering group → 47 permissions
- Alice → member of Engineering

What you don't see:
- Why does Engineering have permission #23?
- Why does Alice need to be in Engineering?
- Was this for a temporary project or permanent role?
- Who approved this and under what circumstances?

The GBAC system preserves the **what** but obliterates the **why**.

### 2. Scope Loss: The 1→N Explosion

Alice needs **one** permission but gets **fifty** because they're bundled in a group. This isn't a side effect—this is the **core mechanism** of information loss.

```
Original intent: Alice needs staging deployment
Implementation: Alice → Engineering group
Actual grant: Alice → [staging, prod_logs, metrics, incidents, 
                       cost_dashboards, api_keys, customer_data, ...]
```

The group was probably created for a good reason years ago. But as the organization evolved, permissions accumulated. Nobody dares remove permissions because nobody knows which ones are actually needed.

**You wanted surgical precision. You got a shotgun blast.**

### 3. Temporal Loss: Time Becomes Infinite

Intent often includes time boundaries:
- "Contractor needs access for 3-month project"
- "Intern needs limited access during summer"
- "Emergency access for this weekend's incident"

But groups are static. Once someone joins, they stay until manually removed. The temporal intent—the WHEN and FOR HOW LONG—evaporates completely.

Worse, cleanup becomes impossible because you don't know if that contractor still needs access. You only know they *have* access.

## The Group Reuse Anti-Pattern

Here's how groups become semantic garbage:

**2020:** "Engineering" group created for "developers who write code"
- Intent: Give them staging deployment access
- Members: 15 software engineers

**2025:** Same "Engineering" group now means "anyone technical"
- Members: 80 people (developers, IT support, DevOps, QA, contractors)
- Permissions: Still has all the original permissions, plus dozens more

The group name stayed the same. The membership changed. The permissions accumulated. **But nobody updated the policies because nobody remembers why they exist.**

This is the fundamental problem: **Groups lack version control for their meaning.** The semantics drift while the permissions persist.

## The Transitive Trust Problem

Groups create implicit trust relationships that nobody explicitly authorized:

```
2024: Alice (admin) creates Engineering group for staging access
2024: Alice trusts Bob → adds Bob to Engineering
2025: Bob (now manager) adds Charlie (new hire) to Engineering
Result: Charlie has staging access via transitive trust
```

Alice never made a trust decision about Charlie. Alice might have left the company. Alice might not even know Charlie exists. But Alice's original decision to create the group with certain permissions now applies to Charlie.

**Access control decisions become inherited through social networks of trust that nobody audits.**

## The Nested Group Nightmare

The transitive trust problem becomes catastrophic when you add nested groups and role inheritance—the reality in most large organizations.

Consider this common structure:

```
Company-Wide
├── Engineering
│   ├── Backend-Team
│   │   ├── Backend-Project-Alpha
│   │   └── Backend-Project-Beta
│   └── Frontend-Team
│       ├── Frontend-Mobile
│       └── Frontend-Web
└── Operations
    ├── DevOps
    └── SRE
```

When Alice joins "Backend-Project-Alpha", she inherits permissions from:
1. Backend-Project-Alpha (specific project permissions)
2. Backend-Team (team-wide permissions)
3. Engineering (all engineering permissions)
4. Company-Wide (organization-wide permissions)

Now imagine roles that inherit from multiple groups:

```
Role: "Deployment-Manager"
Inherits from: Backend-Team + DevOps + Engineering

Alice gets: Deployment-Manager role
Result: Alice inherits from 3 different group hierarchies
```

**This creates an exponential information loss problem:**

- Each group in the hierarchy lost its original intent
- Each role inheritance adds another layer of lost context
- Alice's actual needed permissions: ~5
- Alice's actual granted permissions: ~500+
- Permissions Alice knows she has: ~10
- Permissions anyone can explain: ~2

Nobody can answer: "Why does Alice have access to the customer analytics dashboard?"

The answer chain: Alice → Backend-Project-Alpha → Backend-Team → Engineering → Company-Wide → (some historical permission grant nobody remembers)

**This isn't an edge case. This is how every large organization operates.**

## Why Current Solutions Fall Short

### Direct ACLs (Zanzibar Model): Trading One Loss for Another

The obvious solution: skip groups entirely. Grant permissions directly.

```
user:alice#editor@document:staging_deploy
```

This solves the scope explosion problem—Alice only gets what she needs. But it doesn't solve the intent loss problem. The tuple `user:alice#editor@document:staging_deploy` still doesn't tell you:
- Why does Alice need this?
- Who approved it?
- How long should it last?
- What business process created this grant?

**You've traded "why the group exists" for "why this specific grant exists."** The information loss persists, just at a different granularity.

Plus, you now have scalability problems. Granting 50 engineers access to 1,000 staging resources creates 50,000 tuples. Managing this becomes a nightmare.

### Role-Based Access Control (RBAC): Better, But Still Incomplete

RBAC attempts to preserve intent by making permissions semantic:

```
user:alice → role:staging_deployer → permission:deploy@env:staging
```

This is better! The role "staging_deployer" captures some intent. But RBAC has its own challenges:

**Resource Modeling Overhead:** Every asset must be categorized into types. Your 10,000 documents need to become "document:type:design", "document:type:financial", etc. This is expensive.

**Role Explosion:** You need roles scoped to asset types. Soon you have "staging_deployer", "prod_deployer", "staging_viewer", "prod_viewer", "incident_responder_staging", "incident_responder_prod"... The role hierarchy becomes as complex as the group hierarchy you tried to escape.

**Still No Temporal Context:** Roles don't capture WHEN or WHY Alice was assigned the role.

### Attribute-Based Access Control (ABAC): Closer, But Complex

ABAC preserves more intent by encoding it in policies:

```
IF (user.department = "Engineering" 
    AND user.clearance >= 3 
    AND resource.environment = "staging"
    AND time.business_hours = true) 
THEN allow(deploy)
```

This is powerful! The policy explicitly states the conditions. But:
- **Complexity:** These policies become difficult to write, test, and debug
- **Performance:** Evaluating complex conditions at runtime has overhead
- **Migration:** Converting existing GBAC systems to ABAC is a massive undertaking

## What Actually Works: Audit Trails and Intent Preservation(JIT)

The real solution isn't choosing between groups, ACLs, roles, or attributes. It's **preserving intent at every decision point** regardless of your access control model.

### 1. Make Intent Explicit and Mandatory

Every access grant should record:
```json
{
  "grant": "alice → engineering → staging_deploy",
  "intent": "Alice joining as backend engineer, needs deployment access for feature development",
  "approver": "bob@company.com",
  "business_justification": "New hire onboarding - ticket #1234",
  "created": "2025-01-15",
  "expires": "2026-01-15",
  "review_required": true
}
```

This isn't documentation. This is **structured metadata** stored alongside the access grant itself.

### 2. Implement Temporal Boundaries by Default

All access should have expiration dates unless explicitly marked permanent. Force periodic review:
- Default: 90-day expiration
- Permanent access: Requires senior approval + quarterly attestation
- Temporary access: Auto-revoke after expiration

### 3. Track Scope Drift

When a group gains new permissions, require justification:
```
Engineering group → add cost_dashboard access
Required: "Why does Engineering need this? Which specific engineers? For what purpose?"
```

Create alerts when groups accumulate permissions beyond their original scope.

### 4. Enable Intent-Based Queries

Your access control system should answer:
- "Why does Alice have access to X?" → Return the full intent chain
- "Who has access to X for reason Y?" → Filter by intent, not just membership
- "What permissions were granted in the last 30 days and why?" → Audit trail

### 5. Implement Smart Cleanup with Intent Preservation

The "90-day unused access cleanup" approach sounds good but loses even more intent:
- **Used ≠ Needed:** One-time debugging access shouldn't become permanent
- **Unused ≠ Unnecessary:** Disaster recovery access is unused until it's critical

Instead, use **intent-driven cleanup:**
```
If (access_unused_for > 90_days AND original_intent = "temporary_project") 
   THEN notify_for_review
If (access_unused_for > 90_days AND original_intent = "disaster_recovery") 
   THEN keep_but_audit
```

## The Migration Path: You Can't Blow Up What Exists

You can't replace your entire access control system overnight. Here's a pragmatic approach:

### Phase 1: Instrument Existing Groups
Add intent metadata to new grants. Don't touch existing ones yet.
```
New group membership requires: intent + expiration + approver
Existing memberships: Continue working as-is
```

### Phase 2: Audit and Document
For critical groups, run discovery:
- Survey group members: "Why do you need this access?"
- Analyze usage logs: "What permissions are actually used?"
- Interview approvers: "What was the original intent?"

Backfill intent metadata where possible. Flag what can't be explained.

### Phase 3: Scope Reduction
For groups with clear intent violations:
- Split over-permissioned groups into focused ones
- Move to role-based or attribute-based policies for new use cases
- Maintain legacy groups but freeze their growth

### Phase 4: Active Enforcement
- Expired access auto-revokes
- Permission additions require intent justification
- Quarterly access reviews mandatory for permanent grants
- Intent-based reporting for compliance

## Is Preserving Intent Even the Right Goal?

Here's a contrarian take: **Maybe information loss is a feature, not a bug.**

Groups abstract away complexity. They let administrators think at a higher level. Too much preserved intent might create analysis paralysis—every access decision requires extensive documentation, approval chains, and review cycles.

Some information **should** be lost for operational simplicity. You don't want to track "Alice needs staging access because she's working on feature X in project Y for customer Z" if that level of detail makes access control unusable.

**But here's the counterargument:** The complexity is already there. You just hide it. When an incident happens, when an auditor asks questions, when someone leaves and you need to know what to revoke—the complexity resurfaces, except now you have no information to work with.

The question isn't "should we preserve intent?" It's "what level of intent preservation gives us security without paralysis?"

## Conclusion: Groups Aren't The Enemy

Groups are powerful abstractions. They make access control manageable at scale. The problem isn't groups—it's using groups as the **only** mechanism without preserving the intent behind access decisions.

The path forward isn't abandoning GBAC for some other model. It's **augmenting** whatever model you use with structured intent preservation:
- Explicit "why" for every grant
- Temporal boundaries for all access
- Scope monitoring to prevent permission creep
- Intent-based queries for auditing and cleanup
- Practical migration paths that don't require rip-and-replace

Information loss from intent to policy isn't inevitable. It's a design choice we've accepted for too long. We can build access control systems that remember why decisions were made, not just what those decisions were.

Your future self, debugging a security incident at 2 AM, will thank you for preserving the intent.

---

*What's your experience with intent loss in access control? Have you found strategies that work? Share your thoughts—this is a problem every organization faces but few discuss openly.*