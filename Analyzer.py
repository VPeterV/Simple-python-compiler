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
		self.supported_syntax  = ['.','+','-','*','/','=','([1-9]\d*)|[0-9]','(_|[a-z]|[A-Z]|$)\w*',
								  '(',')','if','while','==','<','<=','>','>=',':','or','and','EOP',
								  'True','False']
		self.supported_syntax_code = []
		self.result_path = result_path
		for item in self.supported_syntax:
			self.supported_syntax_code.append(self.lexical_analyzer.getWordCode(item))
		self.word2code = {x:y for x,y in zip(self.supported_syntax,self.supported_syntax_code)}
		self.code2word = {y:x for x,y in zip(self.supported_syntax,self.supported_syntax_code)}
		self.error_recorder = []
		self.all_semantic_results = []
		self.results = []


	def fit(self,text,space_num_list):
		tokens = []
		self.space_num_list = space_num_list
		self.space_num_list.append(0)
		self.all_backfill_stack = [] #recording the line number of control stream statement
		self.addr_index = 1 #address code's index
		self.space_stack = []	#record every block's space number
		self.while_stack = []
		self.is_control_last = False	#Whether the last statement is control stream
		for sentence in text:
			tmp_list = []
			for item in sentence:
				tmp_list.append(Token(list(item.keys())[0],list(item.values())[0]))
			tokens.append(tmp_list)
		tokens.append([Token('EOP',self.word2code['EOP'])])
		self.index = 0
		for index,sentence in enumerate(tokens):
			self.semantic_results = []
			self.cur_space = self.space_num_list[index]
			self.temporal_index = 1
			self.index += 1
			self.expr_variable = None
			self.variable = None
			self.is_control_stream = False
			if index==0:
				self.last_space_num = 0
			else:
				self.last_space_num = self.space_num_list[index-1]	# a variable for Unexpected indent detection
			# self.results.append(self.__parse(sentence))
			self.__backfill()
			if not sentence[0].word == 'EOP':
				self.__parse(sentence)
			else:
				self.__advance()
			while self.progress < self.sen_len:
				self.error_recorder.append("Syntax error in code line " + str(self.index) + ':\n' +
										   "Unexpected token : " + self.next_tok.word)
				self.__advance()
			if self.variable is not None:
				self.addr_index += 1
				self.semantic_results.append(str(self.variable) + ' = '+ str(self.expr_variable))
			self.all_semantic_results.append(self.semantic_results)
		self.__backfill_EOP()
		self.__storeErrorInExcel()


	def __parse(self,sentence):
		'''

		  The begin of a parse of an expression of assignment statement
		Parse whether the first input token is a legal variable or not
		And we expect the second (next token) is '='
		Then we continue for the expression parse

		'''
		self.sen_len = len(sentence)
		self.tokens = generate_tokens(sentence)
		self.cur_tok = None
		self.next_tok = None
		self.__advance()

		#Go to the control stream module
		if self.__accept(self.word2code['if']) or self.__accept(self.word2code['while']):
			self.is_control_stream = True
			return self.__statement()

		#Go to the expression module
		if self.__accept(self.word2code['(_|[a-z]|[A-Z]|$)\w*']):
			# for judging whether the first token is legal variable
			self.variable = self.next_tok.word
			self.__advance()
		else:
			self.__advance()
			self.error_recorder.append("Syntax error in code line " + str(self.index) + ':\n' +
									   "Expect Variable or Branch statement but received: " + self.next_tok.word)
		# hope the next token is ''='
		self.__expect(self.word2code['='])

		return self.__statement()


	def __statement(self):
		'''
		'''
		#Check those statements which have unexpected indent
		if not self.is_control_stream and not self.is_control_last and self.cur_space>self.last_space_num:
			self.error_recorder.append("Syntax error in code line " + str(self.index) + ':\n' +
									   "Unexpected indent ")
		if self.__accept(self.word2code['if']) or self.__accept(self.word2code['while']):
			self.is_control_last = True
			self.__control()
		else:
			self.__backfill()
			self.is_control_last = False
			exprval,self.expr_variable = self.__expr()


	def __control(self):
		'''
		The begin of a parse for a control stream statement
		'''
		is_while = False
		if self.__accept(self.word2code['while']):
			is_while = True
		self.__advance()
		condition = self.__cond()
		self.__expect(self.word2code[':'])

		semantic_string = 'if ' + condition + ' goto ' + str(self.addr_index + 2) + ':'
		self.semantic_results.append(semantic_string)
		self.addr_index += 1
		semantic_string = 'else goto '
		self.addr_index += 1
		self.semantic_results.append(semantic_string)
		# self.cur_space = self.space_num_list[self.index]
		backfill_list = [self.index]	# all_semantic_results[backfill_list[0]][1] + str(self.addr_index)
		self.all_backfill_stack.extend(backfill_list)
		if is_while:
			self.while_stack.append({'addr_index':self.addr_index-2,'index':self.index})
		self.__control_block()



	def __control_block(self):
		'''
		A module for control_block
		Adjust the space_stack to help program judge whether the block has been OK
		'''
		if len(self.space_stack) >0:
			if self.cur_space > self.space_stack[-1]:
				self.space_stack.append(self.cur_space)
				return
		else:
			self.space_stack.append(self.cur_space)
			return

		# self.__backfill()


	def __backfill(self):
		'''
		A module for backfilling
		Use back_fill_stack and space_stack to backfill
		back_fill_stack is synchronous with space_stack
		'''
		while len(self.space_stack) > 0 and self.cur_space <= self.space_stack[-1]:
			if self.is_control_last:
				self.error_recorder.append('Syntax error in code line ' + str(self.index) + ':\n'+'Indent expected')
				self.is_control_last = False
			if len(self.while_stack)>0:
				if self.while_stack[-1]['index'] == self.all_backfill_stack[-1]:
					self.semantic_results.append('goto ' + str(self.while_stack[-1]['addr_index']))
					self.addr_index += 1
					self.while_stack.pop(-1)
			self.all_semantic_results[self.all_backfill_stack[-1]-1][-1] += str(self.addr_index)
			self.space_stack.pop(-1)
			self.all_backfill_stack.pop(-1)


	def __backfill_EOP(self):
		'''
		backfill those unfilled goto statements when the program has been over
		'''
		assert len(self.all_backfill_stack) == len(self.space_stack)

		while len(self.space_stack)>0:
			self.all_semantic_results[self.all_backfill_stack[-1] - 1][-1] += str(self.addr_index)
			self.space_stack.pop(-1)
			self.all_backfill_stack.pop(-1)
		self.all_semantic_results.append(['EOP'])


	def __cond(self):
		'''
		Parsing the condition  (including 'and' , 'or')
		'''
		left = self.__cond_term()
		cond_string = str(left)
		while self.__accept(self.word2code['and']) or self.__accept(self.word2code['or']):
			self.__advance()
			opt = self.cur_tok.word
			right = self.__cond_term()
			cond_string = str(left) + ' ' + opt +' ' + str(right)

		return cond_string


	def __cond_term(self):
		'''
		Parsing the condition  (including '<' , '<=','==','>','>=')
		'''
		cond_var = self.__factor()
		cond_term = str(cond_var)
		if self.__accept(self.word2code['<']) or self.__accept(self.word2code['<='])\
			or self.__accept(self.word2code['==']) or self.__accept(self.word2code['>'])\
			or self.__accept(self.word2code['>=']):
			self.__advance()
			opt = self.cur_tok.word
			right = self.__factor()
			cond_term = str(cond_var) + ' ' + opt + ' ' + str(right)

		return cond_term


	def __expr(self):
		'''
		expression parse

		Structure:
			left = Term()
			while +/-:
			advance() (scanner)
			right =Term()
			semantic_string = 't' + (index) + '=' left + '+/-' + right
			results.append(semantic_string)
			left = t + (index)
			repeat

		return: left

		'''
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
					if  self.expr_variable is None:
						semantic_string = 't'+str(self.temporal_index)+' = ' + str(exprval) + ' + ' + str(
						right)
					else:
						semantic_string = 't' + str(self.temporal_index) + ' = ' + \
										  str(exprval) + ' + ' + \
								str(right)
						self.expr_variable = None
					self.temporal_index += 1
					self.addr_index += 1
					exprval = semantic_string.split('=')[0].strip()
			elif opt==self.word2code['-']:
				if is_semantic_parse:
					if self.expr_variable is None:
						semantic_string = 't' + str(self.temporal_index) + ' = ' + str(exprval) + ' - ' + str(
							right)
					else:
						semantic_string = 't' + str(self.temporal_index) + ' = ' + \
										  str(exprval) + ' - ' + \
										  str(right)
						self.expr_variable = None
					self.temporal_index += 1
					self.addr_index += 1
					exprval = semantic_string.split('=')[0].strip()
					# exprval -=right
			self.expr_variable = semantic_string.split('=')[0].strip()
			self.semantic_results.append(semantic_string)
		return exprval,semantic_string.split('=')[0].strip()


	def __term(self):
		'''
		term parse

		Structure:
			left = factor()
			while */'/':
			advance() (scanner)
			right =factor()
			semantic_string = 't' + (index) + '=' left + '*/'/' ' + right
			results.append(semantic_string)
			left = t + (index)
			repeat
		return left

		:return: left
		'''
		termval = self.__factor()
		semantic_string = str(termval)
		while self.__accept(self.word2code['*']) or self.__accept(self.word2code['/']):
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
					self.addr_index += 1
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
					self.addr_index += 1
					self.semantic_results.append(semantic_string)
					termval = semantic_string.split('=')[0].strip()

		return termval


	def __factor(self):
		if self.__accept(self.word2code['(_|[a-z]|[A-Z]|$)\w*']) \
				or self.__accept(self.word2code['True']) or self.__accept(self.word2code['False']):
			self.__advance()
			return self.cur_tok.word
		elif self.__accept(self.word2code['([1-9]\d*)|[0-9]']):
			self.__advance()
			return int(self.cur_tok.word)
		elif self.__accept(self.word2code['(']):
			self.__advance()
			exprval,self.expr_variable = self.__expr()
			self.__expect(self.word2code[')'])
			return self.expr_variable
		else:
			self.error_recorder.append("Syntax error in code line " + str(self.index) + ':\n'+
									"Expect \"Variable\" \"Number\" or \"(\" but received: " + self.next_tok.word)
			if not self.__advance():
				return False
			if not self.is_control_stream:
				return self.__statement()
			else:
				return self.__cond()


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


	def __accept(self,acc_type):
		if self.next_tok and self.next_tok.code == acc_type:
			return True
		else:
			return False


	def __expect(self,acc_type):
		if not self.__accept(acc_type):
			# print('error in __expect')
			self.error_recorder.append("Syntax error in code line " + str(self.index) + ':\n'+
									   "Expected {} but received {}".format(str(self.code2word[acc_type]),self.next_tok.word))
			self.__advance()
		else:
			self.__advance()


	def __storeErrorInExcel(self):
		df = pd.DataFrame()
		writer = lexical_analyzer.writer
		error_list = []
		for item in self.error_recorder:
			error_list.append(item)
		df['error'] = error_list
		df = df[['error']]
		df.to_excel(writer,sheet_name='Error-recorder')
		df = pd.DataFrame()
		results_recorder = []
		line_index = 1
		for item in self.all_semantic_results:
			# results_recorder.append("line " + str(line_index) + " : \n")
			for address in item:
				results_recorder.append(address)
		df['results'] = results_recorder
		df = df[['results']]
		df.index = range(1,len(df) + 1)
		df.to_excel(writer,sheet_name='semantic-results')
		writer.save()


if __name__ == '__main__':
	is_semantic_parse = True
	lexical_analyzer = Lexical_Analyzer('wordCode.xlsx','Results.xlsx')
	data_list = loadData('data_expr.txt')
	space_number_list = lexical_analyzer.getSpaceNumber(data_list)
	data_list = lexical_analyzer.convertSentecesToWordCode(data_list)
	syntax_analyzer = Syntactic_Analyzer('Results.xlsx',lexical_analyzer,is_semantic_parse)
	syntax_analyzer.fit(data_list,space_number_list)
	for error in syntax_analyzer.error_recorder:
		logging.error(error)
	index = 1
	# for item in syntax_analyzer.all_semantic_results:
	# 	logging.info('     '+str(item))
	for sentence in syntax_analyzer.all_semantic_results:
		for item in sentence:
			logging.info('Address  line ' + str(index)+ ': ' + str(item))
			index += 1
	logging.info("The results (Lexical,Syntax and Semantic) have been stored in Results.xlsx")
	logging.info("Input Enter to continue")
	to_continue = input()
