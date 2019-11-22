# Simple_python_complier
A simple complier that supports parts of lexical and syntax of python

Python词法分析、语法分析器

词法分析程序：
程序所需文件及环境：

	1、data文件 用来存放本次分析的python语法的程序
	2、wordCode.xlsx文件里面存放有程序支持的所有字符和对应的种别码
	3、程序使用了pandas包，需要在有pandas的环境下运行此程序
  
程序运行说明：

	1、先根据需求更改data中的语法
	2、可以查看wordCode中的种别码
	3、运行程序
	4、结果会输出在控制台，同时也会以Excel的形式保存在result.xlsx中

语法分析程序：
语法分析程序集成了词法分析程序，运行语法分析程序，即可以得到词法分析的结果(result.xlsx)

程序所需文件：
		1、更改data_expr.txt中的内容，改变输入内容（当前仅支持赋值语句）
	  2、种别码如词法分析程序所示

环境：

	1、pandas

程序运行说明：

	1、根据需要更改data_expr中的语法
	2、运行Syntactic.py文件
	3、结果会输出在控制台
	4、同时也会以Excel的形式保存在error_recorder.xlsx中