---
title: "use python with pandas to get the skew in excel"
date: 2014-12-25
draft: false
tags: ["python"]
---

/\*

write @2014  
author: chen xi  
 \*/

use python to read the data in excel and generate the skew().

python3.3:

#this is a test case

# -*- coding: gbk -*-

print(“hello python!中文”)

#env config  
import xlrd  
import os  
import xlwt3  
import numpy

import pandas as pd

#from pandas import Series,DataFrame

#import pandas

data = xlrd.open\_workbook(“E:\data.xlsx”)  
table = data.sheets()[0] #this need to be verify more

#print (“check”)  
print (table.nrows)  
print (table.name)  
print (“############################”)

#total line num  
line\_num=table.nrows

cell\_sectionA=table.cell(1,0).value  
cell\_sectionB=table.cell(1,1).value

#print (cell\_sectionA)

#print (cell\_sectionB)

start\_value=cell\_sectionA

#we need to recode the start value ,but not the end.  
sectionB\_each\_time\_start=0

#sectionB\_each\_time\_end=i is ok.

for i in range(1,line\_num):  
 if start\_value != table.cell(i,0).value:  
 cacu\_num=i-sectionB\_each\_time\_start;

```
#print (cacu_num)
#print ("********************************")
data={}
for j in range(0,(cacu_num-1)):
    data[j]= table.cell((sectionB_each_time_start+j+1),1).value
    #print (data[j])

df = pd.Series(data)
#print("skew\t")
#print("skew: %d  %f" %(table.cell(sectionB_each_time_start+1,0).value,df.skew()))
print("%d"%table.cell(sectionB_each_time_start+1,0).value)
#print("%f" %df.skew())

#after caculate ,update the variable.
sectionB_each_time_start=i-1
start_value=table.cell(i,0).value
```

#file=xlwt3.Workbook()

#table\_for\_wt=file.add\_sheet(“test1”);

#table\_for\_wt.write(0,0,cell\_b)

#table\_for\_wt.write(1,1,cell\_b)

#file.save(‘E:\wtest.xls’)
