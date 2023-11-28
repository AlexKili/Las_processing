# coding=utf-8

"""
Main file of Las-loading module of big-project.
It's cutting code and placement in one module to free Pet-project.
Version 0.0.1

Before using this script you will need doing next actions:
    1) install python into your system
    2) assosiatе .py with python
    3) install next packages: 
    numpy, ploylt, xlsxwriter, PyQt5!!! PyQtWebEngine!!!
"""

import os
from PyQt5 import QtCore, QtWidgets, QtGui

import lasio

# for import settings
import configparser

# this need for plot_giscurve
from plotly.graph_objects import Figure, Scatter
from plotly.offline import plot

# import our internal tools
# not used in alpha-version
#import script_table_lasindb
#import script_table_exporttolas
#import script_settings
#import script_predict_lithology

# next block use for load PyQt library WebEngine
# this library needing for visualisation with plotly
# standart path for load this library not working!!
def webengine_hack():
    app = QtWidgets.QApplication.instance()
    if app is not None:
        import sip
        app.quit()
        sip.delete(app)
    import sys
    from PyQt5 import QtCore, QtWebEngineWidgets
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QtWidgets.qApp = QtWidgets.QApplication(sys.argv)
    return app
try:
    app = QtWidgets.QApplication([''])
    from PyQt5 import QtWebEngineWidgets
except ImportError as exception:
    app = webengine_hack()
    from PyQt5 import QtWebEngineWidgets

class FileSystemView(QtWidgets.QWidget):
    def __init__(self, dir_Path = None):
        super().__init__()
        # устанавливаем путь по умолчанию в корень диска C:
        # TODO: сделать загрузку пути из настроек или предыдущей сессии
        if dir_Path == None:
            dir_Path = 'C:\\'
        
        # установка опций для интерфейса 
        appWidth = 800
        appHeight = 300
        self.setWindowTitle('File System Viewer')
        self.setGeometry(300, 300, appWidth, appHeight)
        
        # установка модели и ее настройка
        self.dirModel = QtWidgets.QFileSystemModel()
        self.dirModel.setRootPath(dir_Path)  
        self.dirModel.setNameFilters(["*.las"])  # установка фильтра файлов по расширению
        self.dirModel.setNameFilterDisables(False)  # не показывать файлы не прошедшие фильтр
        
        # установка и настройка модели QTree
        self.tree =  QtWidgets.QTreeView()
        self.tree.setModel(self.dirModel)
        #self.tree.setRootIndex(self.dirModel.index(dir_Path))
        self.tree.setColumnWidth(0, 250)
        self.tree.setAlternatingRowColors(True)
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.hideColumn(3)
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)



class MainWindow(QtWidgets.QMainWindow):
    """This class is creating new windows with Table from DB"""
    
    #mysingal = QtCore.pyqtSignal(int, int)
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        print('MAINWINDOW INIT')
        
        self.las = None
        self.icon_style = 'standard'
        
        # БЛОК для загрузки иконок 
        if self.icon_style == 'stylish':
            iconOpen = QtGui.QIcon(os.path.dirname(__file__) + 'Main_app_icon.png')
            iconPlot = QtGui.QIcon(os.path.dirname(__file__) + '/icons/IconMenuBar/plot.png')
            iconConnect = QtGui.QIcon(os.path.dirname(__file__) + '/icons/IconMenuBar/connect_curves.png')
            iconExport = QtGui.QIcon(os.path.dirname(__file__) + '/icons/IconMenuBar/export.png')
            main_icon_app = QtGui.QIcon(os.path.dirname(__file__) + 'Main_app_icon.png')
            self.setWindowIcon(main_icon_app)
            
        elif self.icon_style == 'standard':
            iconOpen = self.style().standardIcon( QtWidgets.QStyle.SP_FileIcon )
            iconPlot = self.style().standardIcon( QtWidgets.QStyle.SP_DesktopIcon )
            iconConnect = self.style().standardIcon( QtWidgets.QStyle.SP_ToolBarHorizontalExtensionButton )
            iconExport = self.style().standardIcon( QtWidgets.QStyle.SP_FileDialogListView )
        
        
        # БЛОК для создания меню 
        self.menu = QtWidgets.QMenuBar() # its Menu
        self.menu_instr = self.menu.addMenu('Instruments') # adding Menu to form 
        self.menu_settings = self.menu.addMenu('Settings')
        
        self.menu_instr_openfile = QtWidgets.QAction(iconOpen, 'Open las-file') # create Action to adding in Menu to Open directory
        self.menu_instr_plotcurve = QtWidgets.QAction(iconPlot, 'Plot curve')
        self.menu_instr_connectcurve = QtWidgets.QAction(iconConnect, 'Connect many las')
        self.menu_instr_exporttoexcell = QtWidgets.QAction(iconExport, 'Export to excell')
        
        ## Подблок для создания сигналов и триггеров
        self.menu_instr_openfile.triggered.connect(self.menu_file_path) # Connect pressing Button to function open_dir
        self.menu_instr_plotcurve.triggered.connect(self.plot_curve) 
        self.menu_instr_exporttoexcell.triggered.connect(self.export_to_excellfile)
        
        ## Подблок для добавления пунктов в основне меню  
        self.menu_instr.addAction(self.menu_instr_openfile) # adding Action in Menu 
        self.menu_instr.addAction(self.menu_instr_plotcurve)
        self.menu_instr.addAction(self.menu_instr_connectcurve)
        self.menu_instr.addAction(self.menu_instr_exporttoexcell)
        
        self.setMenuBar(self.menu) # Добавляем основное меню в основное окно
        
        # БЛОК cоздания панели ToolBar 
        self.fileToolBar = QtWidgets.QToolBar("File", self)
        self.fileToolBar.addAction(self.menu_instr_openfile)
        self.fileToolBar.addAction(self.menu_instr_plotcurve)
        self.fileToolBar.addAction(self.menu_instr_connectcurve)
        self.fileToolBar.addAction(self.menu_instr_exporttoexcell)
        self.addToolBar(self.fileToolBar)
        
        
        # БЛОК для создания виджета прикрепляемого слева, для файловой системы
        self.dock = QtWidgets.QDockWidget("File system", self)
        self.listWiget = FileSystemView()
        self.dock.setWidget(self.listWiget)
        self.setCentralWidget(QtWidgets.QTextEdit())
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dock)
        ## self.dock.setFloating(False)
        ## установка сигналов
        self.listWiget.tree.clicked.connect(self.docker_file_path)
        
        
        # БЛОК для создания центральной таблицы
        self.tab_widget = QtWidgets.QTabWidget()  # создает экземпляр класса, который создает вкладки (далее им будут присвоены названия таблиц выбранных по запросу)
        #self.tab_widget.setTabShape(1)  # делает вкладки треугольными если необходимо
        self.tableview = QtWidgets.QTableView()  # создает экземпляр класса для отображения данных в виде таблицы
        self.tableview_model = QtGui.QStandardItemModel()  # создает табличную модель
        self.tab_widget.tabBarClicked.connect(self.tab_select)

        self.setCentralWidget(self.tab_widget) # устанавливает центральный виджет -- таблицу
        
        # БЛОК запуска необходимых функций для создания и заполнения основной таблицы
        #self.load_settings()
        #self.open_temp_file()  # запускает функцию для открытия временного файла и выборки необходимых данных для запроса
        #self.open_las_file()  # создает соединение с БД
        #self.table_fill()  # заполнение формы(таблицы) данными
        
        # 
        self.tab_name = ['Header', 'Data_curves', 'Viewer'] # названия вкладок
        # фомируем вкладку с данными из las-файла 
        # вклада 'Header' будет содержать таблицу
        # ниже приведен блок в котором формируется QTableView
        #  
        self.table = QtWidgets.QTableView()
        self.table_model = QtGui.QStandardItemModel()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(1) 
        self.table.setTextElideMode(1)
        self.table.resizeRowToContents(0)
        self.table.setSortingEnabled(False)  # запрещает сортировку элеметов в таблице
        
        
        


    def docker_file_path(self, path):
        """ считывание пути выбранных файлов
        path - PyQt5.QtCore.QModelIndex object
        """
        #text = self.listWiget.dirModel.data(path)  # название файла 
        file_path = self.listWiget.dirModel.filePath(path)  # полный путь к файлу
        if str(file_path).endswith('.las'):
            file_path = file_path.replace('/', '\\')
            self.open_las_file(path_las_file=file_path)


    def menu_file_path(self):
        """This function called after clicked button 'Browse' and 
        take path to directory with las-files"""
        #print("get_path_las")#FOR_TEST
        file_path = QtWidgets.QFileDialog.getOpenFileName(parent=self, caption="Выбор las-файла...", directory=os.path.dirname(__file__), filter='Las-file (*.las);;Txt-file (*.txt);;All-files (*)')
        file_path = file_path[0]
        print('PATH   ', file_path)#FOR_TEST
        
        if file_path == '':
            self.statusBar().showMessage("Please, set the path of las file")
        else:
            file_path = file_path.replace('/', '\\')
            self.statusBar().showMessage(f"loading las file is {file_path}")
            self.setWindowTitle("Las-file processing" + ' || ' + file_path) 
            self.path_to_save = file_path
            print(self.tab_widget.count())
            
            # очищаем вкладки, если они были открыты до этого
            if self.tab_widget.count() > 0:
                self.tab_widget.clear()
        
        self.open_las_file(path_las_file=file_path)
    
    def open_las_file(self, path_las_file):
        # очищаем вкладки, если они были открыты до этого
        #if self.tab_widget.count() > 0:
        #    self.tab_widget.clear()
        
        # попытка открыть las - файл, еслине получиться в строку состояние выведется сообщение
        # TODO: при неудаче при открытии файла выводить информационное окошко
        
        try:
            self.las = lasio.read(path_las_file)
        except:
            self.statusBar().showMessage("Error - las-file not load")
            QtWidgets.QMessageBox.information(self, 
                                            'Information', 
                                            'Las-file is not opened, try later',
                                            buttons=QtWidgets.QMessageBox.Ok, 
                                            defaultButton=QtWidgets.QMessageBox.Ok)
            return
        
        
        # получаем список значений и кривых из las
        las_df = self.las.df() 
        las_df[las_df.index.name] = las_df.index
        
        # меняем порядок столбцов и ставим на первое место глубину
        columnname = list( las_df.columns )
        columnname.insert(0, columnname.pop(columnname.index(las_df.index.name)))
        las_df = las_df.loc[:, columnname]  
        
        value = []
        for count, row in las_df.iterrows():  # каждое значение в списке элементов обертывает в QStandartItem
            value = [QtGui.QStandardItem(str(element)) for element in row.values] # каждый элемент строки нужно обернуть в QStandardItem и в модель подавать строку из этих обернутых элементов
            self.table_model.appendRow(value)  # затем формирует новый список в модели из экземпляров QStandartItem
        
        self.table_model.setHorizontalHeaderLabels(columnname)  # установить в модели названия колонок
        self.table.setModel(self.table_model)  # установить модель в таблицу
        
        self.tab_widget.addTab(self.table, 'Data_curves')  # добавляем вкладку 'Data_Curves' с виджетом table
        self.tableview.setModel(self.tableview_model)  # 
        
        
        # формируем тектовую модель для второй вкладки
        text = QtWidgets.QTextEdit()
        #text.setText(str(las.header))
        # TODO: write our driver to formating header as html
        import dict_and_html
        result_dict = {}
        list_keys_headeritem = ['mnemonic', 'unit', 'value', 'descr']
        list_keys_curves = ['mnemonic', 'unit', 'value', 'descr', 'original_mnemonic', 'data.shape']
        for key in self.las.header.keys():
            if key != 'Curves':
                header = self.las.header[key]
                header_dict = {}
                for count, item in enumerate(header):
                    dict_mnemonic={}
                    for name in list_keys_headeritem:
                        dict_mnemonic[name] = item[name]
                    header_dict[count] = dict_mnemonic
                result_dict[key] = header_dict
        
        text.setHtml(dict_and_html.dict_and_html(result_dict))
        self.tab_widget.addTab(text, 'Header')  # добавить вкладку 'Headers' с виджетом text
        
        return
    
    
    def plot_curve(self):
        print('plot_curve init')
        if self.las is None:
            QtWidgets.QMessageBox.information(self, 
                                            'Information', 
                                            'Please open las-file',
                                            buttons=QtWidgets.QMessageBox.Ok, 
                                            defaultButton=QtWidgets.QMessageBox.Ok)
            return
        
        self.plotcurvewindow = QtWidgets.QWidget(window, QtCore.Qt.Window)
        self.plotcurvewindow.setWindowTitle("Отображение кривых ГИС")
        self.plotcurvewindow.resize(800,600)
        self.plotcurvewindow.setWindowModality(QtCore.Qt.WindowModal)
        self.plotcurvewindow.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        # создаем представление QWebEngineView и устанавливаем в него html код
        self.plot_widget = QtWebEngineWidgets.QWebEngineView()
        
        # создаем список элементов для выпадающего списка кривых для отображения 
        # удаляем из списка кривую глубины!!!! 
        self.dict_curves = {element['mnemonic']:element['unit'] for element in self.las.curves} 
        if 'DEPT' in self.dict_curves:
            self.depth_unit = self.dict_curves['DEPT']
            del self.dict_curves['DEPT']
        elif 'DEPTH' in self.dict_curves:
            self.depth_unit = self.dict_curves['DEPTH']
            del self.dict_curves['DEPTH']
            
        self.combo_box = QtWidgets.QComboBox(self) 
        self.combo_box.setGeometry(200, 150, 120, 30)
        self.combo_box.addItems(list(self.dict_curves.keys()))
        self.combo_box.currentIndexChanged.connect(self.change_curve)
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.combo_box)
        vbox.addWidget(self.plot_widget)
        
        
        self.change_curve(0)
        
        self.plotcurvewindow.setLayout(vbox)
        self.plotcurvewindow.show()
    
    def change_curve(self, string):
        print(string)
        print(list(self.dict_curves.keys())[string])
        name_curve = list(self.dict_curves.keys())[string]
        unit = self.dict_curves[name_curve]
        self.las.df()[name_curve]
        # create the plotly figure
        fig = Figure(Scatter(x=self.las.df()[name_curve], y=self.las.df().index))
        fig.update_layout(title=str(name_curve),
                          xaxis_title=str(name_curve)+', '+str(unit),
                          yaxis_title=f"Depth, {self.depth_unit }",
                          yaxis = dict(autorange="reversed"),
                          margin=dict(l=0, r=0, t=30, b=0),
                          template="plotly_white",
                          paper_bgcolor='white', 
                          plot_bgcolor='white')
        
        # we create html code of the figure
        html = '<html><body>'
        html += plot(fig, output_type='div', include_plotlyjs='cdn')
        html += '</body></html>'
        self.plot_widget.setHtml(html)
        return
    
    
    def tab_select(self, index):
        # It's for test
        #print('INDEX:', index)
        #print(self.tab_name[index])
        pass


    def export_to_excellfile(self):
        print('open_dir init')
        if self.las is None:
            QtWidgets.QMessageBox.information(self, 
                                            'Information', 
                                            'Please open las-file',
                                            buttons=QtWidgets.QMessageBox.Ok, 
                                            defaultButton=QtWidgets.QMessageBox.Ok)
            return
        self.path_to_save.replace('.las', '.xlsx')
        self.las.to_excel(self.path_to_save+'.xlsx')




if __name__=="__main__":
    import sys
    print('BASE INIT')
    #app = QtWidgets.QApplication(sys.argv)  # создает объект приложения в виде объекта QApplication,
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance() 
    app.setStyle("Fusion")
    
    # доступ к нему осуществляется через атрибут qApp из модуля QtWidgets
    window = MainWindow()  # создает объект окна в виде экземляра класса Qwidget
    window.setWindowTitle("Las-file processing")  # задает текст, который будет выводиться в заголовке окна  Информация об объектах
    
    # Создание строки состояния 
    window.statusBar().showMessage("ready to load file") 
    window.resize(1024, 800)  # задает минимальные размеры окна, первый параметр - ширина, второй - высота
    # эти размеры являются рекомендацией, если объекты не будут помещатся в окне, то оно будет увеличено
    window.show()  # выводит на экран окно и все компоненты, которые мы ранее в него добавили
    sys.exit(app.exec_())  # запускает бесконечный цикл обработки событий в приложении
    # код после этого выражения будет выполнен только после завершения работы приложения
    