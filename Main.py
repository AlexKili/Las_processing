# coding=utf-8

"""
Main file of Las-loading module of big-project.
It's cutting code and placement in one module to free Pet-project.
Version 0.0.3

Before using this script you will need doing next actions:
    1) install python into your system
    2) assosiatе .py with python
    3) install next packages: 
    numpy, ploylt, xlsxwriter, PyQt5!!! PyQtWebEngine!!!
"""

import os
from PyQt5 import QtCore, QtWidgets, QtGui

import lasio
import io
import csv

# for import settings
#import configparser

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


class AddWellDialog(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setWindowTitle('Add new well to project')
        self.vbox = QtWidgets.QVBoxLayout()
        
        self.name_well = "Name well"
        self.coordinate_x = 0
        self.coordinate_y = 0
        self.type_altitude = "Kelly bushing"
        self.list_type_altitude = ["Kelly bushing", "Ground level", "Rotary table", "Drill floor"]
        self.elevation_altitude = 0
        self.bottommd = 0
        
        # Блок для задания названия скважины
        self.name_well_group = QtWidgets.QHBoxLayout()
        self.name_well_group.addWidget( QtWidgets.QLabel("Name well: ") )
        self.name_well_lineedit = QtWidgets.QLineEdit(str(self.name_well))
        self.name_well_group.addWidget(self.name_well_lineedit)
        
        # TODO: блок для введения типа скважины
        
        # Блок для введения координат
        self.coordinate_group = QtWidgets.QHBoxLayout()
        self.coordinate_group.addWidget( QtWidgets.QLabel("Well head X: ") )
        self.coordinate_x_lineedit = QtWidgets.QLineEdit(str(self.coordinate_x))
        self.coordinate_group.addWidget(self.coordinate_x_lineedit)
        self.coordinate_group.addWidget( QtWidgets.QLabel("Well head Y: ") )
        self.coordinate_y_lineedit = QtWidgets.QLineEdit(str(self.coordinate_y))
        self.coordinate_group.addWidget(self.coordinate_y_lineedit)
        #verticalSpacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        
        # Блок для введения альтитуды стола ротора
        self.altitude_group = QtWidgets.QVBoxLayout()
        self.type_altitude_group = QtWidgets.QHBoxLayout()
        self.type_altitude_group.addWidget( QtWidgets.QLabel("Well datum name: ") )
        self.type_altitude_combo = QtWidgets.QComboBox()
        for element in self.list_type_altitude:
            self.type_altitude_combo.addItem(element)
        self.type_altitude_group.addWidget(self.type_altitude_combo)
        
        self.elevation_altitude_group = QtWidgets.QHBoxLayout()
        self.elevation_altitude_group.addWidget( QtWidgets.QLabel("Elevation: ") )
        self.elevation_altitude_lineedit = QtWidgets.QLineEdit(str(self.elevation_altitude))
        self.elevation_altitude_group.addWidget(self.elevation_altitude_lineedit)
        
        self.altitude_group.addLayout(self.type_altitude_group)
        self.altitude_group.addLayout(self.elevation_altitude_group)
        
        # Блок для указания глубины забоя
        self.bottommd_group = QtWidgets.QHBoxLayout()
        self.bottommd_group.addWidget( QtWidgets.QLabel("Bottom MD: ") )
        self.bottommd_lineedit = QtWidgets.QLineEdit(str(self.bottommd))
        self.bottommd_group.addWidget(self.bottommd_lineedit)
        
        # Блок для создания основных кнопок внизу 
        self.button_group = QtWidgets.QHBoxLayout()
        self.button_cancel = QtWidgets.QPushButton("Cancel")
        self.button_apply = QtWidgets.QPushButton("Apply")
        self.button_group.addWidget(self.button_cancel)
        self.button_group.addWidget(self.button_apply)
        
        # Добавляем все группы на основной Vbox widget 
        self.vbox.addItem(self.name_well_group)
        self.vbox.addItem(self.coordinate_group)
        self.vbox.addItem(self.altitude_group)
        self.vbox.addItem(self.bottommd_group)
        self.vbox.addItem(self.button_group)
        
        # Добавляем основнйо Vbox widget на основной слой для отображения 
        self.setLayout(self.vbox)
        
        # добавляем сигналы к элементам
        self.signals()
    
    def signals(self):
        self.name_well_lineedit.editingFinished.connect(self.name_well_changed) # if need use textChanged signal for change text in real time
        self.coordinate_x_lineedit.editingFinished.connect(self.coordinate_x_changed)
        self.coordinate_y_lineedit.editingFinished.connect(self.coordinate_y_changed)
        self.type_altitude_combo.activated.connect(self.type_altitude_changed)
        self.elevation_altitude_lineedit.editingFinished.connect(self.elevation_changed)
        self.bottommd_lineedit.editingFinished.connect(self.bottommd_changed)
        self.button_cancel.pressed.connect(self.close)
        self.button_apply.pressed.connect(self.apply_addwell)
    
    def name_well_changed(self):
        self.name_well = str(self.name_well_lineedit.text())
        print(self.name_well)
        
    def coordinate_x_changed(self):
        try:
            self.coordinate_x = float(self.coordinate_x_lineedit.text())
        except:
            self.coordinate_x_lineedit.setText("Enter a number, not a string")
    
    def coordinate_y_changed(self):
        try:
            self.coordinate_y = float(self.coordinate_y_lineedit.text())
        except:
            self.coordinate_y_lineedit.setText("Enter a number, not a string")
    
    def type_altitude_changed(self, index):
        self.type_altitude = self.list_type_altitude[index]
    
    def elevation_changed(self):
        try:
            self.elevation_altitude = float(self.elevation_altitude_lineedit.text())
        except:
            self.elevation_altitude_lineedit.setText("Enter a number, not a string")
    
    def bottommd_changed(self):
        try:
            self.bottommd = float( self.bottommd_lineedit.text() )
        except:
            self.bottommd_lineedit.setText("Enter a number, not a string")
    
    
    def apply_addwell(self):
        pass
    

class FileSystemView(QtWidgets.QWidget):
    """Класс создающий QtWidget для отображения файловой системы
    
    Returns:
        _type_: _description_
    """
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


class TabWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.tab_name = ['Header', 'Data_curves', 'Viewer'] # названия вкладок
        
        self.tab_widget = QtWidgets.QTabWidget()  # создает экземпляр класса, который создает вкладки (далее им будут присвоены названия таблиц выбранных по запросу)
        #self.tab_widget.setTabShape(1)  # делает вкладки треугольными если необходимо
        
        # БЛОК для создания вкладки Header
        self.text_header = QtWidgets.QTextEdit()
        self.tab_widget.addTab(self.text_header, 'Header')  # добавить вкладку 'Headers' с виджетом text
        
        # БЛОК для создания вкладки Data_curves
        # фомируем вкладку с данными из las-файла 
        # вклада 'Header' будет содержать таблицу
        # ниже приведен блок в котором формируется QTableView 
        self.table = QtWidgets.QTableView() # создает экземпляр класса для отображения данных в виде таблицы
        self.tableview_model = QtGui.QStandardItemModel()  # создает табличную модель
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)  # делает четные-нечетные строки разным цветом
        self.table.setSelectionBehavior(1)  # задает режим выделения элементво в таблице
        self.table.setTextElideMode(1)  # задает режим обрезки текста если он не помещается
        self.table.resizeRowToContents(0)  # изменяет размер строк, чтобы все поместилось
        self.table.setSortingEnabled(False)  # запрещает сортировку элеметов в таблице
        self.table.setCornerButtonEnabled(True)  # в левом углу можно выделить всю таблицу
        ## создает событие для ctrl+С позволяющее скопировать таблицу
        self.table.installEventFilter(self)
        
        self.tab_widget.addTab(self.table, 'Data_curves')  # добавляем вкладку 'Data_Curves' с виджетом table
        
        self.tab_widget.tabBarClicked.connect(self.tab_select) # устанавливаем сигналы
        
        self.plotcurvewindow = QtWidgets.QWidget(self, QtCore.Qt.Window)
        
        # создаем представление QWebEngineView и устанавливаем в него html код
        self.plot_widget = QtWebEngineWidgets.QWebEngineView()
        
        # создаем список элементов для выпадающего списка кривых для отображения 
        self.combo_box = QtWidgets.QComboBox(self) 
        self.combo_box.setGeometry(200, 150, 120, 30)
        
        ## устанавливаем сигналы
        #self.combo_box.currentIndexChanged.connect(self.change_curve)
        
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.combo_box)
        vbox.addWidget(self.plot_widget)
        
        self.plotcurvewindow.setLayout(vbox)
        self.tab_widget.addTab(self.plotcurvewindow, 'Viewer')
        #self.plotcurvewindow.show()
        
    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.KeyPress and
            event.matches(QtGui.QKeySequence.Copy)):
            self.copySelection()
            return True
        return super(QtWidgets.QWidget, self).eventFilter(source, event)
    
    def copySelection(self):
        selection = self.table.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            rowcount = rows[-1] - rows[0] + 1
            colcount = columns[-1] - columns[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]
            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                table[row][column] = index.data()
            stream = io.StringIO()
            csv.writer(stream, delimiter=";").writerows(table)
            QtWidgets.QApplication.clipboard().setText(stream.getvalue())
    
    def tab_select(self, index):
        # It's for next update
        #print('INDEX:', index)
        #print(self.tab_name[index])
        pass


class PlotCurveWindow(QtWidgets.QWidget):
    def __init__(self, window):
        super().__init__()
        self.plotcurvewindow = QtWidgets.QWidget(window, QtCore.Qt.Window)
        self.plotcurvewindow.setWindowTitle("Отображение кривых ГИС")
        self.plotcurvewindow.resize(800,600)
        self.plotcurvewindow.setWindowModality(QtCore.Qt.WindowModal)
        self.plotcurvewindow.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        # создаем представление QWebEngineView и устанавливаем в него html код
        self.plot_widget = QtWebEngineWidgets.QWebEngineView()
        
        self.combo_box = QtWidgets.QComboBox(self) 
        self.combo_box.setGeometry(200, 150, 120, 30)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.combo_box)
        vbox.addWidget(self.plot_widget)
        self.plotcurvewindow.setLayout(vbox)
        
    
    def plot_curve(self):
        self.las = window.las
        
        if self.las is None:
            QtWidgets.QMessageBox.information(self, 
                                            'Information', 
                                            'Please open las-file',
                                            buttons=QtWidgets.QMessageBox.Ok, 
                                            defaultButton=QtWidgets.QMessageBox.Ok)
            return
        # создаем список элементов для выпадающего списка кривых для отображения 
        # удаляем из списка кривую глубины
        self.dict_curves = {element['mnemonic']:element['unit'] for element in self.las.curves} 
        if 'DEPT' in self.dict_curves:
            self.depth_unit = self.dict_curves['DEPT']
            del self.dict_curves['DEPT']
        elif 'DEPTH' in self.dict_curves:
            self.depth_unit = self.dict_curves['DEPTH']
            del self.dict_curves['DEPTH']
        
        self.combo_box.addItems(list(self.dict_curves.keys()))
        self.combo_box.currentIndexChanged.connect(self.change_curve)
        
        self.change_curve(0)
        self.plotcurvewindow.show()

        
    def change_curve(self, string):
        name_curve = list(self.dict_curves.keys())[string]
        unit = self.dict_curves[name_curve]
        self.las.df()[name_curve]
        # create the plotly figure
        fig = Figure(Scatter(x=self.las.df()[name_curve], y=self.las.df().index))
        fig.update_layout(title=str(name_curve),
                            xaxis_title=str(name_curve)+', '+str(unit),
                            yaxis_title=f"Depth, {self.depth_unit}",
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


class LasLoadingThread(QtCore.QThread):
    state = QtCore.pyqtSignal(bool)
    result = QtCore.pyqtSignal(list)
    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.parent = parent
        
    def __del__(self):
        self.wait()
    
    @QtCore.pyqtSlot(list)
    def run(self):
        try:
            print('load las begin')
            self.las = lasio.read(self.parent.path_las_file)
            print('end loading')
            self.state.emit(True)
        except:
            self.state.emit(False)
            return
        
        las_header = self.load_header(las_file=self.las)
        columnname, values  = self.load_lasdf(self.las)
        self.result.emit([self.las, las_header, columnname, values])
        
    def load_header(self, las_file):
        """Заполнение текстовой модели вкладки Header

        Args:
            las_file (LasFile): открытый las-файл в lasio
        """
        las_header = "~~~~~~WELL SECTION~~~~~~\n" + str(las_file.well) \
                + "\n\n\n~~~~~~CURVES SECTION~~~~~~\n" + str(las_file.curves) \
                    + "\n\n\n~~~~~~PARAMETERS SECTION~~~~~~\n" +str(las_file.params) \
                        + "\n\n\n~~~~~~OTHER SECTION~~~~~~\n" + str(las_file.other)
        
        # TODO: write our driver to formating header as html
        #self.tab_widget.addTab(self.text_header, 'Header')  # добавить вкладку 'Headers' с виджетом text
        return las_header
    
    def load_lasdf(self, las_file):
        """Заполнение табличной модели вкладки Data_curves

        Args:
            las_file (LasFile): открытый las-файл в lasio
        """
        las_df = las_file.df() 
        las_df[las_df.index.name] = las_df.index
        
        # меняем порядок столбцов и ставим на первое место глубину
        columnname = list( las_df.columns )
        columnname.insert(0, columnname.pop(columnname.index(las_df.index.name)))
        las_df = las_df.loc[:, columnname]  
        
        values = []
        for count, row in las_df.iterrows():  # каждое значение в списке элементов обертывает в QStandartItem
            row = [QtGui.QStandardItem(str(element)) for element in row.values] # каждый элемент строки нужно обернуть в QStandardItem и в модель подавать строку из этих обернутых элементов
            values.append(row)
            
        return columnname, values


class MainWindow(QtWidgets.QMainWindow):
    """ Создает основное окно приложения для загрузки и визуализации las-файла
    """
    
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        print('MAINWINDOW INIT')
        
        self.las = None
        self.icon_style = 'standard' # TODO: get this parameter from settings.ini
        
        # БЛОК для загрузки иконок 
        if self.icon_style == 'stylish':
            iconAdd = self.style().standardIcon( QtWidgets.QStyle.SP_FileDialogNewFolder )
            iconOpen = QtGui.QIcon(os.path.dirname(__file__) + 'Main_app_icon.png')
            iconPlot = QtGui.QIcon(os.path.dirname(__file__) + '/icons/IconMenuBar/plot.png')
            iconConnect = QtGui.QIcon(os.path.dirname(__file__) + '/icons/IconMenuBar/connect_curves.png')
            iconExport = QtGui.QIcon(os.path.dirname(__file__) + '/icons/IconMenuBar/export.png')
            main_icon_app = QtGui.QIcon(os.path.dirname(__file__) + 'Main_app_icon.png')
            self.setWindowIcon(main_icon_app)
            
        elif self.icon_style == 'standard':
            iconAdd = self.style().standardIcon( QtWidgets.QStyle.SP_FileDialogNewFolder )
            iconOpen = self.style().standardIcon( QtWidgets.QStyle.SP_FileIcon )
            iconPlot = self.style().standardIcon( QtWidgets.QStyle.SP_DesktopIcon )
            iconConnect = self.style().standardIcon( QtWidgets.QStyle.SP_ToolBarHorizontalExtensionButton )
            iconExport = self.style().standardIcon( QtWidgets.QStyle.SP_FileDialogListView )
        
        # БЛОК для создания меню 
        self.menu = QtWidgets.QMenuBar() # its Menu
        self.menu_instr = self.menu.addMenu('Instruments') # adding Menu to form 
        self.menu_settings = self.menu.addMenu('Settings')
        
        self.menu_instr_addwell = QtWidgets.QAction(iconAdd, 'Add new well')
        self.menu_instr_openfile = QtWidgets.QAction(iconOpen, 'Open las-file') # create Action to adding in Menu to Open directory
        self.menu_instr_plotcurve = QtWidgets.QAction(iconPlot, 'Plot curve')
        self.menu_instr_connectcurve = QtWidgets.QAction(iconConnect, 'Connect many las')
        self.menu_instr_exporttoexcell = QtWidgets.QAction(iconExport, 'Export to excell')
        
        ## Подблок для создания сигналов и триггеров
        self.menu_instr_addwell.triggered.connect(self.add_new_well)
        self.menu_instr_openfile.triggered.connect(self.menu_file_path) # Connect pressing Button to function open_dir
        self.plotcurve = PlotCurveWindow(self)
        self.menu_instr_plotcurve.triggered.connect(self.plotcurve.plot_curve) 
        self.menu_instr_exporttoexcell.triggered.connect(self.export_to_excellfile)
        
        ## Подблок для добавления пунктов в основне меню  
        self.menu_instr.addAction(self.menu_instr_openfile) # adding Action in Menu 
        self.menu_instr.addAction(self.menu_instr_plotcurve)
        self.menu_instr.addAction(self.menu_instr_connectcurve)
        self.menu_instr.addAction(self.menu_instr_exporttoexcell)
        
        self.setMenuBar(self.menu) # Добавляем основное меню в основное окно
        
        # БЛОК cоздания панели ToolBar 
        self.fileToolBar = QtWidgets.QToolBar("File", self)
        self.fileToolBar.addAction(self.menu_instr_addwell)
        self.fileToolBar.addAction(self.menu_instr_openfile)
        self.fileToolBar.addAction(self.menu_instr_plotcurve)
        self.fileToolBar.addAction(self.menu_instr_connectcurve)
        self.fileToolBar.addAction(self.menu_instr_exporttoexcell)
        self.addToolBar(self.fileToolBar)
        
        # БЛОК для создания виджета прикрепляемого слева, для файловой системы
        self.dockFilesystem = QtWidgets.QDockWidget("File system", self)
        self.listWidget = FileSystemView()  # загружаем класс FileSystemView
        self.dockFilesystem.setWidget(self.listWidget)  # устанавливаем его в боковую панель
        self.setCentralWidget(QtWidgets.QTextEdit())
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockFilesystem)
        ## self.dockFilesystem.setFloating(False)
        ## установка сигналов
        self.listWidget.tree.clicked.connect(self.docker_file_path)
        
        # БЛОК для создания виджета со списком кривых, прикрепляемого слева
        self.dockCurveslist = QtWidgets.QDockWidget("Curves in list", self)
        self.listCurveslist = QtWidgets.QTextEdit()  # загружаем класс FileSystemVi
        self.dockCurveslist.setWidget(self.listCurveslist)  # устанавливаем его в боковую панель
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockCurveslist)
        ## self.dockFilesystem.setFloating(False)
        ## установка сигналов
        self.listWidget.tree.clicked.connect(self.docker_file_path)
        
        # БЛОК для создания центральной таблицы
        centralWidget = QtWidgets.QMdiArea()
        self.setCentralWidget(centralWidget)
        self.tabWidget = TabWidget()
        subWindow_TabWidget = centralWidget.addSubWindow(self.tabWidget.tab_widget)
        subWindow_TabWidget.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        subWindow_TabWidget.show()
        
        
        # БЛОК для создания progressBar 
        self.progressBar = QtWidgets.QProgressBar()
        self.statusBar().addPermanentWidget(self.progressBar)
        self.progressBar.hide()
        
        
        # БЛОК запуска необходимых функций для создания и заполнения основной таблицы
        # TODO: сделать функции доступными после бета-релиза с новым интерфесом
        #self.load_settings()
        #self.open_temp_file()  # запускает функцию для открытия временного файла и выборки необходимых данных для запроса
        #self.open_las_file()  # создает соединение с БД
        #self.table_fill()  # заполнение формы(таблицы) данными
        
    def add_new_well(self):
        dialog_add_new_well = AddWellDialog()
        dialog_add_new_well.setModal(True)
        dialog_add_new_well.resize(400,200)        
        dialog_add_new_well.exec_()
        
    def docker_file_path(self, path):
        """Cчитывание пути выбранных файлов в FileSystemView
        
        Args:
            path (PyQt5.QtCore.QModelIndex object): index of object
        
        Returns:
            none: none
        """
        
        # очищаем виджеты во вкладках
        self.tabWidget.text_header.clear()
        self.tabWidget.tableview_model.clear()
        self.tabWidget.combo_box.clear()
        self.tabWidget.table.setModel(self.tabWidget.tableview_model)
        self.tabWidget.plot_widget.setHtml('<html><body>  </body></html>')
        
        # получаем данные о файле из выделенного элемента
        name_file = self.listWidget.dirModel.data(path)  # название файла
        file_path = self.listWidget.dirModel.filePath(path)  # полный путь к файлу
        if str(file_path).lower().endswith('.las'):
            file_path = file_path.replace('/', '\\')
            
            self.open_las_file(path_las_file=file_path)
        
        # Показать progress bar
        #self.progressBar.setFixedSize(self.geometry().width() - 120, 16) # опция если нужен фиксированный размер progress bar
        self.progressBar.show()
        self.statusBar().showMessage(f"loading file {name_file}...", 0)
        self.progressBar.setRange(0, 0)
        
        return
    
    def menu_file_path(self):
        """Эта функция вызывается после нажатия кнопки 'Browse' и позволяет выбрать путь к las-файлам"""
        
        file_path = QtWidgets.QFileDialog.getOpenFileName(parent=self, caption="Выбор las-файла...", directory=os.path.dirname(__file__), filter='Las-file (*.las);;Txt-file (*.txt);;All-files (*)')
        file_path = file_path[0]
        
        if file_path == '':
            self.statusBar().showMessage("Please, set the path of las file")
        else:
            file_path = file_path.replace('/', '\\')
            self.statusBar().showMessage(f"loading las file is {file_path}")
            self.setWindowTitle("Las-file processing" + ' || ' + file_path) 
            self.path_to_save = file_path
            
        self.open_las_file(path_las_file=file_path)
        
        # Показать progress bar
        #self.progressBar.setFixedSize(self.geometry().width() - 120, 16) # опция если нужен фиксированный размер progress bar
        self.progressBar.show()
        self.statusBar().showMessage(f"loading file ...", 0)
        self.progressBar.setRange(0, 0)
        
    
    def open_las_file(self, path_las_file):
        """Открывает las-файл и передает в функции дальше для его отображения
        
        Args:
            path_las_file (str): полный путь к файлу
        
        Returns:
            Boolean: состояние открытия фала
        """
        # попытка открыть las - файл, еслине получиться в строку состояние выведется сообщение
        self.path_las_file = path_las_file
        lasloadThread = LasLoadingThread(parent = self)
        lasloadThread.start()
        lasloadThread.state.connect(self.state_reading)
        lasloadThread.result.connect(self.result_reading)
    
    def state_reading(self, state):
        self.state = state
        if self.state is False:
            QtWidgets.QMessageBox.information(self, 
                                            'Information', 
                                            'Please open las-file',
                                            buttons=QtWidgets.QMessageBox.Ok, 
                                            defaultButton=QtWidgets.QMessageBox.Ok)
    
    def result_reading(self, list_las_data):
        if self.state is True:
            #self.view_lasdf(self.las)
            self.view_curves(list_las_data)
            return True
        
    
    def view_curves(self, list_las_data):
        self.las, las_header, columnname, values = list_las_data
        
        # устанавливаем header в  вкладку header
        self.tabWidget.text_header.setText(str(las_header))
        
        # устанавливаем табличку с значениями кривых в вкладку data 
        [self.tabWidget.tableview_model.appendRow(row) for row in values] # каждый элемент строки нужно обернуть в QStandardItem и в модель подавать строку из этих обернутых элементов
        self.tabWidget.tableview_model.setHorizontalHeaderLabels(columnname)  # установить в модели названия колонок
        self.tabWidget.table.setModel(self.tabWidget.tableview_model)  # установить модель в таблицу

        
        # устанавливаем отображение кривых в вкладку viewer
        ## очищаем combo box
        self.tabWidget.combo_box.clear()
        ## создаем список элементов для выпадающего списка кривых для отображения
        self.dict_curves = {element['mnemonic']:element['unit'] for element in self.las.curves} 
        if 'DEPT' in self.dict_curves:
            self.depth_unit = self.dict_curves['DEPT']
            del self.dict_curves['DEPT']
        elif 'DEPTH' in self.dict_curves:
            self.depth_unit = self.dict_curves['DEPTH']
            del self.dict_curves['DEPTH']
            
        self.listCurveslist.setText('\n'.join(list(self.dict_curves.keys())))
        self.tabWidget.combo_box.addItems(list(self.dict_curves.keys()))
        self.tabWidget.combo_box.currentIndexChanged.connect(self.change_curve_on_tab)
        self.change_curve_on_tab(0)
        self.statusBar().showMessage("completed", 0)
        self.progressBar.hide()
        
    
    def change_curve_on_tab(self, string):
        """string - index of selected element from signal"""
        name_curve = list(self.dict_curves.keys())[string]
        unit = self.dict_curves[name_curve]
        if name_curve not in self.las.df().columns:
            return
        self.las.df()[name_curve]
        # create the plotly figure
        fig = Figure(Scatter(x=self.las.df()[name_curve], y=self.las.df().index))
        fig.update_layout(title=str(name_curve),
                            xaxis_title=str(name_curve)+', '+str(unit),
                            yaxis_title=f"Depth, {self.depth_unit}",
                            yaxis = dict(autorange="reversed"),
                            margin=dict(l=0, r=0, t=30, b=0),
                            template="plotly_white",
                            paper_bgcolor='white', 
                            plot_bgcolor='white')
        
        # we create html code of the figure
        html = '<html><body>'
        html += plot(fig, output_type='div', include_plotlyjs='cdn')
        html += '</body></html>'
        self.tabWidget.plot_widget.setHtml(html)
        return
    
    def export_to_excellfile(self):
        # TODO: сделать диалоговое окно с выбором места сохранения файла
        
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
    
