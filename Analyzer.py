# -*- coding: utf-8 -*-
# @Time    : 2019/11/18 13:16
# @Author  : PeterV
# @FileName: Analyzer.py
# @Software: PyCharm

from Lexical_Analyzer import Lexical_Analyzer,loadData
import pandas
import copy
import os
import re
import logging
from Token import Token
import pandas as pd

logging.basicConfig(level=logging.INFO)

def generate_tokens(sentence):
	for i in range(len(sentence)):
		yield i,sentence[i]


class Syntactic_Analyzer:
	def __init__(self,result_path,lexical_analyzer,is_semantic_parse):
		self.is_semantic_parse = is_semantic_parse
		self.lexical_analyzer = lexical_analyzer
		self.supported_syntax  = ['.','+','-','*','/','=','([1-9]\d*)|[0-9]','(_|[a-z]|[A-Z]|$)\w*','(',')']
		self.supported_syntax_code = []
		self.result_path = result_path
		for item in self.supported_syntax:
			self.supported_syntax_code.append(self.lexical_analyzer.getWordCode(item))
		self.word2code = {x:y for x,y in zip(self.supported_syntax,self.supported_syntax_code)}
		self.code2word = {y:x for x,y in zip(self.supported_syntax,self.supported_syntax_code)}
		self.error_recorder = []
		self.all_semantic_results = []
		self.results = []

	def fit(self,text):
		tokens = []
		for sentence in text:
			tmp_list = []
			for item in sentence:
				tmp_list.append(Token(list(item.keys())[0],list(item.values())[0]))
			tokens.append(tmp_list)
		self.index = 0
		for index,sentence in enumerate(tokens):
			self.semantic_results = []
			self.temporal_index = 1
			self.index = index + 1
			self.expr_variable = None
			self.variable = None
			self.results.append(self.__parse(sentence))
			while self.progress < self.sen_len:
				self.error_recorder.append("Syntax error in " + str(self.index) + " line:\n" +
										   "Unexpected token : " + self.next_tok.word)
				self.__advance()
			if self.variable is not None:
				self.semantic_results.append(str(self.variable) + ' = '+self.semantic_results[-1].split('=')[0].strip())
			self.all_semantic_results.append(self.semantic_results)
		self.__storeErrorInExcel()

	def __parse(self,sentence):
		self.sen_len = len(sentence)
		self.tokens = generate_tokens(sentence)
		self.cur_tok = None
		self.next_tok = None
		self.__advance()
		# print(self.next_tok.word)

		return self.__analyze()

	def __analyze(self):
		if self.__accept(self.word2code['(_|[a-z]|[A-Z]|$)\w*']):
			self.variable = self.next_tok.word
			self.__advance()
		else:
			self.__advance()
			self.error_recorder.append("Syntax error in " + str(self.index) + " line:\n" +
									   "Expect Variable but received: " + self.next_tok.word)
		self.__expect(self.word2code['='])

		return self.__statement()

	def __statement(self):
		# if self.next_tok.code in self.supported_syntax_code:
		# 	self.__advance()
		# else:
		# 	self.error_recorder.append("Syntax error in " + str(self.index) + " line:\n" +
		# 							   "Unsupported token type: " + self.next_tok.word)
		# 	self.__advance()
		exprval,self.expr_variable = self.__expr()

	def __expr(self):
		exprval = self.__term()
		semantic_string = str(exprval)
		# print('expr '+ self.next_tok.word)
		while self.__accept(self.word2code['+']) or self.__accept(self.word2code['-']):
			# print('+')
			# if not self.__advance():
			# 	break
			self.__advance()
			opt = self.cur_tok.code
			right = self.__term()
			if opt==self.word2code['+']:
				if is_semantic_parse:
					# if term_address_left is None and term_address_right is None:
					# 	semantic_string = 't'+str(self.temporal_index)+' = ' + str(exprval) + ' + ' + str(right)
					# elif term_address_left is None:
					# 	semantic_string = 't'+str(self.temporal_index)+' = ' + str(exprval) + ' + ' + str(term_address_right)
					# elif term_address_right is None:
					# 	semantic_string = 't'+str(self.temporal_index)+' = ' + str(term_address_left) + ' + ' + str(right)
					# else:
					if  self.expr_variable is None:
						semantic_string = 't'+str(self.temporal_index)+' = ' + str(exprval) + ' + ' + str(
						right)
					elif self.expr_variable is not None:
						# print(self.temporal_index)
						# print(self.semantic_results)
						semantic_string = 't' + str(self.temporal_index) + ' = ' + \
										  str(exprval) + ' + ' + \
								str(right)
						self.expr_variable = None
					self.temporal_index += 1
					exprval = semantic_string.split('=')[0].strip()
					# self.semantic_results.append(semantic_string)
				# print(right)
				# if type(right) is int and type(exprval) is int:
				# 	print(right)
				# 	print(exprval)
					# exprval += right
			elif opt==self.word2code['-']:
				if is_semantic_parse:
					if self.temporal_index == 0:
						semantic_string = 't' + str(self.temporal_index) + ' = ' + str(exprval) + ' - ' + str(
							right)
					else:
						semantic_string = 't' + str(self.temporal_index) + ' = ' + str(exprval) + ' - ' + str(
							right)
					self.temporal_index += 1
					exprval = semantic_string.split('=')[0].strip()
				# exprval -=right
			self.expr_variable = semantic_string.split('=')[0].strip()
			self.semantic_results.append(semantic_string)
		# self.__advance()
		return exprval,semantic_string.split('=')[0].strip()

	def __term(self):
		termval = self.__factor()
		semantic_string = str(termval)
		while self.__accept(self.word2code['*']) or self.__accept(self.word2code['/']):
			# print('*')
			# if not self.__advance():
			# 	break
			self.__advance()
			opt = self.cur_tok.code
			right = self.__factor()
			if opt==self.word2code['*']:
				# print(termval)
				if is_semantic_parse:
					if self.expr_variable is None:
						semantic_string = 't'+str(self.temporal_index)+' = ' + str(termval) + ' * ' + str(right)
					else:
						semantic_string = 't'+str(self.temporal_index)+' = ' + str(termval) + ' * ' + str(right)
						self.expr_variable = None
					self.temporal_index += 1
					self.semantic_results.append(semantic_string)
					termval = semantic_string.split('=')[0].strip()
				# print(termval)
			elif opt==self.word2code['/']:
				if is_semantic_parse:
					if self.expr_variable is None:
						semantic_string = 't'+str(self.temporal_index)+' = ' + str(termval) + ' / ' + str(right)
					else:
						semantic_string = 't' + str(self.temporal_index) + ' = ' +str(termval) + ' / ' +str(right)
						self.expr_variable = None
					self.temporal_index += 1
					self.semantic_results.append(semantic_string)
					termval = semantic_string.split('=')[0].strip()

		# self.__advance()
		# print('return')
		# print(termval)
		# return termval,semantic_string.split('=')[0].strip()
		return termval


	def __factor(self):
		# print(self.next_tok.word)
		# print(self.word2code['('])
		if self.__accept(self.word2code['(_|[a-z]|[A-Z]|$)\w*']):
			self.__advance()
			return self.cur_tok.word
		elif self.__accept(self.word2code['([1-9]\d*)|[0-9]']):
			self.__advance()
			return int(self.cur_tok.word)
		elif self.__accept(self.word2code['(']):
			self.__advance()
			# print('(((((')
			# print(self.cur_tok)
			exprval,self.expr_variable = self.__expr()
			self.__expect(self.word2code[')'])
			return self.expr_variable
		else:
			# print('error in __factor')
			self.error_recorder.append("Syntax error in " + str(self.index) + " line: \n "+
									" Expect \"Variable\" \"Number\" or \"(\" but received: " + self.next_tok.word)
			if not self.__advance():
				return False
			return self.__statement()

	def __advance(self):
		'''
		advance the token
		'''
		try:
			self.cur_tok,tuple_next = self.next_tok,next(self.tokens)
			self.progress, self.next_tok = tuple_next
			return True
		except StopIteration:
			self.cur_tok,tuple_next = self.next_tok,(self.sen_len,Token('None','-1'))
			self.progress, self.next_tok = tuple_next
			return False
			# self.next_tok = Token('None','-1')



	def __accept(self,acc_type):
		if self.next_tok and self.next_tok.code == acc_type:
			return True
		else:
			return False

	def __expect(self,acc_type):
		if not self.__accept(acc_type):
			# print('error in __expect')
			self.error_recorder.append("Syntax error in " + str(self.index) + " line:\n"
									   +"Expected {} but received {}".format(str(self.code2word[acc_type]),self.next_tok.word))
			self.__advance()
		else:
			self.__advance()


	def __storeErrorInExcel(self):
		df = pd.DataFrame()
		writer = pd.ExcelWriter(self.result_path)
		error_list = []
		for item in self.error_recorder:
			error_list.append(item)
		df['error'] = error_list
		df = df[['error']]
		df.to_excel(writer,sheet_name='error_recorder')
		df = pd.DataFrame()
		results_recorder = []
		line_index = 1
		for item in self.all_semantic_results:
			results_recorder.append("line " + str(line_index) + " : \n")
			for address in item:
				results_recorder.append(address)
		df['results'] = results_recorder
		df = df[['results']]
		df.to_excel(writer,sheet_name='results')
		writer.save()

if __name__ == '__main__':
	is_semantic_parse = True
	lexical_analyzer = Lexical_Analyzer('wordCode.xlsx','result.xlsx')
	data_list = loadData('data_expr.txt')
	data_list = lexical_analyzer.convertSentecesToWordCode(data_list)
	syntax_analyzer = Syntactic_Analyzer('SyntaxAndSemanticResults.xlsx',lexical_analyzer,is_semantic_parse)
	syntax_analyzer.fit(data_list)
	for error in syntax_analyzer.error_recorder:
		logging.error(error)
	# logging.info('results: ' + str(syntax_analyzer.results))
	for item in syntax_analyzer.all_semantic_results:
		logging.info(str(item))
