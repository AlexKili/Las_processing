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


class FileSystemView(QtWidgets.QWidget):
    """A class that creates a QtWidget for displaying the file system
    """
    def __init__(self, dir_Path = None):
        super().__init__()
        # setting the default path to the root of the C:
        # TODO drive: make the path download from the settings or the previous session
        if dir_Path == None:
            dir_Path = 'C:\\'
        
        # setting options for interface
        appWidth = 800
        appHeight = 300
        self.setWindowTitle('File System Viewer')
        self.setGeometry(300, 300, appWidth, appHeight)
        
        # setting model
        self.dirModel = QtWidgets.QFileSystemModel()
        self.dirModel.setRootPath(dir_Path)  
        self.dirModel.setNameFilters(["*.las"])  # installing a file filter by extension
        self.dirModel.setNameFilterDisables(False)  # do not show files that have not passed the filter
        
        # setting model QTree
        self.tree =  QtWidgets.QTreeView()
        self.tree.setModel(self.dirModel)
        self.tree.setColumnWidth(0, 250)
        self.tree.setAlternatingRowColors(True)
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.hideColumn(3)
        
        # set widget to main layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)


class TabWidget(QtWidgets.QWidget):
    """A class that creates a TabWidget with three tabs for displaying the content of file
    """
    def __init__(self):
        super().__init__()
        # List of tab names
        self.tab_name = ['Header', 'Data_curves', 'Viewer']
        
        ### creates an instance of the class that creates tabs (then they will be assigned the names of the tables selected on request)
        self.tab_widget = QtWidgets.QTabWidget() 
        ## self.tab_widget.setTabShape(1)  # makes tabs triangular if necessary
        
        # BLOCK for creating the Header tab
        self.text_header = QtWidgets.QTextEdit()
        self.tab_widget.addTab(self.text_header, 'Header')  # добавить вкладку 'Headers' с виджетом text
        
        # BLOCK for creating the Data_curves tab
        ## creating a tab with data from the las file 
        ## 'Header' field will contain a table
        ## below is the block in which the QTableView is generated
        self.table = QtWidgets.QTableView() # creates an instance of the class to display data as a table
        
        ## Creates a tabular model
        self.tableview_model = QtGui.QStandardItemModel()  
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        ### makes even-odd lines in different colors
        self.table.setAlternatingRowColors(True)  
        ### sets the selection mode of the item in the table
        self.table.setSelectionBehavior(1) 
        ### sets the text cropping mode if it does not fit
        self.table.setTextElideMode(1)  
        ### resizes the rows to fit everything
        self.table.resizeRowToContents(0)  
        ### disables sorting of items in the table
        self.table.setSortingEnabled(False)  
        ### in the left corner, you can select the entire table
        self.table.setCornerButtonEnabled(True)  
        ### creates an event for ctrl+C that allows you to copy the table
        self.table.installEventFilter(self)
        ### adding the 'Data_Curves' tab with the table widget
        self.tab_widget.addTab(self.table, 'Data_curves')
        ### setting the signals
        self.tab_widget.tabBarClicked.connect(self.tab_select)
        
        ## Creates a plotting widget
        self.plotcurvewindow = QtWidgets.QWidget(self, QtCore.Qt.Window)
        ### creating a QWebEngineView view and installing html code into it
        self.plot_widget = QtWebEngineWidgets.QWebEngineView()
        ### creating a list of elements for the drop-down list (combonbox) of curves to display
        self.combo_box = QtWidgets.QComboBox(self) 
        self.combo_box.setGeometry(200, 150, 120, 30)
        ### setting the signals for combo box
        ### self.combo_box.currentIndexChanged.connect(self.change_curve)
        
        ## add widgets to vbox
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.combo_box)
        vbox.addWidget(self.plot_widget)
        
        ## plot curves add to main layout
        self.plotcurvewindow.setLayout(vbox)
        self.tab_widget.addTab(self.plotcurvewindow, 'Viewer')
        ### self.plotcurvewindow.show()
        
    def eventFilter(self, source, event):
        """Event filtering to press ctrl+C pressing processing"""
        if (event.type() == QtCore.QEvent.KeyPress and
            event.matches(QtGui.QKeySequence.Copy)):
            self.copySelection()
            return True
        return super(QtWidgets.QWidget, self).eventFilter(source, event)
    
    def copySelection(self):
        """Processing event is start, 
        this copying selecting data and load it to csv file in IO Stream"""
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
        # print('INDEX:', index)
        # print(self.tab_name[index])
        pass


class PlotCurveWindow(QtWidgets.QWidget):
    """This create a SEPARATE window (not in tabwidget!) for plotting curves is needing.
        In next updates it's need to connecting curves from other files, but for one well.
    """
    def __init__(self, window):
        super().__init__()
        # create plotting widget
        self.plotcurvewindow = QtWidgets.QWidget(window, QtCore.Qt.Window)
        self.plotcurvewindow.setWindowTitle("Отображение кривых ГИС")
        self.plotcurvewindow.resize(800,600)
        self.plotcurvewindow.setWindowModality(QtCore.Qt.WindowModal)
        self.plotcurvewindow.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        # creating a QWebEngineView view and installing html code into it
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
        # creating a list of elements for the drop-down list of curves to display
        # removing the depth curve from the list
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
    """Create thread to load las in parralel time and forming signal with data from las"""
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
        """Filling textual model in tab Header

        Args:
            las_file (LasFile): opened las-file in lasio
        """
        las_header = "~~~~~~WELL SECTION~~~~~~\n" + str(las_file.well) \
                + "\n\n\n~~~~~~CURVES SECTION~~~~~~\n" + str(las_file.curves) \
                    + "\n\n\n~~~~~~PARAMETERS SECTION~~~~~~\n" +str(las_file.params) \
                        + "\n\n\n~~~~~~OTHER SECTION~~~~~~\n" + str(las_file.other)
        
        return las_header
    
    def load_lasdf(self, las_file):
        """Filling in the tabular model of the Data_curves tab

        Args:
            las_file (LasFile): opened las file in lasio
        """
        las_df = las_file.df() 
        las_df[las_df.index.name] = las_df.index
        
        # change the order of the columns and put depth in the first place
        columnname = list( las_df.columns )
        columnname.insert(0, columnname.pop(columnname.index(las_df.index.name)))
        las_df = las_df.loc[:, columnname]  
        
        values = []
        # each value in the list of elements wraps in a QStandartItem
        for count, row in las_df.iterrows():  
            # each element of the string must be wrapped in a QStandardItem and a string of these wrapped elements must be fed into the model
            row = [QtGui.QStandardItem(str(element)) for element in row.values] 
            values.append(row)
            
        return columnname, values


class MainWindow(QtWidgets.QMainWindow):
    """ Creates the main application window for loading and visualizing the las file
    """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        print('MAINWINDOW INIT')
        
        self.las = None
        self.icon_style = 'standard' # TODO: get this parameter from settings.ini
        
        # BLOCK to loading icons
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
        
        # BLOCK to create menu
        self.menu = QtWidgets.QMenuBar() 
        self.menu_instr = self.menu.addMenu('Instruments') 
        self.menu_settings = self.menu.addMenu('Settings')
        
        # create Action to adding in Menu to Open directory
        self.menu_instr_openfile = QtWidgets.QAction(iconOpen, 'Open las-file') 
        self.menu_instr_plotcurve = QtWidgets.QAction(iconPlot, 'Plot curve')
        self.menu_instr_connectcurve = QtWidgets.QAction(iconConnect, 'Connect many las')
        self.menu_instr_exporttoexcell = QtWidgets.QAction(iconExport, 'Export to excell')
        
        ## Subblock to create signals andtriggers
        self.menu_instr_openfile.triggered.connect(self.menu_file_path) 
        self.plotcurve = PlotCurveWindow(self)
        self.menu_instr_plotcurve.triggered.connect(self.plotcurve.plot_curve) 
        self.menu_instr_exporttoexcell.triggered.connect(self.export_to_excellfile)
        
        ## Subblock to adding items in the main menu
        self.menu_instr.addAction(self.menu_instr_openfile) # adding Action in Menu 
        self.menu_instr.addAction(self.menu_instr_plotcurve)
        self.menu_instr.addAction(self.menu_instr_connectcurve)
        self.menu_instr.addAction(self.menu_instr_exporttoexcell)
        
        self.setMenuBar(self.menu)  # Add main menu in main window
        
        # BLOCK creating ToolBar panel
        self.fileToolBar = QtWidgets.QToolBar("File", self)
        self.fileToolBar.addAction(self.menu_instr_openfile)
        self.fileToolBar.addAction(self.menu_instr_plotcurve)
        self.fileToolBar.addAction(self.menu_instr_connectcurve)
        self.fileToolBar.addAction(self.menu_instr_exporttoexcell)
        self.addToolBar(self.fileToolBar)
        
        # BLOCK to create a widget attached on the left, for the file system
        self.dockFilesystem = QtWidgets.QDockWidget("File system", self)
        self.listWidget = FileSystemView() 
        self.dockFilesystem.setWidget(self.listWidget) 
        self.setCentralWidget(QtWidgets.QTextEdit())
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockFilesystem)
        ## self.dockFilesystem.setFloating(False) # this need to floating panel
        ## setting the signals
        self.listWidget.tree.clicked.connect(self.docker_file_path)
        
        # BLOCK to create a widget with a list of curves attached on the left
        self.dockCurveslist = QtWidgets.QDockWidget("Curves in list", self)
        self.listCurveslist = QtWidgets.QTextEdit()  
        self.dockCurveslist.setWidget(self.listCurveslist)  
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockCurveslist)
        
        # BLOCK to create central tables
        self.tabWidget = TabWidget()
        self.setCentralWidget(self.tabWidget.tab_widget) # устанавливает центральный виджет
        
        # BLOCK to create progressBar 
        self.progressBar = QtWidgets.QProgressBar()
        self.statusBar().addPermanentWidget(self.progressBar)
        self.progressBar.hide()
        
        # BLOCK шьзщкештп the necessary functions for curve processing
        # This needeng to next updates
        # TODO: make features available after the beta release with a new interface
        ## self.load_settings()
        ## self.open_temp_file()  # запускает функцию для открытия временного файла и выборки необходимых данных для запроса
        ## self.open_las_file()  # создает соединение с БД
        ## self.table_fill()  # заполнение формы(таблицы) данными
        

        
    def docker_file_path(self, path):
        """Reading the path of selected files in FileSystemView
        
        Args:
            path (PyQt5.QtCore.QModelIndex object): index of object
        
        Returns:
            none: none
        """
        
        # clearing widgets in tabs
        self.tabWidget.text_header.clear()
        self.tabWidget.tableview_model.clear()
        self.tabWidget.combo_box.clear()
        self.tabWidget.table.setModel(self.tabWidget.tableview_model)
        self.tabWidget.plot_widget.setHtml('<html><body>  </body></html>')
        
        # getting the file data from the selected element
        name_file = self.listWidget.dirModel.data(path)  # file name
        file_path = self.listWidget.dirModel.filePath(path)  # the full path to the file
        if str(file_path).lower().endswith('.las'):
            file_path = file_path.replace('/', '\\')
            
            self.open_las_file(path_las_file=file_path)
        
        # Show progress bar
        ## self.progressBar.setFixedSize(self.geometry().width() - 120, 16) ## option if you need a fixed size progress bar
        self.progressBar.show()
        self.statusBar().showMessage(f"loading file {name_file}...", 0)
        self.progressBar.setRange(0, 0)
        
        return
    
    def menu_file_path(self):
        """This function is called after clicking the 'Browse' button and allows you to select the path to the las files"""
        file_path = QtWidgets.QFileDialog.getOpenFileName(parent=self, caption="Выбор las-файла...", directory=os.path.dirname(__file__), filter='Las-file (*.las);;Txt-file (*.txt);;All-files (*)')
        file_path = file_path[0]
        
        if file_path == '':
            self.statusBar().showMessage("Please, set the path of las file")
        else:
            file_path = file_path.replace('/', '\\')
            self.statusBar().showMessage(f"loading las file is {file_path}")
            self.setWindowTitle("Las-file processing" + ' || ' + file_path) 
            self.path_to_save = file_path
            
            # Show progress bar
            #self.progressBar.setFixedSize(self.geometry().width() - 120, 16) # опция если нужен фиксированный размер progress bar
            self.progressBar.show()
            self.statusBar().showMessage(f"loading file ...", 0)
            self.progressBar.setRange(0, 0)
            
        self.open_las_file(path_las_file=file_path)
    
    
    def open_las_file(self, path_las_file):
        """Opens the las file and passes it on to the function to display it
        
        Args:
            path_las_file (str): полный путь к файлу
        
        Returns:
            Boolean: file opening status
        """
        # an attempt to open a las file, if it fails, a message will be displayed in the status bar
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
        
        # installing the header in the header tab
        self.tabWidget.text_header.setText(str(las_header))
        
        # we install the table with the values of the curves in the data tab
        ## each element of the string must be wrapped in a QStandardItem and a string of these wrapped elements must be fed into the model
        [self.tabWidget.tableview_model.appendRow(row) for row in values] 
        self.tabWidget.tableview_model.setHorizontalHeaderLabels(columnname)  # set in model name of columns
        self.tabWidget.table.setModel(self.tabWidget.tableview_model)  # set model in table

        
        # set plotting curves in tab Viewer
        ## befor clearing combo box
        self.tabWidget.combo_box.clear()
        ## creating list of elements for combobox with name of curves to plotting
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
        # TODO: make a dialog box with a choice of where to save the file
        
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
    #app = QtWidgets.QApplication(sys.argv)  # creates an application object as a QApplication object,
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance() 
    app.setStyle("Fusion")
    
    # it is accessed via the qApp attribute from the QtWidgets module
    window = MainWindow()  # creates a window object as an instance of the Qwidget class
    window.setWindowTitle("Las-file processing")  # sets the text that will be displayed in the title of the Object Information window
    
    # Creating a status bar 
    window.statusBar().showMessage("ready to load file") 
    window.resize(1024, 800)  # sets the minimum window size, the first parameter is width, the second is height
    # these sizes are a recommendation, if the objects will not fit in the window, then it will be enlarged
    window.show()  # displays the window and all the components that we previously added to it
    sys.exit(app.exec_())  # starts an endless event loop in the application
    # the code after this expression will be executed only after the application is shut down
    
