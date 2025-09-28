---
title: "use slice works as queue"
date: 2016-10-25
draft: false
tags: ["golang"]
---

因为project需要用到queue，翻了下go的资料。

queue的实现，可以使用list，也可以使用slice， 看到list有点啰嗦。  
尝试使用了slice，非常好用：

唯一需要注意的地方是：:= 与 ＝  
queue = append(queue, myVar)  
而不是：queue ：= append(queue, myVar)

//here is the code.

//initial a slice  
queue := make([]\*myType, 0)

// Push  
myVar:= &myType{ whatever arguments}  
queue = append(queue, myVar)

// Top (just get next element, don’t remove it)  
getOneVar := queue[0]

// pop  
queue = queue[1:]

// Is empty ?  
if len(queue) == 0 {  
 fmt.Println(“Queue is empty !”)  
}
