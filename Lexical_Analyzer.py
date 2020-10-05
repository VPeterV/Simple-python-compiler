# -*- coding: utf-8 -*-
# @Time    : 2019/10/26 18:33f
# @Author  : PeterV
# @FileName: Lexical_Analyzer.py
# @Software: PyCharm

import pandas as pd
import re
import copy

class Lexical_Analyzer:
	def __init__(self,word_code_path,result_path):
		self.word_code_path = word_code_path
		self.result_path = result_path
		self.__initialize_word_code()

	def __initialize_word_code(self):
		file = pd.read_excel(self.word_code_path,sheet_name=0,index=False)
		# print(file)
		self.word2id = {}
		self.id2word = {}
		for item_word,item_code in zip(file['word'],file['code']):
			# print(item_word)
			self.word2id[item_word] = item_code
			self.id2word[item_code] = item_word

	def getSpaceNumber(self,data_list):
		spacenumber_list = []
		for item in data_list:
			amount = 0
			for i in range(len(item)):
				if item[i]==' ':
					amount+=1
				elif item[i]=='\t':
					amount+=4
				else:
					# print(item[i])
					break
			spacenumber_list.append(amount)
		return spacenumber_list

	def getAllWordCode(self,data_list):
		word_code_list = []
		for sentence in data_list:
			# print(sentence)
			sen_list = sentence.replace('\t','    ').split(' ')
			# print(sen_list)
			# print(sen_list)
			tmp_list_origin = []
			tmp_list_dict = []
			for word in sen_list:
				# print(word)
				tmp_list_origin.extend(self.__stringProcessing(word))
			# print(tmp_list_origin)
			for word in tmp_list_origin:
				tmp_list_dict.append({word:self.getWordCode(word)})
			word_code_list.extend(tmp_list_dict)
		self.__storeResultsInExcel(word_code_list)
		return word_code_list

	def convertSentecesToWordCode(self,data_list):
		sen_word_code_list = []
		for sentence in data_list:
			word_code_list = []
			# print(sentence)
			sen_list = sentence.replace('\t','    ').split(' ')
			# print(sen_list)
			# print(sen_list)
			tmp_list_origin = []
			tmp_list_dict = []
			for word in sen_list:
				# print(word)
				tmp_list_origin.extend(self.__stringProcessing(word))
			# print(tmp_list_origin)
			for word in tmp_list_origin:
				tmp_list_dict.append({word:self.getWordCode(word)})
			word_code_list.extend(tmp_list_dict)
			sen_word_code_list.append(word_code_list)
		all_word_code_list = self.getAllWordCode(data_list)
		return sen_word_code_list

	def getWordCode(self, word):
		# print(word)
		if word in self.word2id:
			code =self.word2id[word]
		else:
			if re.match('(_|[a-z]|[A-Z]|$)\w*', word):
				code = self.word2id['(_|[a-z]|[A-Z]|$)\w*']
			elif re.match('([1-9]\d*)|[0-9]', word):
				code = self.word2id['([1-9]\d*)|[0-9]']
			else:
				code = self.word2id['ERROR']

		return code

	def __stringProcessing(self,word):
		'''
		Parse those tokens that cannot be tokenized by space or '\t'
		'''
		origin_word = copy.deepcopy(word)
		processed_word_list = []
		start_index = 0
		last_index = len(origin_word)
		duplicated_continue = False
		for i in range(len(origin_word)):
			if duplicated_continue:
				duplicated_continue=False
				continue
			if origin_word[i]=='(':
				processed_word_list,start_index,duplicated_continue=self.__expressionProcessing(processed_word_list,
																			origin_word,start_index,i,False,'(',None)
			elif origin_word[i]==')':
				processed_word_list, start_index,duplicated_continue = self.__expressionProcessing(processed_word_list,
																			   origin_word, start_index, i, False, ')',
																			   None)
			elif origin_word[i]=='[':
				processed_word_list, start_index, duplicated_continue = self.__expressionProcessing(processed_word_list,
																									origin_word,
																									start_index, i,
																									False, '[',
																									None)
			elif origin_word[i]==']':
				processed_word_list, start_index, duplicated_continue = self.__expressionProcessing(processed_word_list,
																									origin_word,
																									start_index, i,
																									False, ']',
																									None)
			elif origin_word[i]=='{':
				processed_word_list, start_index, duplicated_continue = self.__expressionProcessing(processed_word_list,
																									origin_word,
																									start_index, i,
																									False, '{',
																									None)
			elif origin_word[i]=='}':
				processed_word_list, start_index, duplicated_continue = self.__expressionProcessing(processed_word_list,
																									origin_word,
																									start_index, i,
																									False, '}',
																									None)
			elif origin_word[i]=='+':
				if i+1<len(origin_word) and origin_word[i+1]=='=':
					processed_word_list, start_index,duplicated_continue = self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, True,
																				   '+', '=')
				else:
					processed_word_list, start_index,duplicated_continue = self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, False,
																				   '+', None)
			elif origin_word[i]=='-':
				if i+1<len(origin_word) and origin_word[i+1]=='=':
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, True,
																				   '-', '=')
				else:
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, False,
																				   '-', None)
			elif origin_word[i]=='*':
				if i+1<len(origin_word) and origin_word[i+1]=='=':
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, True,
																				   '*', '=')
				else:
					processed_word_list, start_index,duplicated_continue = self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, False,
																				   '*', None)
			elif origin_word[i]=='/':
				if i+1<len(origin_word) and origin_word[i+1]=='=':
					processed_word_list, start_index,duplicated_continue = self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, True,
																				   '/', '=')
				else:
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, False,
																				   '/', None)

			elif origin_word[i]=='<':
				if i+1<len(origin_word) and origin_word[i+1]=='=':
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, True,
																				   '<', '=')
				elif i+1<len(origin_word) and origin_word[i+1]=='<':
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, True,
																				   '<', '<')
				else:
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, False,
																				   '<', None)
			elif origin_word[i]=='>':
				if i+1<len(origin_word) and origin_word[i+1]=='=':
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, True,
																				   '>', '=')
				elif i+1<len(origin_word) and origin_word[i+1]=='>':
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, True,
																				   '>', '>')
				else:
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, False,
																				   '>', None)
			elif origin_word[i]=='=':
				if i+1<len(origin_word) and origin_word[i+1]=='=':
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, True,
																				   '=', '=')
				else:
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, False,
																				   '=', None)
			elif origin_word[i]=='%':
				if i+1<len(origin_word) and origin_word[i+1]=='=':
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, True,
																				   '%', '=')
				else:
					processed_word_list, start_index ,duplicated_continue= self.__expressionProcessing(processed_word_list,
																				   origin_word, start_index, i, False,
																				   '%', None)
			elif origin_word[i]==':':
				# print(origin_word[i])
				# print(processed_word_list)
				processed_word_list, start_index, duplicated_continue = self.__expressionProcessing(processed_word_list,
																									origin_word,
																									start_index, i,
																									False,
																									':', None)
				# print(processed_word_list)

			elif origin_word[i]==',':
				processed_word_list, start_index, duplicated_continue = self.__expressionProcessing(processed_word_list,
																									origin_word,
																									start_index, i,
																									False,
																									',', None)
			elif origin_word[i]=='.':
				processed_word_list, start_index, duplicated_continue = self.__expressionProcessing(processed_word_list,
																									origin_word,
																									start_index, i,
																									False,
																									'.', None)
			elif origin_word[i]=='\'':
				processed_word_list, start_index, duplicated_continue = self.__expressionProcessing(processed_word_list,
																									origin_word,
																									start_index, i,
																									False,
																									'\'', None)
			elif origin_word[i]=='\"':
				processed_word_list, start_index, duplicated_continue = self.__expressionProcessing(processed_word_list,
																									origin_word,
																									start_index, i,
																									False,
																									'\"', None)
			elif origin_word[i]=='#':
				last_index = i
				processed_word_list, start_index, duplicated_continue = self.__expressionProcessing(processed_word_list,
																									origin_word,
																									start_index, i,
																									False,
																									'#', None)
				break
			# print(processed_word_list)
		# print(processed_word_list)
		if start_index<last_index:
			processed_word_list.append(origin_word[start_index:last_index])
		return processed_word_list

	def __storeResultsInExcel(self,allWordCodes):
		df = pd.DataFrame()
		self.writer = pd.ExcelWriter(self.result_path)
		word_list = []
		code_list = []
		for item_dict in allWordCodes:
			for key,value in item_dict.items():
				if key=='==':
					key = '\'' + key + '\''
				word_list.append(key)
				code_list.append(value)
		df['word'] = word_list
		df['code'] = code_list
		df = df[['word','code']]
		df.to_excel(self.writer,sheet_name='Word-code')
		self.writer.save()

	def	__expressionProcessing(self,processed_word_list,origin_word,start_index,i,isDuplicated,char,duplicated_char):
		if not isDuplicated:
			if start_index != i:
				processed_word_list.append(origin_word[start_index:i])
			processed_word_list.append(char)
			start_index = i + 1
			# if start_index >= len(origin_word):
			# 	start_index = i
			duplicated_continue = False
		else:
			if start_index != i:
				processed_word_list.append(origin_word[start_index:i])
			processed_word_list.append(char+duplicated_char)
			start_index = i + 2
			# if start_index >= len(origin_word):
			# 	start_index = i
			duplicated_continue = True

		return processed_word_list,start_index,duplicated_continue

def loadData(data_path):
	data_list = []
	with open(data_path,'r',encoding='utf-8') as file:
		for item in file:
			data_list.append(item.strip('\n'))
	return data_list


if __name__ == '__main__':
	analyzer = Lexical_Analyzer('wordCode.xlsx','result.xlsx')
	# print(analyzer.word2id)
	# print(analyzer.id2word)
	# test_str = '_abc'
	# pattern = '(_|[a-z]|[A-Z]|$)\w*'
	# string = re.match(pattern,test_str)
	# print(string.string)
	# long_string = ''
	# print(len(long_string))
	data_list = loadData('data.txt')
	all_word_codde = analyzer.getAllWordCode(data_list)
	print('The results (The results have also been stored in ./result.xlsx ) :')
	print(all_word_codde)
