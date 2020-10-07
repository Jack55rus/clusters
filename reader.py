import pandas as pd

class Reader(object):
	"""docstring for ClassName"""
	def __init__(self):
		pass

	def read(self, file_path):
		'''
		args:
		file_path -- path to the file

		returns:
		dataframe if format is correct
		None otherwise
		'''
		file_extension = file_path.split('.')[1]
		if file_extension == 'csv':
			in_df = pd.read_csv(file_path) 
		elif file_extension == 'xlsx' or file_extension == 'xls':
			in_df = pd.read_excel(file_path) 
		else:
			print('Unsupported format')
			return
		if self.is_valid(in_df):
			return in_df
		else:
			print('Unsupported format')
			return

	def is_valid(self, df):
		'''
		Checks if input dataframe's columns are in the right format 
		'''
		# print([col_name[1:] for col_name in df.columns[1:]])
		# input('stop')
		coords_nums = [int(col_name[1:]) for col_name in df.columns[1:]]
		is_asc = coords_nums == sorted(coords_nums)
		if is_asc == False:
			print('Wrong column name format')
			return False
		for i, col_name in enumerate(df.columns):
			print(col_name[0])
			if i == 0 and col_name != 'id':
				print('Wrong column name format')
				return False
			elif i > 0 and col_name[0] != 'X':
				print('Wrong column name format')
				return False
		return True


