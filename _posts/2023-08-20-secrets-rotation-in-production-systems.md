---
layout: post
title: "The Effort to Rotate Secrets in Production Systems: Challenges and Best Practices"
date: 2023-08-20
tags: ["security", "secrets-management", "production", "devops", "rotation"]
---

Rotating secrets is an essential practice for securing information in a production environment. Yet, this process presents several challenges, particularly in complex, distributed systems. By understanding and managing these challenges, companies can enhance their security posture and mitigate risks related to compromised secrets.

## Key Challenges in Secret Rotation

### 1. Standardization of Secret Types

Different types of secrets, such as SSH keys, TLS certificates, authentication tokens, single sign-on (SSO) credentials, and JWT tokens, come with unique formats and characteristics. In the absence of standardization, automating the rotation process becomes difficult, potentially leading to inconsistencies and errors. For instance, if a username has a secret path like `mysecret.username`, and a password has `mysecret-credential.password`, you must know that these secrets are related and should be rotated together.

### 2. Knowing How to Obtain New Secret Values

Creating new secret values demands varied approaches depending on the secret type and associated resources. For instance:

- **For MySQL passwords**, you need to know where the internal MySQL password generation occurs to create a new password.
- **For AWS accounts**, having the AWS account number enables the general creation of new secret values.
- **For cryptographic keys**, knowledge of the Key Encryption Key (KEK) is necessary to regenerate a Data Encryption Key (DEK).

### 3. Knowing When to Decommission Secrets

Old secrets remaining in a system present a security risk, but decommissioning them can be challenging due to several factors:

- The secret's usage or ownership might be unclear, especially if the creator has left the company.
- The secret might still be used by a deprecated service or shared with another service.
- There may be no auditing mechanism to check if a secret has been fetched or used within a certain timeframe.

Ideally, secrets associated with non-existing resources, such as AWS resources, should be confidently deleted based on auditing data.

### 4. Separating User/Machine-related Secrets from Production Secrets

It's crucial to distinguish between secrets used for user or machine authentication and those used in production systems. Users may set secrets with limited timeframes for testing or verification. Managing these temporary secrets separately from production secrets prevents accidental exposure or misuse.

### 5. Minimizing the Use of Secrets in Production Systems

In some cases, it may be possible to avoid using secrets altogether in production systems. Various alternative methods can be employed for secure authentication and authorization:

- **For single-tenant systems**, mutual TLS (mTLS) combined with simple authorization mechanisms offer secure access.
- **For cloud environments**, authentication federation allows users to access cloud resources using their existing identities.
- **For SaaS applications**, the federation provides secure access without additional secrets.
- **For workloads**, adding workload identity aids in securely identifying and authenticating applications.

### 6. Using Historical Auditing Data for Delegation and Mitigation

Historical auditing data can help to track and understand the usage patterns of secrets. It allows organizations to delegate secret management more effectively and aids in addressing any potential issues related to secret rotation or misuse.

## Conclusion

Rotating secrets is a crucial practice for maintaining a secure production environment. By addressing the challenges related to secret rotation and employing alternative authentication and authorization methods, companies can reduce the risk of compromised secrets and bolster their overall security posture.