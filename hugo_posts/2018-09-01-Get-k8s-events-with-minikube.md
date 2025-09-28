---
title: "Get k8s events with minikube"
date: 2018-09-01
draft: false
tags: []
---

**How to use minikube [play with minikube](http://highfv.com/2017/06/17/play-k8s-with-minikube/)**

```sh
$ minikube start --cpus 2 --memory 2048 --vm-driver xhyve #create a small cluster on your mac/windows/linux
$ minikube ip #eg: 192.168.64.2
$ kubectl get no
$ kubectl create clusterrolebinding default:default:clusteradmin --clusterrole cluster-admin --serviceaccount default:default
$ export secret=`kubectl get serviceaccount default -o json | jq -r '.secrets[].name'`
$ kubectl get secret $secret -o yaml | grep "token:" | awk {'print $2'} | base64 -D > token
$ curl -v -k -H --cacert ~/.minikube/ca.crt -H "Authorization: Bearer $(cat ~/token)" "https://192.168.64.2:8443/api/v1/pods"
```

**watch and get events:**

```sh
$ curl -v -k -H --cacert ~/.minikube/ca.crt -H "Authorization: Bearer $(cat ~/token)" "https://192.168.64.2:8443/api/v1/namespaces?watch=true&resourceVersion=0"
```

**results**

{“type”:”ADDED”,”object”:{“kind”:”Namespace”,”apiVersion”:”v1”,”metadata”:{“name”:”default”,”selfLink”:”/api/v1/namespaces/default”,”uid”:”ed9909fc-8856-11e7-afe5-7a5714de8165”,”resourceVersion”:”16”,”creationTimestamp”:”2017-08-23T23:00:59Z”},”spec”:{“finalizers”:[“kubernetes”]},”status”:{“phase”:”Active”}}}

{“type”:”ADDED”,”object”:{“kind”:”Namespace”,”apiVersion”:”v1”,”metadata”:{“name”:”test”,”selfLink”:”/api/v1/namespaces/test”,”uid”:”4a97c56a-173f-11e8-a2b2-7a5714de8165”,”resourceVersion”:”423676”,”creationTimestamp”:”2018-02-21T19:42:03Z”},”spec”:{“finalizers”:[“kubernetes”]},”status”:{“phase”:”Active”}}}

{“type”:”MODIFIED”,”object”:{“kind”:”Namespace”,”apiVersion”:”v1”,”metadata”:{“name”:”test”,”selfLink”:”/api/v1/namespaces/test”,”uid”:”4a97c56a-173f-11e8-a2b2-7a5714de8165”,”resourceVersion”:”423689”,”creationTimestamp”:”2018-02-21T19:42:03Z”,”deletionTimestamp”:”2018-02-21T19:42:11Z”},”spec”:{“finalizers”:[“kubernetes”]},”status”:{“phase”:”Terminating”}}}

{“type”:”DELETED”,”object”:{“kind”:”Namespace”,”apiVersion”:”v1”,”metadata”:{“name”:”test”,”selfLink”:”/api/v1/namespaces/test”,”uid”:”4a97c56a-173f-11e8-a2b2-7a5714de8165”,”resourceVersion”:”423696”,”creationTimestamp”:”2018-02-21T19:42:03Z”,”deletionTimestamp”:”2018-02-21T19:42:11Z”},”spec”:{},”status”:{“phase”:”Terminating”}}}

refer:  
<https://github.com/kubernetes/client-go>  
<https://www.kubernetes.org.cn/1309.html>
