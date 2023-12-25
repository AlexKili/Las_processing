from PyQt5 import QtCore, QtWidgets

import numpy as np
import sys
import sqlite3
import json
import os

#import matplotlib.pyplot as plt
#import plotly.express as px
import pandas as pd
import codecs
#import lasio
#from welly import Curve
import welly
welly.__version__
from welly import Well
from sklearn.preprocessing import RobustScaler 
from sklearn.neighbors import KNeighborsRegressor
#from sklearn.preprocessing import PowerTransformer, QuantileTransformer, MaxAbsScaler, MinMaxScaler, StandardScaler, Normalizer
#from scipy.signal import savgol_filter
#import re


class LasindbWindow(QtWidgets.QDialog):
    """This class is creating window with script to loading las-files into DB"""
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        
        # create constant
        self.PATH_LAS_FOLDER = None
        self.SOURCE_SEW = None # automatic sew, or human sew
        self.METHOD = None # all las-files is load to DB, only sew-file load into DB
        # create needing values for constant
        #self.PATH_DB = "C:\\Users\\alexk\\Desktop\\WPy64-3741\\For_SQL\\GISdb.sqlite"
        self.SOURCE_SEW = 'automatic'
        self.METHOD = 'onlysew'
                
        # create elements of interface       
        self.group_path = QtWidgets.QGroupBox("PAth to LAS-files (.las)")  # создает группу виджетов для задания пути к шейп-файлу
        self.file_path = QtWidgets.QLineEdit("path to directory with LAS-files")
        button_path = QtWidgets.QPushButton("Browse...")
        self.button_start = QtWidgets.QPushButton("Start")
        hbox_path = QtWidgets.QHBoxLayout()  # создает горизонтальную форму для виджетов для задания пути к шейп-файлу
        hbox_path.addWidget(self.file_path)
        hbox_path.addWidget(button_path)
        hbox_path.addWidget(self.button_start)
        self.group_path.setLayout(hbox_path)
        
        # create signals for interface
        button_path.clicked.connect(self.get_path_las)
        self.button_start.clicked.connect(self.process_stitching)
        
        # create text-elements for view status
        self.status_loadlas = QtWidgets.QTextEdit()
        self.status_loadlas.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.status_loadlas.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        
        # create main vertical box
        vbox_main_lasindb = QtWidgets.QVBoxLayout()
        vbox_main_lasindb.addWidget(self.group_path)
        vbox_main_lasindb.addWidget(self.status_loadlas)        
        
        # set vertical box on main layout
        self.setLayout(vbox_main_lasindb)
    
    def get_parameters(self):
        """This function needing to transfer parametres from main function"""
        print("getParameters")
        self.PATH_DB = "F:\\WPy64-3741\\For_SQL\\GISdb_temporary.sqlite"
        pass
    
    def load_csvdict(self):
        """This function load dictionary with Welnname in db and 
        wellname occasionally occurring in las-file. 
        This dictionary needing to comparison wellname in las to wellname in db"""
        print("load_Csvdict")
        import csv
        dict_from_csv = {}
        curent_file = os.path.basename(__file__)
        curent_directory = os.path.abspath(__file__).replace(curent_file, '')
        with open(f'{curent_directory}\\dictionary\\wellname_db--las.csv', 'r') as File:
            reader = csv.reader(File)
            for row in reader:
                dict_from_csv[row[0]]=row[1]
        return dict_from_csv
    
    def get_path_las(self):
        """This function called after clicked button 'Browse' and 
        take path to directory with las-files"""
        #print("get_path_las")#FOR_TEST
        self.PATH_LAS_FOLDER = QtWidgets.QFileDialog.getExistingDirectory(parent=self, caption="Выбор папки...", directory="C:\\Temp\\")
        self.PATH_LAS_FOLDER = self.PATH_LAS_FOLDER.replace('/', '\\')
        print('PATH   ', self.PATH_LAS_FOLDER)#FOR_TEST
        
        if self.PATH_LAS_FOLDER == '':
            self.status_loadlas.append("<font color=red>please, set the path of las file</font>")
        else:
            self.file_path.setText(self.PATH_LAS_FOLDER)
            self.status_loadlas.append(f"<font color=green>get_path_las_filename={self.PATH_LAS_FOLDER}</font>")
        return
    
    def process_stitching(self):
        """
        Main process. Load after press Start button.
        """
        print('----|||PROCESS STITCHING BEGIN|||---- ')
        self.button_start.setDown(True)  # делает кнопку недоступной пользователю до окончания процесса
        
        # создает соединение с базой данной
        self.conn = sqlite3.connect(self.PATH_DB)
        self.cursor = self.conn.cursor()
        
        # Preparing data in las-files and creating 2 DataFrame for appending into DB 
        gis_las = pd.DataFrame(columns = ['well_id', 'las_id', 'Filename', 'WellName', 'Folder'])
        gis_curve = pd.DataFrame(columns = ['well_id', 'curve_id', 'las_id', 'wellname', 'name_curve', 'unit', 'data_curve', 
                                            'depth_data', 'start', 'stop', 'step', 'head_las'])

        # for connecting (sew) las-files
        # Делаем новый DataFrame с заданными столбцами
        df = pd.DataFrame(columns = ['well_id', 'WellName', 'Name_curve', 'Unit', 'Data_curve', 
                                     'Depth_data', 'Start', 'Stop', 'Step'])
        
        # this block is update index to automatic indexing all las-files.
        max_id_las = self.maxid('wells_gis_las', 'las_id')
        max_id_curve = self.maxid('wells_gis_curve', 'curve_id')
        max_id_sew = self.maxid('wells_gis_sew', 'sew_id')
        
        len_to_main_folder = len(self.PATH_LAS_FOLDER.split('\\'))
        dict_well_name = self.load_csvdict()
        
        for folderName, subfolder, filename in os.walk(self.PATH_LAS_FOLDER):
            las = filter(lambda x: x.endswith((".las", ".LAS")), filename) 
            ### print('Folder', folderName)
            # checking for exist wells in DB
            for filename in las:
                #print('Filename', filename)
                ### Forming table "Gis<->las"
                las_file = folderName + '\\' + filename
                
                # Reading, finding problem strings, replacing it 
                self.fix_lasfile(las_file)
                
                # Reading Name of Well
                well_from_las, well_name_inlas = self.reading_namewell(las_file)
                if well_name_inlas == None: 
                    self.status_loadlas.append(f"<font color=red> !-- WARNING: not open las-file: {las_file}")
                    print(f"!-- WARNING: not read name of well!")
                    continue 
                
                # BLOCK to calculate well_id
                well_name_folder = folderName.split('\\')[len_to_main_folder]
                well_id, well_name_indb = self.wellid(dict_well_name, well_name_folder, well_name_inlas)
                if well_id == None: 
                    print(f'Well id for wellname {well_name_folder} and {well_name_inlas} not found')
                    continue
                
                # las_id
                max_id_las += 1
                
                # las_files
                # gis_las - DataFrame используемый для дальнейшей загрузки в таблицу Wells_gis_las
                gis_las = gis_las.append({'well_id': well_id, 
                                          'las_id': max_id_las, 
                                          'Filename': filename, 
                                          'WellName': well_name_indb, 
                                          'Folder': folderName}, 
                                          ignore_index = True)
                
                # Reading Header of las
                edit_las = open(las_file, 'r', encoding = 'CP866', errors = 'ignore')
                header = edit_las.read().split('~ASCII')[0]
                edit_las.close()
                
                # Reading main data
                dept = np.array(well_from_las.df().index)
                
                for key in well_from_las.data.keys(): # проходимся по каждой кривой в лас-файле
                    max_id_curve += 1
                    #curve_id = max_id_curve
                    
                    cur_name = key # название кривой
                    #curve = well_from_las.data[key]
                    cur_unit = well_from_las.data[key].units # единицы СИ
                    cur_data = np.array(well_from_las.data[key]) # значения кривой (сама кривая)
                    
                    dept = np.array(well_from_las.df().index)
                    dept = np.round(dept, 2)
                    
                    # обрезание NaN значений с начала и конца кривой
                    ## удаление NaN-значений с начала кривой
                    len_curve = len(cur_data)
                    for i in range(len_curve):
                        if np.isnan(cur_data[i]) == False:  
                            # при первом числе не равном NaN удаляются записи ранее этого числа и цикл прерывается
                            cur_data = np.delete(cur_data, np.arange(0, i, 1))
                            dept = np.delete(dept, np.arange(0, i, 1))
                            break
                    """
                    if np.any(np.isnan(cur_data)) == True: 
                        self.status_loadlas.append(f"<font color=red> Curve contain <any> value is Nan ', {well_name_indb} </font>") # FOR_TEST
                    """
                    ## удаление NaN-значений с конца кривой
                    len_curve = len(cur_data) # refresh lenght of curves
                    for i in np.arange(len_curve-1, 0, -1):
                        if np.isnan(cur_data[i]) == False:
                            cur_data = np.delete(cur_data, np.arange(i, len_curve, 1))
                            dept = np.delete(dept, np.arange(i, len_curve, 1))
                            break
                    
                    len_curve = len(cur_data) # refresh lenght of curves
                    start_cur = round(dept[0], 2) # отметка глубины начала кривой
                    stop_cur = round(dept[-1], 2) # отметка глубины конца кривой
                    step_cur = round (dept[1]-dept[0], 2) # шаг квантования (шаг изменения отметок глубины)
                    
                    # добавление строк в DataFrame 
                    # gis_curve - DataFrame используемый для дальнейшей загрузки в таблицу Wells_GIS_curve
                    gis_curve = gis_curve.append({'well_id':well_id, 
                                                  'curve_id':max_id_curve, 
                                                  'las_id':max_id_las, 
                                                  'wellname': well_name_indb, 
                                                  'name_curve':cur_name, 
                                                  'unit':cur_unit, 
                                                  'data_curve':json.dumps(cur_data.tolist()), 
                                                  'depth_data':json.dumps(dept.tolist()),
                                                  'start':start_cur, 
                                                  'stop':stop_cur, 
                                                  'step':step_cur, 
                                                  'head_las':header}, 
                                                  ignore_index=True)
                    df = df.append({'well_id':well_id, 
                                    'WellName':well_name_indb, 
                                    'Name_curve':cur_name, 
                                    'Unit':cur_unit, 
                                    'Data_curve':cur_data.tolist(), 
                                    'Depth_data':dept.tolist(), 
                                    'Start':start_cur, 
                                    'Stop':stop_cur, 
                                    'Step':step_cur}, 
                                    ignore_index=True)
                pass
            pass
        pass
        
        #print(df)
        # GET RESULT DICT WITH SEW-GIS FROM DATAFRAME
        #result_df = pd.DataFrame(columns = ['well_id', 'WellName', 'Name_curve', 'Unit', 'Data_curve', 'Depth_data', 'Start', 'Stop', 'Step'])
        result_dict = {}
        error_unit = []
        # df is [well_id	WellName	Name_curve	Unit	Data_curve	Depth_data	Start	Stop	Step]
        for name_well in list(dict.fromkeys(list(df['WellName']))):
            gis_dict = {}
            for name_curve in list(dict.fromkeys(list(df.query(f'WellName == "{name_well}"')['Name_curve']))):
                #for name_curve in ['GK', 'PS']:
                print('----|||NEW_CYCLE|||----          name_curve=', name_curve)
                new_df = df.query(f'WellName == "{name_well}" and Name_curve == "{name_curve}"').copy(deep=True)
                new_df = self.main_block(new_df)
                gis_dict[name_curve] = new_df
                #result_df = pd.concat([result_df, new_df])
            result_dict[name_well] = gis_dict
        #print('Result_dict', result_dict)
        
        # PREPARING DATA BEFORE LOADING IN DB
        # Forming dataframe to DB
        result_df = pd.DataFrame(columns = ['well_id','WellName','Name_curve','Unit','Data_curve','Depth_data','Start','Stop','Step'])
        for wellname in result_dict.keys():
            for method in result_dict[wellname].keys():
                result_df = result_df.append(result_dict[wellname][method])
        
        # Correction result_df before entering into DB
        len_index = len(result_df.index)
        result_df['sew_id'] = np.arange(max_id_sew + 1, max_id_sew + 1 + len_index)
        
        # Converting Data_curve and Depth_data into json-object
        """
        result_df['Data_curve'] = [json.dumps(x) for x in result_df['Data_curve']]
        result_df['Depth_data'] = [json.dumps(x) for x in result_df['Depth_data']]
        """
        
        #print('ERORR', result_df['WellName'], result_df['Data_curve'])
        for i, row in result_df.iterrows():
            try:
                result_df.loc[i, 'Data_curve'] = json.dumps(row['Data_curve'])
            except:
                print(f"-------------------------ERORR {i}, {type(row['Depth_data'])}")
        
        for i, row in result_df.iterrows():
            try:
                result_df.loc[i, 'Depth_data'] = json.dumps(row['Depth_data'])
            except:
                print(f"-------------------------ERORR {i}, {type(row['Depth_data'])}")
        
        # load information to DataBase
        #gis_las = [] # FOR TEST
        #gis_curve = [] # FOR_TEST
        if len(gis_las) > 0 and len(gis_curve) > 0: 
            print('LOAD IN Database')
            self.cursor.executemany("""INSERT INTO wells_gis_las('well_id', 'las_id', 'Filename','WellName', 'Folder') 
                                        VALUES(?, ?, ?, ?,?);""", gis_las.values.tolist()) 
            self.conn.commit()
            self.cursor.executemany("""INSERT INTO wells_gis_curve('well_id', 'curve_id', 'las_id', 'wellName','name_curve', 'unit', 'data_curve','depth_data', 'start', 'stop', 'step', 'head_las') 
                                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?);""", gis_curve.values.tolist()) 
            self.conn.commit()
            self.status_loadlas.append("<font color=green> Information of las-files write to DB successfully</font>")
        else:
            self.status_loadlas.append("<font color=red> Information of las-files not write to DB </font>")
        self.button_start.setDown(False)
        
        print('Before loading:', result_df.values.tolist())
        self.cursor.executemany("""INSERT INTO wells_gis_sew('well_id', 'WellName', 'Name_curve', 'Unit', 'Data_curve', 'Depth_data',  
                           'Start', 'Stop', 'Step', 'sew_id') VALUES(?,?,?,?,?,?,?,?,?,?);""", result_df.values.tolist())
        self.conn.commit()
        
        
        print('CONGRADULATION! STITCHING SUCCESSFUL!')
        # self.status_loadlas("<font color=red> CONGRADULATION! STITCHING SUCCESSFUL! </font>")
        return
    
    # ------ PASTED BLOCK -------
    def main_block(self, new_df):
        """Основной блок для сшивки кривых
        Получает на вход DataFrame со списком кривых по одному методу
        На выходе сшитая кривая по одному методу"""
        # IMPORTANT: У некоторых кривых в разных ласах разные единицы измерения!!!!!
        # например д.ед. и % из-за этого сшитая кривая некорректна!!! 
        # TODO: сделать проверку схожести ед.измерения и приведение их к одной единице измерения
        print('----|||INTO_MAIN_BLOCK|||----')
        #print('New_df', new_df)
        min_len_learnsample = 5 # TODO: change this parametr
        
        # new_df.shape[0] its a count of curves 
        # the next cycle runs until there is no one curve left
        # the curves are removed after stitching
        # counter_for_cycle is required to prevent an infinite loop
        counter_for_cycle = 0
        #if new_df.shape[0] == 1:
        #    start_curve_index = 0
        while new_df.shape[0] > 0 and counter_for_cycle < 40: 
            #print('Into cycle', counter_for_cycle)
            counter_for_cycle += 1
            
            start_curve = new_df[new_df.Start == new_df.Start.min()]
            if len(start_curve) == 1:
                start_curve_index = start_curve.index[0]
            elif len(start_curve) >1:
                start_curve = start_curve[start_curve.Stop == start_curve.Stop.max()]
                start_curve_index = start_curve.index[0]
            else:
                self.status_loadlas.append("Incorrect input DataFrame for sew")
            
            start_curve_begin = new_df.loc[start_curve_index]['Start'] # Start point of first curve
            start_curve_end = new_df.loc[start_curve_index]['Stop'] # Stop point of first curve
            
            # this cycle need for search intersection or not intersection curves
            cross_curve_index = [] # this list contains indexes of curves that intersect with the initial curve
            notcross_curve_index = [] #this list contains indexes of curves that not intersect with the initial curve
            for current_index in new_df.index:
                current_curve = new_df.loc[current_index]
                begin_point = current_curve['Start']
                end_point = current_curve['Stop']
                
                if current_index == start_curve_index:
                    # если индекс соответствует стартовой кривой, то цикл переходит на следующую итерацию
                    continue
                elif begin_point+min_len_learnsample < start_curve_end and start_curve_end < end_point:
                    # если начальная точка находится в интервале стартовой кривой а конечная точка за пределами 
                    # стартовой кривой, то индекс кривой заносится в список пересекающихся
                    cross_curve_index.append(current_index)
                elif begin_point+min_len_learnsample > start_curve_end:
                    # если начальная точка находится за пределами стартовой кривой 
                    # то кривая заносится в список не пересекающихся кривых 
                    notcross_curve_index.append(current_index)
                else:
                    # если начальная и конечная точка находится в интервале стартовой кривой, 
                    # либо стартовые точки кривых одинаковые, а конечная точка внутри стартовой кривой
                    # то такие кривые исключаются из ДатаФрейма
                    #self.status_loadlas.append("Curves is equal, not connection! Search in working")
                    new_df = new_df.drop(index = current_index)
            
            if cross_curve_index != []:
                # если были найдены пересекающиеся кривые с начальной кривой
                id_intersect_curve = new_df.loc[cross_curve_index][['Start']].idxmin().to_numpy()[0]
                step = 0.2 # TODO: change this parametr!!
                new_df = self.crossing(new_df, id_intersect_curve, start_curve_index, step)
            elif notcross_curve_index != []:
                # если не были найдены пересекающиеся кривые с начальной кривой
                id_intersect_curve = new_df.loc[notcross_curve_index][['Start']].idxmin().to_numpy()[0]
                step = 0.2 # TODO: change this parametr!!
                #self.status_loadlas.append(f"Notcrossing!, {id_intersect_curve}, {start_curve_index}, {step}")
                new_df = self.not_crossing(new_df, id_intersect_curve, start_curve_index, step)
            else:
                self.status_loadlas.append("Erorr! Booth list of index is empty!")
            self.status_loadlas.append(f"End stitching curve, {start_curve_index}")
        return new_df.query(f'index=={start_curve_index}')
    
    def not_crossing(self, new_df, *list_params):
		# This function uses if curves have not cross
        print('---|||INTO_NOT_CROSS|||----')
		# 1-формирование нового DataFrame из значений первой и второй кривой
        id_intersect_curve, start_index, step = list_params
		#i, index, values, start_index, start_values, step = list_params
		
        curve_start = np.array( new_df.loc[start_index, 'Data_curve'] )
        curve_start = curve_start.flatten()
		
        dept_start = np.array( new_df.loc[start_index, 'Depth_data'] )
        dept_start = np.round(np.array(dept_start), 2)
        dept_start = dept_start.flatten()
		
        start_curve_begin = dept_start[0]
        start_curve_end = dept_start[-1]
        unit_start = new_df.loc[start_index, 'Unit'] 
		#curve_start = np.nan_to_num(curve_start) # TODO: change this
        ###print('Not crossing start curve info: ', start_index, new_df.loc[start_index, 'Name_curve'])
		
        curve_intersect = np.array( new_df.loc[id_intersect_curve, 'Data_curve'] )
        curve_intersect = curve_intersect.flatten()
		
        dept_intersect = np.array( new_df.loc[id_intersect_curve, 'Depth_data'] )
        dept_intersect = np.round(np.array(dept_intersect), 2)
        dept_intersect = dept_intersect.flatten()
		
        intersect_curve_begin = dept_intersect[0]
        intersect_curve_end = dept_intersect[-1]   
        unit_intersect = new_df.loc[id_intersect_curve, 'Unit']
		#curve_intersect = np.nan_to_num(curve_intersect)
		#start_index = new_df.loc[start_index[0]] ['Data_curve']
		#dept_start = new_df.loc[start_index[0]] ['Depth_data']
        print('curve_start begin end', start_curve_begin, start_curve_end)
        ###print('curve_intersect begin end', intersect_curve_begin, intersect_curve_end)
		
        
        depth_between = np.arange(start_curve_end + step, 
									intersect_curve_begin, 
									step)
        value_between = np.full((len(depth_between)), np.NaN)
					
		#curve_intersect = new_df.loc[i] ['Data_curve']
		#dept_intersect = new_df.loc[i] ['Depth_data']
        
        
        if len(start_index.shape)>1: 
            start_index = start_index.values
            start_index = start_index[:,0]
        if len(curve_intersect.shape)>1: 
            curve_intersect = curve_intersect.T[0]
		
        new_values = np.hstack((curve_start, value_between, curve_intersect))
        new_values = new_values.tolist()
        new_values_depth = np.hstack((dept_start, value_between, dept_intersect))
        new_values_depth = np.round(new_values_depth, 1)
        new_values_depth = new_values_depth.tolist()
        # load new values into DataFrame
        new_df.at[start_index, 'Data_curve'] = new_values
        new_df.at[start_index, 'Depth_data'] = new_values_depth
        new_df.loc[start_index, 'Start'] = new_values_depth[0]
        new_df.loc[start_index, 'Stop'] = new_values_depth[-1]
        new_df.loc[start_index, 'Step'] = new_df.loc[start_index, 'Step']
        new_df = new_df.drop(id_intersect_curve)
        #print('RETURNING_FROM_NOTCROSSING', new_values.shape, new_values_depth.shape)
        print('Return from not crossing', type(new_values))
        return new_df
	
	# ------PRERELEASE VERSION------
    def crossing(self, new_df, *list_params):
        print('----|||INTO_CROSSLINK|||----')
        id_intersect_curve, start_index, step = list_params
		# i - номер записи пересекающейся со стартовым интервалом
		# step - шаг квантования стартового интервала из ласа
		# index - индексы всех значений из new_df
		# values - все значения 'Dept_start' и 'Dept_stop' из new_df
		# start_index - значение индекса стартового интервала
		# start_values - значение глубины стартового интервала
		#print('i: ', i, 'index: ',index, 'values:',values, 'start index:',start_index, 'start_values',start_values, 'step',step)
		
		# выделение стартовой (первой) кривой к которой будет пришиваться вторая кривая
		# нормализация стартовой кривой с использованием регуляризаторов библиотеки scikit-learn
        ###print('Crossing start curve info: ', start_index, new_df.loc[start_index]['Name_curve'], id_intersect_curve)
        ###print('New df info:', new_df.loc[start_index]['Data_curve'])
		
        curve_start = np.array( new_df.loc[start_index]['Data_curve'] )
        curve_start = curve_start.flatten()
		#curve_start = curve_start.reshape(len(curve_start), 1)
		
        dept_start = np.array( new_df.loc[start_index]['Depth_data'] )
        dept_start = np.round(np.array(dept_start), 2)
        dept_start = dept_start.flatten()
		
        start_curve_begin = dept_start[0]
        start_curve_end = dept_start[-1]
        unit_start = new_df.loc[start_index]['Unit']
		
        curve_intersect = np.array( new_df.loc[id_intersect_curve]['Data_curve'] )
        curve_intersect = curve_intersect.flatten()
		#curve_intersect = curve_intersect.reshape(len(curve_intersect),1) 
		
        dept_intersect = np.array( new_df.loc[id_intersect_curve]['Depth_data'] )
        dept_intersect = np.round(np.array(dept_intersect), 2)
        dept_intersect = dept_intersect.flatten()
		
        if len(curve_start) != len(dept_start):
            dept_start = [start_curve_begin+(i+1)*step for i in range(len(curve_start))]  # generating new list with depth
        dept_intersect = self.select_shift(dept_start, curve_start, dept_intersect, curve_intersect) # DELETE_ONLY_THIS_STRING
		
        intersect_curve_begin = dept_intersect[0]
        intersect_curve_end = dept_intersect[-1]
        unit_intersect = new_df.loc[id_intersect_curve]['Unit']

		# TODO: get this block into other function!!!
		#print(unit_start, unit_intersect)
        if str(unit_start) != str(unit_intersect): 
            self.status_loadlas.append(f"<font color=red>---WARNING! UNIT OF TWO CURVES IS NOT EQUAL! unit_start: , {unit_start}, unit_intersect: , {unit_intersect}</font>")
            if str(unit_start) == '%' and str(unit_intersect) == 'd.ed':
                print( '--TRANSFORM ded for %--')
                curve_intersect = curve_intersect*100
                unit_intersect = '%'
                new_df.loc[id_intersect_curve, 'Unit'] = '%'
            if str(unit_start) == 'd.ed' and str(unit_intersect) == '%':
                print( '--TRANSFORM % for ded--')
                curve_intersect = curve_intersect/100
                unit_intersect = 'd.ed'
                new_df.loc[id_intersect_curve, 'Unit'] = 'd.ed'
	
		# выделение пришиваемой (второй) кривой и ее нормализация
		#curve_start = curve_start.reshape(len(curve_start))
		#curve_intersect = curve_intersect.reshape(len(curve_intersect))
		
		# создание DataFrame с частями кривых, которые пересекаются, для создания обучающей выборки

        df1 = pd.DataFrame({'dept_start':dept_start, 'curve_start':curve_start})
        df2 = pd.DataFrame({'dept_intersect':dept_intersect, 'curve_intersect':curve_intersect})
		
        df_merged = pd.merge(left = df1, right = df2, left_on = 'dept_start', right_on = 'dept_intersect', how = 'inner')
        df_merged = df_merged.dropna()
		
		#print('ALLERT ', df_merged)
        if len(df_merged) < 6:
            print('Allert merge is empty')
	
		# создание обучающей выборки    
        y = np.array( np.round(df_merged['curve_intersect']-df_merged['curve_start'].tolist(), 2) )
        x = np.array( df_merged['curve_intersect'].tolist() )
        #print('----------------------Y', y)
        #print('----------------------X', x)
		
		# выполняем проверку, что обучающие данные ненулевые и обучение модели
        if len(x) == 0 or len(y) == 0: # если обучающие данные нулевые, то просто соединеям кривые
            print('BREAK', '   because y or x == 0!')
            df1 = pd.DataFrame({'dept':dept_start, 'curve':curve_start[:len(dept_start)]})
            list2 = np.where((dept_intersect) >= start_curve_end)
            df2 = pd.DataFrame({'dept':dept_intersect[list2], 'curve':curve_intersect[list2]})
            new_values_curve = pd.concat([df1, df2])
            new_values_curve = new_values_curve['curve'].tolist()
            new_step = new_df.loc[id_intersect_curve, 'Step']
            new_depth_curve = np.round(np.arange(start_curve_begin, 
                                                intersect_curve_end + new_step, 
                                                new_step),1)
            new_depth_curve = new_depth_curve.tolist()
            #print(start_index, new_df.loc[start_index, 'well_id'], )

            new_df.at[start_index, 'Data_curve'] = new_values_curve
            new_df.at[start_index, 'Depth_data'] = new_depth_curve
            new_df.loc[start_index, 'Start'] = start_curve_begin
            new_df.loc[start_index, 'Stop'] = intersect_curve_end
            new_df.loc[start_index, 'Step'] = new_step
            new_df = new_df.drop(id_intersect_curve)
            print('Return from crossing -- not crossing', type(new_values_curve))
            return new_df
		
		# если обучающая выборка ненулевая
        transformer_merge = RobustScaler(with_scaling=False).fit(y.reshape(len(y),1))
        y = transformer_merge.transform(y.reshape(len(y),1))
        q_25 = np.quantile(y, 0.40) # определение квантиля 0.25
        q_75 = np.quantile(y, 0.60) # определение квантиля 0.75
		#print('AVERAGE: ', np.average(y), 'min-max:', np.min(y), np.max(y))
		#print('MERGE:    ', q_25,  q_75)
        y[np.where(y>q_75)] = q_75 
        y[np.where(y<q_25)] = q_25
        print("XY_____len_____:", len(x), len(y))
	
        model = KNeighborsRegressor(n_neighbors = 5, weights = 'distance').fit(x.reshape(len(x),1), y)
        df_merged['Y'] = y
        df_merged['Pred'] = model.predict(x.reshape(len(x),1)).reshape(len(x))
		
		# вычисление значений второй кривой на основе обученной модели
        curve_intersect = np.nan_to_num(curve_intersect, nan=-9999)
        predict = np.round(model.predict(curve_intersect.reshape(len(curve_intersect), 1)), 4)
        predict = transformer_merge.inverse_transform(predict)
        predict = predict.flatten()
		
        curve_start = curve_start.reshape(len(curve_start), 1)
        curve_intersect = curve_intersect.reshape(len(curve_intersect), 1)
	
        curve_start = curve_start.reshape(len(curve_start))
        curve_intersect = curve_intersect.reshape(len(curve_intersect))
		
        curve_intersect = curve_intersect - predict
		# трансформация кривых в нормальный вид из нормализованного
        new_curve = np.hstack([curve_start, curve_intersect[np.where((dept_intersect) > start_curve_end)]])
        new_curve = new_curve.tolist()
        new_dept = np.hstack([dept_start, dept_intersect[np.where((dept_intersect) > start_curve_end)]])
        new_dept = new_dept.tolist()
        
        # заполняем данными строку со стартовой кривой
        new_df.at[start_index, 'Data_curve'] = new_curve
        new_df.at[start_index, 'Depth_data'] = new_dept
        new_df.loc[start_index, 'Start'] = start_curve_begin
        new_df.loc[start_index, 'Stop'] = intersect_curve_end
        new_df.loc[start_index, 'Step'] = step
		# удаляем запись о второй кривой
        new_df = new_df.drop(id_intersect_curve)
        print('------------------End crossing', type(new_curve))
        return new_df
	
    def select_shift(self, *list_param):
        print("!INTO_SELECT_SHIFT!")
        dept1, curve1, dept2, curve2 = list_param
        step = 0.2  # TODO: !! IMPORTANT !! todo choose step out of LAS
		
        df1 = pd.DataFrame({'dept1':dept1, 'curve1':curve1})
        df2 = pd.DataFrame({'dept2':dept2, 'curve2':curve2})
        df12_merged = pd.merge(left = df1, right = df2, left_on = 'dept1', right_on = 'dept2', how = 'inner')
        df12_merged = df12_merged.dropna()
		
        len_merge = df12_merged['dept1'].shape[0]
        size_shift = 25 #25 points - 5 meters
        if (len_merge + size_shift) < len(dept1): # проверяем не будет ли смещение больше длины кривой
            start_point = dept1[-(len_merge + size_shift)]
            end_point = dept1[-(len_merge - 40)]
        else:
			#print(dept1)
            start_point = np.array([x for x in dept2 if x == x]).min()
            end_point = np.array([x for x in dept1 if x == x]).max()
        print('Start and end points', start_point, end_point)
		
        mean_dict = {}
        try:
            shift_interval = np.round(np.arange(start_point, end_point+step, step), 2)
        except:
            print("ALERT! ERORR! NOT TRY IT!", df12_merged['dept2'].min(), df12_merged['dept1'].max())
            start_point = df12_merged['dept2'].min()
            end_point = df12_merged['dept1'].max()
            shift_interval = np.round(np.arange(start_point, end_point+step, step), 2)
		#print('SHIFT_INTERVAL: ', list(shift_interval))
		
        for point in shift_interval:
			#print("!TESTING!    difference: ", dept2[0]-point)
			#print("!TESTING! dept2: ", dept2)
            df_merged_intervals = None
            changed_dept2 = np.round(np.array(dept2+(dept2[0]-point)), 2)
			
            df1 = pd.DataFrame({'dept1':dept1, 'curve1':curve1})
            df2 = pd.DataFrame({'dept2':changed_dept2, 'curve2':curve2})
            df_merged_intervals = pd.merge(left = df1, right = df2, left_on = 'dept1', right_on = 'dept2', how = 'inner')
			#print("before", df_merged_intervals.shape)
			#print('CURVE1', df_merged_intervals['curve1'].tolist())
			#print('CURVE2', df_merged_intervals['curve2'].tolist())
            df_merged_intervals = df_merged_intervals.dropna()
			#print(point, '   ', len(list1[0]), len(list2[0]))
			#print("after", df_merged.shape)
            difference_list = list(np.round(df_merged_intervals['curve2']-df_merged_intervals['curve1'], 2))
			#print(f'Difference for {point}:', difference_list)
            if len(np.array( difference_list )) > 5: 
                mean = (np.array( difference_list ).max()-
						np.array( difference_list ).min())
            else:
                continue
			
            if np.isnan(mean):
                print("!!!!!!!!!!!ALERT!!!!!!!!:", (df_merged_intervals))
            else:
                mean_dict[mean] = np.round((dept2[0]-point), 2)
		
        ###print('mean_dict:', mean_dict)
        min_dif_list = list(mean_dict.keys())
        if len(np.array(min_dif_list)) != 0:
            min_dif = np.array(min_dif_list).min()
        else:
            print('!!Zero-array is it, dept2 not changing!!')
            return dept2
        ###print("!TESTING!    min_dif: ", min_dif)
		
        if min_dif in mean_dict: 
            difference = mean_dict[min_dif]
        dept2 = np.round(dept2, 2) + np.round(difference, 2)
        dept2 = np.round(dept2, 2)
        ###print('DIFFERENCE:', difference)
        return dept2
	
        """
		[['Omm', 'ohm.m'],
		['ohm.m', 'Omm'],
		['M', 'meters'],
		['d.ed', '%'],
		['%', 'd.ed'],
		['d.ed', '%'],
		['imp/min', 'imp./min'],
		['imp./min', 'imp/min'],
		['/', ''],
		['', '/'],
		['imp/min', '/'],
		['/', ''],
		['mcs', 'mks'],
		['mks', 'mcs'],
		['mcs', 'mks'],
		['mks', 'mcs'],
		['mcs/m', 'mks/m'],
		['mks/m', 'mcs/m'],
		['%', 'd.ed'],
		['d.ed', 'd/ed'],
		['gr/m', 'degC'],
		['degC', 'gr/m'],
		['/', '']]
        """
	# ----- END PASTED BLOCK -----

    
    
    def maxid(self, nametable, nameidfield):
        self.cursor.execute(f"SELECT {nameidfield} FROM {nametable};")
        list_id = self.cursor.fetchall()
        if list_id == []:
            max_num_id = 0
        else:
            max_num_id = np.array(list_id).max()
        return max_num_id
    
    def wellid(self, dict_well_name, well_name_folder,  well_name_inlas):
        #well_name
        self.cursor.execute("SELECT well_id, wellname FROM wells_wellheads")
        dict_wellid_wellname = self.cursor.fetchall()        
        dict_wellid_wellname = {line[1]:line[0] for line in dict_wellid_wellname}
        
        if well_name_inlas != well_name_folder:
            well_name_inlas = well_name_folder
            self.status_loadlas.append(f"<font color=red> !-- WARNING: Name of well in las {well_name_inlas} not equal name well of folder {well_name_folder}. Please pay attention to accessory informaton of well in las_file")
        else: 
            pass
        
        if well_name_inlas in dict_well_name:
            well_name_indb = dict_well_name[well_name_inlas]
            well_id = dict_wellid_wellname[well_name_indb]
        elif well_name_inlas in dict_wellid_wellname.keys():
            well_name_indb = well_name_inlas
            well_id = dict_wellid_wellname[well_name_indb]
        else:
            self.status_loadlas.append("<font color=red>Las is exist in table 'Wells_gis_curve', all operation canceled</font>")
            well_name_indb = None  
            well_id = None
            well_name_indb = None

        return well_id, well_name_indb
    
    def fix_lasfile(self, path_to_las_file):
        """Reading, finding problem strings, replacing it"""
        # TODO: fix promblem with start curve '~ASCII Log Data' for load in Petrel
        # TODO: fix promblem with fantom '-' in log data !!!
        edit_las = codecs.open(path_to_las_file, 'r', encoding='utf-8', errors='ignore')
        text = edit_las.read()
        text = text.replace("\r\n UWI .                                             :UNIQUE WELL ID\r\n", "\r\n")
        text = text.replace("FLD   ", "FLD.  ")
        #text = text.replace("~A DEPTH", "~ASCII Log Data ")
        #test = test.replace("ALT     ", "ALT.    ")
        #test = test.replace("DEPTH","DEPT ")
        with codecs.open(path_to_las_file, "w", encoding='utf-8', errors='ignore') as file_out:
            file_out.write(text)
        edit_las.close()
        self.status_loadlas.append(f"<font>Las-file {path_to_las_file} fixed successfully!</font>")
        return

    def reading_namewell(self, path_to_las_file):
        try:
            w = Well.from_las(path_to_las_file) # проходимся по каждому лас-файлу
            #print('::load_las_file::', w) # ::load_las_file:: Well(uwi: 'M38041TERS1S1', 1 curves: ['TS'])
        except:
            print(f'Erorr in load las-file {path_to_las_file}!!!!')
            return None, None
        # вытягиваем название скважины их пути к файлу!! Это необходимо для сравнения с заголовком в ласе (заголовки очень косячные!!)
        try:
            well_name_inlas = (str(w.header['name'])+' '+w.header['field']) # вытаскиваем из лас-файла название скважины
        except:
            well_name_inlas = str(w.header['name'])
        return w, well_name_inlas
    

if __name__ == "__main__":
    #import sys
    #app = QtWidgets.QApplication(sys.argv)
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()  
    window = LasindbWindow()
    window.get_parameters()
    window.show()
    sys.exit(app.exec())
