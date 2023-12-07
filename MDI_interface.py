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


class ProjectTreeView(QtWidgets.QWidget):
    """Класс создающий QtWidget для отображения файловой системы
    
    Returns:
        _type_: _description_
    """
    def __init__(self):
        super().__init__()
        # устанавливаем путь по умолчанию в корень диска C:
        # TODO: сделать загрузку пути из настроек или предыдущей сессии
        tree = {'Seismic': 
                        {'Attribute': 
                            {'Variance': 
                                {'Cube1': {}}}, 
                            'RMS': 
                                {'Cube1': {}}, 
                            'Chaos': {}}, 
                'Wells': 
                    {'Well_Num1': 
                        {'Curves':{},
                        'Inclination':{},
                        'Core':{},
                        'Testing':{},
                        'Construction':{},
                        'RIGIS':{}}}, 
                'Horizons': {}, 
                'Points': {},
                'Areas':{}}
        
        
        # установка опций для интерфейса 
        appWidth = 500
        appHeight = 300
        self.setWindowTitle('Project Viewer')
        #self.setGeometry(300, 300, appWidth, appHeight)
        self.setMinimumSize(QtCore.QSize(400,300))
        # установка и настройка модели QTree
        self.projectTree =  QtWidgets.QTreeView()
        
        # create of model view directory
        self.dirModel = QtGui.QStandardItemModel()
        self.createTree(tree, self.dirModel.invisibleRootItem())
        self.dirModel.setHorizontalHeaderLabels(['Папка', 'Тип'])
        self.projectTree.setModel(self.dirModel)
        self.projectTree.setColumnWidth(0, 250)
        self.projectTree.setAlternatingRowColors(True)
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.projectTree)
        self.setLayout(layout)
        
        
        self.projectTree.expandAll()
        self.projectTree.selectionModel().selectionChanged.connect(self.onSelectionChanged)

    def createTree(self, children, parent):
        for child in children:
            child_item_dir = QtGui.QStandardItem(child)
            child_item_type = QtGui.QStandardItem('surface')
            parent.appendRow([child_item_dir, child_item_type])
            if isinstance(children, dict):
                self.createTree(children[child], child_item_dir)

    def onSelectionChanged(self, *args):
        for sel in self.projectTree.selectedIndexes():
            val = "/"+sel.data()
            while sel.parent().isValid():
                sel = sel.parent()
                val = "/"+ sel.data()+ val
            print(val)
        
        
        


class MainWindow(QtWidgets.QMainWindow):
    """ Создает основное окно приложения для загрузки и визуализации las-файла
    """
    
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        print('MAINWINDOW INIT')
        
        # БЛОК для создания виджета прикрепляемого слева, для файловой системы
        self.dockFilesystem = QtWidgets.QDockWidget("Project Viewer", self)
        self.listWidget = ProjectTreeView()  # загружаем класс FileSystemView
        self.dockFilesystem.setWidget(self.listWidget)  # устанавливаем его в боковую панель
        self.setCentralWidget(QtWidgets.QTextEdit())
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockFilesystem)
        ## self.dockFilesystem.setFloating(False)
        ## установка сигналов
        #self.listWidget.tree.clicked.connect(self.docker_file_path)
        
        # БЛОК для создания виджета со списком кривых, прикрепляемого слева
        self.dockCurveslist = QtWidgets.QDockWidget("Curves in list", self)
        self.listCurveslist = QtWidgets.QTextEdit()  # загружаем класс FileSystemVi
        self.dockCurveslist.setWidget(self.listCurveslist)  # устанавливаем его в боковую панель
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockCurveslist)
        ## self.dockFilesystem.setFloating(False)
        ## установка сигналов
        #self.listWidget.tree.clicked.connect(self.docker_file_path)
        
        # БЛОК для создания центральной таблицы
        centralWidget = QtWidgets.QMdiArea()
        self.setCentralWidget(centralWidget)
        w = QtWidgets.QTextEdit()
        subWindow = centralWidget.addSubWindow(w)
        subWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        subWindow.show()
        
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
    window.setWindowTitle("Seismic processing")  # задает текст, который будет выводиться в заголовке окна  Информация об объектах
    
    # Создание строки состояния 
    window.statusBar().showMessage("ready to load file") 
    window.resize(1024, 800)  # задает минимальные размеры окна, первый параметр - ширина, второй - высота
    # эти размеры являются рекомендацией, если объекты не будут помещатся в окне, то оно будет увеличено
    window.show()  # выводит на экран окно и все компоненты, которые мы ранее в него добавили
    sys.exit(app.exec_())  # запускает бесконечный цикл обработки событий в приложении
    # код после этого выражения будет выполнен только после завершения работы приложения
    
