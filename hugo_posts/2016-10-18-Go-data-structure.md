---
title: "Go-data_structure"
date: 2016-10-18
draft: false
tags: ["golang"]
---

10/18/2016 在夏洛特飞三番的飞机上。

一直用java刷题， 最近学习go语言，感觉就是面向过程编程的极大延伸  
希望能给用go应对常见的算法面试。

暂时尚未找到比较合适的算法库。 潜在的选择 <https://github.com/Workiva/go-datastructures>

**指针与结构体**

type Point struct{  
 X,Y int  
}

p:= Point{10,20} 结构体赋值  
pp:=&Point{10,20} 结构体指针。

**字符串**  
s:= “hello”  
temp:= s[2:3]

**slice**  
指向数组的某个片段  
x:= []int{2,3,5,7,11}  
y:= x[1:3]  
len(p)  
p[i]  
s[lo:hi] 取 s 中的下表从 lo 开始到 hi-1 结束的部分

//create a array.  
a := make([]int, 5) // len(a)=5  
b := make([]int, 0, 5) // len(b)=0, cap(b)=5  
Go和C中的数组的主要区别，在Go中，

数组是值。将一个数组赋予另一个数组将复制其所有元素。  
特别地，如果你将一个数组传递给一个函数，它将接收到该数组的一个副本， 而不是指向它的指针。  
数组的大小是其类型的一部分。类型 [10]int 和 [20]int 是不同的。

slice是Go语言的习惯用法， 数组的代价极为昂贵。

!useful one.  
append(&array, i)

import “sort”  
var keys []int  
sort.Ints(keys)

**for-rang**  
 for index, value := range pow {  
 fmt.Printf(“%d\n”, value)  
}

**new && make**  
new 返回的是类型指针。 new是一个函数， 并不是运算符， 不会对值进行赋值。  
make返回类型实体。

**map**  
var mymap map[string]mytype  
or  
var mymap map[mytype1]mytype2

!must use map to create a new object.

usage:  
mymap[key] = elem  
elem = m[key]  
delete(m,key)  
elem,ok=m[key]

visited := make(map[\*Node]bool)

One common way to protect maps is with sync.RWMutex.  
This statement declares a counter variable that is an anonymous struct containing a map and an embedded sync.RWMutex.

var counter = struct{  
 sync.RWMutex  
 m map[string]int  
}{m: make(map[string]int)}

**use heap in go**  
<https://golang.org/pkg/container/heap/>

import “container/heap”

type InitHeap []int  
Len() / Less(i,j int)/ Swap(i, j int)  
Push/Pop  
how to use:

h:=&IntHeap{2,1,5}  
heap.Init(h)  
heap.Push(h,3)  
h.Len()  
heap.Pop(h)

**PriorityQueue**

pq := make(PriorityQueue, len(items))

heap.Init(&pq)  
heap.Push(&pq, item)  
pq.update  
heap.Pop(&pq).(\*Item)  
fmt.Printf(“%.2d:%s “, item.priority, item.value)

**fibonacci**

package main

import “fmt”

// fibonacci is a function that returns  
// a function that returns an int.  
func fibonacci() func() int {  
 pre, next := 0,1  
 return func()int{  
 pre, next = next, pre+next  
 return pre  
 }  
}

func main() {  
 f := fibonacci()  
 for i := 0; i < 10; i++ {  
 fmt.Println(f())  
 }  
}  
**stack**  
type stack []int

func (s stack) Empty() bool { return len(s) == 0 }  
func (s stack) Peek() int { return s[len(s)-1] }  
func (s *stack) Put(i int) { (*s) = append((*s), i) }  
func (s* stack) Pop() int {  
 d := (*s)[len(*s)-1]  
 (*s) = (*s)[:len(*s)-1]  
 return d  
}  
*\*ring环形链表**  
import “container/ring”  
Do是一个好玩的遍历方法。

type Ring  
 func New(n int) *Ring // 初始化环  
 func (r* Ring) Do(f func(interface{})) // 循环环进行操作  
 func (r *Ring) Len() int // 环长度  
 func (r* Ring) Link(s *Ring)* Ring // 连接两个环  
 func (r *Ring) Move(n int)* Ring // 指针从当前元素开始向后移动或者向前（n可以为负数）  
 func (r *Ring) Next()* Ring // 当前元素的下个元素  
 func (r *Ring) Prev()* Ring // 当前元素的上个元素  
 func (r *Ring) Unlink(n int)* Ring // 从当前元素开始，删除n个元素

**list**  
import “container/list”  
type Element

type Element struct {

```
Value interface{}   //在元素中存储的值
```

}

func (e *Element) Next()* Element //返回该元素的下一个元素，如果没有下一个元素则返回nil  
func (e *Element) Prev()* Element//返回该元素的前一个元素，如果没有前一个元素则返回nil。  
type List  
func New() *List //返回一个初始化的list  
func (l* List) Back() *Element //获取list l的最后一个元素  
func (l* List) Front() *Element //获取list l的第一个元素  
func (l* List) Init() *List //list l初始化或者清除list l  
func (l* List) InsertAfter(v interface{}, mark *Element)* Element //在list l中元素mark之后插入一个值为v的元素，并返回该元素，如果mark不是list中元素，则list不改变。  
func (l *List) InsertBefore(v interface{}, mark* Element) *Element//在list l中元素mark之前插入一个值为v的元素，并返回该元素，如果mark不是list中元素，则list不改变。  
func (l* List) Len() int //获取list l的长度  
func (l *List) MoveAfter(e, mark* Element) //将元素e移动到元素mark之后，如果元素e或者mark不属于list l，或者e==mark，则list l不改变。  
func (l *List) MoveBefore(e, mark* Element)//将元素e移动到元素mark之前，如果元素e或者mark不属于list l，或者e==mark，则list l不改变。  
func (l *List) MoveToBack(e* Element)//将元素e移动到list l的末尾，如果e不属于list l，则list不改变。  
func (l *List) MoveToFront(e* Element)//将元素e移动到list l的首部，如果e不属于list l，则list不改变。  
func (l *List) PushBack(v interface{})* Element//在list l的末尾插入值为v的元素，并返回该元素。  
func (l *List) PushBackList(other* List)//在list l的尾部插入另外一个list，其中l和other可以相等。  
func (l *List) PushFront(v interface{})* Element//在list l的首部插入值为v的元素，并返回该元素。  
func (l *List) PushFrontList(other* List)//在list l的首部插入另外一个list，其中l和other可以相等。  
func (l *List) Remove(e* Element) interface{}//如果元素e属于list l，将其从list中删除，并返回元素e的值。

links and thanks:  
<http://ilovers.sinaapp.com/node/33>  
<https://gobyexample.com/maps>
