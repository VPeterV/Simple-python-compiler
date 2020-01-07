# Simple-python-complier
A simple complier that supports parts of lexical, syntax and simple semantics of python

Update the support for semantic translation (only supporting some simple assignment statement now). For the convenience of the coding, temporally remove the return of results

Python词法分析、语法分析器，语义分析器
exe运行：
	在当前环境下有wordCode.xlsx和data_expr.txt两个文件的情况下可以直接双击运行Analyzer.exe得到Results.xlsx查看结果

源码运行：
语法分析程序集成了词法分析程序，简单语义分析器，运行语法/语义分析程序，即可以同时得到三者的结果(Result.xlsx)
程序所需文件：
		1、data_expr.txt，改变其中的内容即更改输入（支持赋值语句和If、while语句）
	  	2、种别码文件wordCode.xlsx
环境：

		1、pandas
		2、python 3 (3.5+ best)

程序运行说明：

		1、根据需要更改data_expr中的语法
		2、运行Analyzer.py文件
		3、结果会输出在控制台
		4、同时也会以Excel的形式保存在Results.xlsx中的word-code,error-recorder和semantic-result三个表中
	
	
