---
title: "play kubernetes with minikube"
date: 2017-06-17
draft: false
tags: ["k8s,minikube,kubernetes"]
---

#This document describes how to use minikube on a Mac.

Full Documentation

* Yaml:  
   <https://www.mirantis.com/blog/introduction-to-yaml-creating-a-kubernetes-deployment/>  
   Google documentation is available at:  
   <http://kubernetes.io/docs/getting-started-guides/minikube/>
* API spec: <https://kubernetes.io/docs/api-reference/v1.6/>.
* Practice: <https://imhotepio.github.io/learnk8s>, based on minikube and k8s 1.5.

#Prerequisites:  
Docker v17.04.0  
Kubernetes CLI v1.6.1

MiniKube v0.16.0  
Postgresql v9.6.2 : you may need it to follow the examples.

Install Docker:

```
brew install docker
```

verify:

```
docker version   
docker info
```

Install Kubectl:

```
brew install kubectl
```

verify:

```
kubectl version
```

**Tips:**

```
cd /usr/local/bin  
ln -s ku kubectl
```

**Install Minikube:**

```
brew install Caskroom/cask/minikube
```

**Start Minikube:**

```
brew install docker-machine-driver-xhyve
sudo chown root:wheel $(brew --prefix)/opt/docker-machine-driver-xhyve/bin/docker-machine-driver-xhyve
sudo chmod u+s $(brew --prefix)/opt/docker-machine-driver-xhyve/bin/docker-machine-driver-xhyve
```

**Start:**

```
minikube start --cpus 2 --memory 2048 --vm-driver xhyve
```

**Find IP address of Minikube**

```
   minikube ip
192.168.218.152
```

**Check the services of Minikube:**

```
minikube service list
```

**Access UI in browser**

```
minikube dashboard
Opening kubernetes dashboard in default browser...
```

**SSH to Minikube**

```
minikube ssh
```

**See Kubernetes logs**

```
minikube logs -f $POD_ID
```

**Stop Minikube**

```
minikube stop
Stopping local Kubernetes cluster...
Machine stopped.
```

##Tips before following the examples:

* get/watch information:

  ```
  kubectl get po,svc,deploy 
  kubectl get po,svc,deploy  -o wide
  kubectl get po --watch
  ```
* secrets environment value should be encoded with Base64.
* must enable heapster if you want to use auto scaling. And it will take serveral minutes to work.

  ```
  minikube addons enable heapster
  ```
* check status of the pod:

  ```
  kubectl get po
  ```
* check the log:

  ```
  kubectl logs -f POD_ID
  ```
* If deploy was used, you can not delete pod

  ```
  kubectl delete po $POD_ID"
  ```

  you should use:

  ```
  kubectl delete deploy $DEPLOY_ID
  ```

#How to use the yml file:

```
kubectl create -f $NAME.yml
kubectl delete -f $NAME.yml
```

##Example1: services and pod  
[lab\_pod.yml](https://github.com/hixichen/example-yml-for-k8s/blob/master/lab_pod.yml)  
[lab\_service.yml](https://github.com/hixichen/example-yml-for-k8s/blob/master/lab_service.yml)  
[lab\_service\_and\_pod.yml](https://github.com/hixichen/example-yml-for-k8s/blob/master/lab_service_and_pod.yml)

##Example2: secrets  
deploy sequence: secret, db  
[lab\_secrets\_secret.yml](https://github.com/hixichen/example-yml-for-k8s/blob/master/lab_secrets_secret.yml)  
[lab\_secrets\_db.yml](https://github.com/hixichen/example-yml-for-k8s/blob/master/lab_secrets_db.yml)

##Example3: auto scaling.  
 kubectl get hpa  
[lab\_auto\_scale.yml](https://github.com/hixichen/example-yml-for-k8s/blob/master/lab_auto_scale.yml)

##Example4: Probe  
[lab\_probe.yml](https://github.com/hixichen/example-yml-for-k8s/blob/master/lab_probe.yml)

##Example5: persistant volume.  
[lab\_pvc.yml](https://github.com/hixichen/example-yml-for-k8s/blob/master/lab_pvc.yml)

##Example6: UI–API–DB, a small project  
deploy sequence: db, api, ui  
[lab\_monitor\_db.yml](https://github.com/hixichen/example-yml-for-k8s/blob/master/lab_monitor_db.yml)  
[lab\_monitor\_api.yml](https://github.com/hixichen/example-yml-for-k8s/blob/master/lab_monitor_api.yml)  
[lab\_monitor\_ui.yml](https://github.com/hixichen/example-yml-for-k8s/blob/master/lab_monitor_ui.yml)
