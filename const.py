import yaml
import numpy as np
import pandas as pd

from utils import get_F, get_F_example

from sklearn.metrics import pairwise_distances

class Const(object):
	def __init__(self):
		self.config = yaml.load(open("settings.yaml", 'r'))
		self.__norms = {}

	def __normalize(self, X, percent):
		#add dict of means
		norms = []
		for i in range(X.shape[1]):
			x = X[:, i]
			d = pairwise_distances(x[:, np.newaxis]).ravel()
			d.sort()
			d = d[d != 0]
			num = max(int(d.shape[0] * percent / 100), 2)
			norm = d[:num].mean()
			x = x / norm
			norms.append(norm)
			X[:, i] = x
		return X, norms

	def norm(self, df, percent=15):
		'''
		Inplace method for normilaze coords
		args:
		df -- data frame ['id', 'X1', 'X2', ..., 'Xn']

		'''
		X, norms = self.__normalize(df.iloc[:, 1:].values, percent)
		
		for i, col in enumerate(df.columns[1:]):
			self.__norms[col] = norms[i]
		df.iloc[:, 1:] = X

	def get_norms(self):
		if len(self.__norms)==0:
			print("Norms is not calculated. Maybe you don't normalize training data")
			return 
		else:
			return self.__norms

	def __calculate_weights_by_max(self, X_percent_matrix, X, started_a):

		first = True# задаем флаг для первого нахождения a и средней суммы весов
		
		#Создаем список, где 0 (т.е. started) a будет стоять в начале
		var = [i for i in range(-self.config['consts']['down_steps'],self.config['consts']['up_steps']+1)]
		var.pop(var.index(0))
		list_for_k = [0] + var

		for k in list_for_k:# задаем цикл диапазона [-down_steps:up_steps]
			
			a =  started_a * (self.config['consts']['power_koef']**k)#Вычисляем текущее значение а
			
			F = get_F_example(X, a)#Вычисляем F для матрицы (!!!ВНИМАНИЕ ФОРМУЛА!!!) [id, X1,..,Xn, F]

			def F_sort(arr):#Вспомогательная функция для сортировки
				return arr[-1]
			F.sort(key=F_sort,reverse = True)#Сортируем F по убыванию
			
			# Выбираем Y% матрицы
			lenght = int(np.round(len(F)*self.config['consts']['percent_Y']/100, 0))
			Y_percent_matrix = np.array(F[:lenght])
			
			#Высчитываем сумму ребер
			summ = 0
			for edge in X_percent_matrix:# Проходим построчно матрицу X% - row = [id вершины 1, id вершины 2, расстояние]
				if edge[0] in Y_percent_matrix[:,0] and edge[1] in Y_percent_matrix[:,0]: #Если обе вершины в матрице, то сумма + 1
					summ += 1
				elif edge[0] in Y_percent_matrix[:,0] or edge[1] in Y_percent_matrix[:,0]: #Если только 1 из вершин в матрице, то сумма + 0.5
					summ += 0.5

			if first:# Если флаг первого вхождения = True, то искомые a и среднюю сумму задаем тут
				first =False #Меняем флаг на False
				max_summ_edge = summ/len(X_percent_matrix)
				max_a = a
			else:# Если флаг первого фхождения = False, то у нас уже есть искомая a и средняя сумма
				if max_summ_edge < summ/len(X_percent_matrix): #Сравниваем среднюю сумму с предыдущим значение, если оно большо, тообновляем max_summ_edge и max a
					max_summ_edge = summ/len(X_percent_matrix)
					max_a = a

		return max_a, F

	def __calculate_weights_by_Y(self, X_percent_matrix, X, started_a):


		list_a = [] #Создаем список для хранения всех а
		list_Y_percent = [] #Создаем список для хранения всех Y% при которых средняя сумма больше порога
		list_summ_edge = [] #Создаем список для хранения всех средних сумм, которые впервые превысили порог
		
		arr_Y_step = [] # задаем массив шагов по Y%
		current = self.config['consts']['Y_step'] #Устанавлиаем первое значение как шаг по Y%

		while current < 100: #Пока текущее значение процента не превышает 100% 
			arr_Y_step.append(current) # Добавляем текущее значение в массив шагов по Y%
			current += self.config['consts']['Y_step'] # Прибавляем к текущему значению шаг 
		if arr_Y_step[-1]<100: #Для случая если шаг 100/Y_step не целое (например Y_step=3%), то добавляем в конец массивf шагов по Y% 100%
			arr_Y_step.append(100)

		#Создаем список, где 0 (т.е. started) a будет стоять в начале
		var = [i for i in range(-self.config['consts']['down_steps'],self.config['consts']['up_steps']+1)]
		var.pop(var.index(0))
		list_for_k = [0] + var

		for k in list_for_k: # задаем цикл диапазона [-down_steps:up_steps]

			a =  started_a * (self.config['consts']['power_koef']**k)#Вычисляем текущее значение а

			list_a.append(a)#Добавляем текущее значение а в список для хранения всех а

			
			F = get_F_example(X, a) #Вычисляем F для матрицы (!!!ВНИМАНИЕ ФОРМУЛА!!!) [id, X1,..,Xn, F]
			
			def F_sort(arr):#Вспомогательная функция для сортировки
				return arr[-1]
			F.sort(key=F_sort,reverse = True)#Сортируем F по убыванию

			for step in arr_Y_step:#Итерируемся по матрице шагов Y%
				
				# Выбираем текущий Y% матрицы
				lenght = int(np.round(len(F)*step/100, 0))
				Y_percent_matrix = np.array(F[:lenght])

				#Высчитываем сумму ребер
				summ = 0
				for edge in X_percent_matrix:# Проходим построчно матрицу X% - row = [id вершины 1, id вершины 2, расстояние]
					if edge[0] in Y_percent_matrix[:,0] and edge[1] in Y_percent_matrix[:,0]:#Если обе вершины в матрице, то сумма + 1
						summ += 1
					elif edge[0] in Y_percent_matrix[:,0] or edge[1] in Y_percent_matrix[:,0]:#Если только 1 из вершин в матрице, то сумма + 0.5
						summ += 0.5
				if summ/len(X_percent_matrix) > self.config['consts']['threshold']:#Если текущая средняя сумма больше порога
					list_Y_percent.append(step)#Добавляем текущее значение Y% в список для хранения всех всех Y%
					list_summ_edge.append(summ/len(X_percent_matrix))#Добаляем среднюю сумму в список для хранения всех средних сумм
					# print('a=',a, 'step=',step)
					break # Прерываем цикл

		#Задаем начальные значения как 0 элементы списков
		# print(list_Y_percent)
		min_Y_percent = list_Y_percent[0] 
		max_summ_edge = list_summ_edge[0]
		max_a = list_a[0]
		for i in range(1, len(list_Y_percent)):
			if min_Y_percent > list_Y_percent[i]: # Если текущий элемент списка Y% меньше минимального, то обновялем наши значения
				min_Y_percent = list_Y_percent[i]
				max_summ_edge = list_summ_edge[i]
				max_a = list_a[i]

		return max_a

	def __calculate_const(self, X, type = 1):
		#
		matrix = []
		distance_matrix = np.tril(pairwise_distances(X[:,1:]))#Вычисляем матрицу расстояний [len(id), len(id)]
		#[0,   0,   0]
		#[1.3, 0,   0] - пример
		#[1.8, 5.2, 0]
		#Цикл для составления матрицы соответствия [id вершины 1, id вершины 2, расстояние]
		for i in range(distance_matrix.shape[0]):
			for j in range(distance_matrix.shape[1]):
				if distance_matrix[i,j]!=0:
					row = [i+1, j+1, distance_matrix[i,j]]
					matrix.append(row)
		#[1, 2, 1.3]
		#[1, 3, 1.8] - пример
		#[2, 3, 5.2]
		def sort_dist(row): #Вспомогательная функция для сортировки
			return row[2]
		matrix.sort(key=sort_dist)
		distance_matrix = np.array(matrix) #Переводим матрицу в np.array

		#Выбираем X% матрицы расстояний
		lenght = int(np.round(distance_matrix.shape[0]*(self.config['consts']['percent_X']/100), 0))
		X_percent_matrix = distance_matrix[:lenght]

		#Вычисляем начальное значение a
		mean_distance_matrix = X_percent_matrix[:,2].mean()
		started_a = self.config['consts']['const'] * mean_distance_matrix

		if type == 1:#В первом варианте высчитываем расстояния по 1-му варианту в документе
			max_a = self.__calculate_weights_by_max(X_percent_matrix, X, started_a)
		else:#Во втором варианте высчитываем расстояния по 2-му варианту в документе
			max_a = self.__calculate_weights_by_Y(X_percent_matrix, X, started_a)
		#На выходе получаем 2 значения (коэффициент a, и среднее значение весов)
		self.config['consts']['a'] = max_a
		return max_a

	def calculate_a(self, df, type_of_optimization=2):
		'''
		Method for calcualte_a and change consts with a
		args:
		df - data frame ['id', 'X1', 'X2', ..., 'Xn']
		type_of_optimization - type of optimization (type1 - using max; type2 - using threshold) default = type2
		'''
		X = df.iloc[:].values#приводим их np.array [id, X1, X2]

		if type_of_optimization==1:
			max_a = self.__calculate_const(X, 1)
		elif type_of_optimization==2:
			max_a = self.__calculate_const(X, 2)
		else:
			print('Not implemented')
		#Изменяем необходимые константы
		self.config['isolated_cluster']['min_len'] = \
			np.round(self.config['isolated_cluster']['min_len'] * max_a, self.config['consts']['round_const'])

		self.config['knots']['stop_const'] = \
			np.round(self.config['knots']['stop_const'] * max_a, self.config['consts']['round_const'])

		value = 1./((max_a * self.config['conturs']['min_diff'][0])**2\
			+ max_a * self.config['conturs']['min_diff'][1])
		self.config['conturs']['min_diff'] = np.round(value, self.config['consts']['round_const'])

		value = 1./((max_a * self.config['isolated_cluster']['min_dif'][0])**2\
			+ max_a * self.config['isolated_cluster']['min_dif'][1])
		self.config['isolated_cluster']['min_dif'] = np.round(value, self.config['consts']['round_const'])

