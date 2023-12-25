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
import pandas as pd

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


class AddOneLasToWell(QtWidgets.QMainWindow):
    """ Creates the main application window for loading and visualizing the las file
    """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        print('MAINWINDOW INIT')
        
        self.las = None
        self.interactive = False
        
        # BLOCK to create a widget attached on the left, for the file system
        self.dockFilesystem = QtWidgets.QDockWidget("File system", self)
        self.listWidget = FileSystemView() 
        self.dockFilesystem.setWidget(self.listWidget) 
        self.setCentralWidget(QtWidgets.QTextEdit())
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockFilesystem)
        ## self.dockFilesystem.setFloating(False) # this need to floating panel
        ## setting the signals
        self.listWidget.tree.clicked.connect(self.docker_file_path)
        
        
        # BLOCK to create list of loading files
        #self.droppingFileWidget = QtWidgets.QDockWidget("Перетащите файл:", self)
        #self.droppingFileList = QtWidgets.QListWidget()
        #self.droppingFileWidget.setWidget(self.droppingFileList)
        #self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.droppingFileWidget)
        
        # BLOCK to create central tables
        check_hbox = QtWidgets.QHBoxLayout()
        interactive_mode = QtWidgets.QCheckBox('Interactive mode')
        multifile_loading = QtWidgets.QCheckBox('Multifile selecting')
        check_hbox.addWidget(interactive_mode)
        check_hbox.addWidget(multifile_loading)
        ## signals
        interactive_mode.stateChanged.connect(self.interactive_on)
            
        
        # BLOCK to set tab widget
        # List of tab names
        self.tab_name = ['Curves_List', 'Header',  'Viewer']
        
        ### creates an instance of the class that creates tabs (then they will be assigned the names of the tables selected on request)
        self.tab_widget = QtWidgets.QTabWidget() 
        ## self.tab_widget.setTabShape(1)  # makes tabs triangular if necessary
        
        # BLOCK to create a widget with a list of curves attached on the left
        self.listCurveslist = QtWidgets.QTextEdit()  
        self.tab_widget.addTab(self.listCurveslist, 'Curves_List')
        
        
        # BLOCK for creating the Header tab
        self.text_header = QtWidgets.QTextEdit()
        self.tab_widget.addTab(self.text_header, 'Header')  # добавить вкладку 'Headers' с виджетом text
        
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
        
        
        central_widget = QtWidgets.QWidget()
        vbox_central = QtWidgets.QVBoxLayout()
        
        # BLOCK to set push button box
        pushbutton_hbox = QtWidgets.QHBoxLayout()
        apply_adding = QtWidgets.QPushButton('Apply')
        close_dialog = QtWidgets.QPushButton('Close')
        pushbutton_hbox.addWidget(apply_adding)
        pushbutton_hbox.addWidget(close_dialog)
        close_dialog.clicked.connect(self.close)
        apply_adding.clicked.connect(self.add_one_las_to_well)
        
        vbox_central.addLayout(check_hbox)
        vbox_central.addWidget(self.tab_widget)
        vbox_central.addLayout(pushbutton_hbox)
        central_widget.setLayout(vbox_central)
        self.setCentralWidget(central_widget) # устанавливает центральный виджет
        
        
        # BLOCK to create progressBar 
        self.progressBar = QtWidgets.QProgressBar()
        self.statusBar().addPermanentWidget(self.progressBar)
        self.progressBar.hide()
    
    def add_one_las_to_well(self):
        pass
    
    
    
    def interactive_on(self, state):
        if state == 2:
            self.interactive = True
        elif state == 0:
            self.interactive = False
        
    def docker_file_path(self, path):
        """Reading the path of selected files in FileSystemView
        
        Args:
            path (PyQt5.QtCore.QModelIndex object): index of object
        
        Returns:
            none: none
        """
        if self.interactive is False:
            return
        
        # clearing widgets in tabs
        self.text_header.clear()
        self.listCurveslist.clear()
        self.combo_box.clear()
        self.plot_widget.setHtml('<html><body>  </body></html>')
        
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
        self.text_header.setText(str(las_header))
        
        
        # set plotting curves in tab Viewer
        ## befor clearing combo box
        self.combo_box.clear()
        ## creating list of elements for combobox with name of curves to plotting
        self.dict_curves = {element['mnemonic']:element['unit'] for element in self.las.curves} 
        if 'DEPT' in self.dict_curves:
            self.depth_unit = self.dict_curves['DEPT']
            del self.dict_curves['DEPT']
        elif 'DEPTH' in self.dict_curves:
            self.depth_unit = self.dict_curves['DEPTH']
            del self.dict_curves['DEPTH']
        
        self.listCurveslist.setText('\n'.join(list(self.dict_curves.keys())))
        
            
        self.combo_box.addItems(list(self.dict_curves.keys()))
        self.combo_box.currentIndexChanged.connect(self.change_curve_on_tab)
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
        self.plot_widget.setHtml(html)
        return


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
    window = AddOneLasToWell()  # creates a window object as an instance of the Qwidget class
    window.setWindowTitle("Las-file processing")  # sets the text that will be displayed in the title of the Object Information window
    
    # Creating a status bar 
    window.statusBar().showMessage("ready to load file") 
    window.resize(1024, 800)  # sets the minimum window size, the first parameter is width, the second is height
    # these sizes are a recommendation, if the objects will not fit in the window, then it will be enlarged
    window.show()  # displays the window and all the components that we previously added to it
    sys.exit(app.exec_())  # starts an endless event loop in the application
    # the code after this expression will be executed only after the application is shut down
    
