import os
import maya.mel as mel
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtCore, QtGui

spath = os.path.dirname(__file__)
spath = spath.replace("\\", "/")

class CreateControllerUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(CreateControllerUI, self).__init__(parent)
        self.setWindowTitle("Create Controller")
        self.setFixedSize(480, 350)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        main_layout = QtWidgets.QVBoxLayout(self)
        self.create_radio = QtWidgets.QRadioButton("Create")
        self.change_shape_radio = QtWidgets.QRadioButton("Change Shape")
        self.create_radio.setChecked(True)
        self.range_combo = QtWidgets.QComboBox()
        self.range_combo.addItems(["Only Ctrl", "Constraint", "Joint Based", "Connection"])
        self.range_combo.setFixedWidth(188)

        radio_combo_layout = QtWidgets.QHBoxLayout()
        radio_combo_layout.addWidget(self.create_radio)
        radio_combo_layout.addWidget(self.range_combo)
        radio_layout = QtWidgets.QVBoxLayout()
        radio_layout.addLayout(radio_combo_layout)
        radio_layout.addWidget(self.change_shape_radio)
        main_layout.addLayout(radio_layout)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        self.scroll_widget = QtWidgets.QWidget()
        scroll_area.setWidget(self.scroll_widget)
        self.grid_layout = QtWidgets.QGridLayout(self.scroll_widget)

        button_size = 70
        self.shape_folder = os.path.join(spath, 'icons')
        self.shape_files = [f for f in os.listdir(self.shape_folder) if f.endswith('.png')]
        self.button_icon_map = {}

        for i, shape_file in enumerate(self.shape_files):
            button = QtWidgets.QPushButton()
            button.setFixedSize(button_size, button_size)
            icon_path = os.path.join(self.shape_folder, shape_file)
            button.setIcon(QtGui.QIcon(icon_path))
            button.setIconSize(QtCore.QSize(button_size, button_size))
            row, col = i // 5, i % 5
            self.grid_layout.addWidget(button, row, col)
            self.button_icon_map[button] = shape_file
            button.clicked.connect(self.button_clicked)

        self.change_shape_radio.toggled.connect(self.toggle_combo_lock)

    def toggle_combo_lock(self, checked):
        """Toggle the combo box based on the radio button state."""
        self.range_combo.setEnabled(not checked)

    def button_clicked(self):
        """Handle button clicks to create or change controllers."""
        cmds.undoInfo(openChunk=True)
        sender = self.sender()
        selected_range = self.range_combo.currentText()

        if self.create_radio.isChecked():
            sel = cmds.ls(sl=True)
            if not sel:
                self.create_curve()
            else:
                if selected_range == 'Only Ctrl':
                    self.create_only_ctrl(sel)
                elif selected_range == 'Constraint':
                    self.create_constraint(sel)
                elif selected_range == 'Joint Based':
                    self.create_joint_based(sel)
                elif selected_range == 'Connection':
                    self.create_connection(sel)

        if self.change_shape_radio.isChecked():
            self.change_curve()

        cmds.undoInfo(closeChunk=True)

    def create_only_ctrl(self, selection):
        """Create controllers and parent them to selected objects."""
        for obj in selection:
            ctrl = self.create_curve()
            cmds.parentConstraint(obj, ctrl, mo=False)
            cmds.delete(ctrl, cn=True)

    def create_constraint(self, selection):
        """Create controllers with constraints to selected objects."""
        for obj in selection:
            trans = cmds.createNode("transform", name=obj + "_ctrl")
            transOff = cmds.createNode("transform", name=trans + "_off")
            cmds.parent(trans, transOff)
            ctrl = self.create_curve()
            ccshape = cmds.listRelatives(ctrl, shapes=True)
            cmds.delete(cmds.parentConstraint(obj, transOff, mo=False))
            cmds.parentConstraint(trans, obj, mo=True)
            cmds.scaleConstraint(trans, obj, mo=True)
            cmds.parent(ccshape, trans, relative=True, shape=True)
            cmds.delete(ctrl)

    def create_joint_based(self, selection):
        """Create joint-based controllers for selected objects."""
        for obj in selection:
            trans = cmds.createNode("transform", name=obj + "_ctrl")
            transOff = cmds.createNode("transform", name=trans + "_off")
            cmds.parent(trans, transOff)
            jnt = cmds.createNode("joint", name=obj + "_jj")
            ctrl = self.create_curve()
            ctrlShape = cmds.listRelatives(ctrl, shapes=True)
            cmds.delete(cmds.parentConstraint(obj, transOff, mo=False))
            cmds.parentConstraint(trans, jnt, mo=False)
            cmds.scaleConstraint(trans, jnt, mo=True)
            cmds.parent(ctrlShape, trans, relative=True, shape=True)
            cmds.delete(ctrl)
            cmds.skinCluster(jnt, obj)

    def create_connection(self, selection):
        """Create controllers with connections to selected objects' attributes."""
        axies = "XYZ"
        attrs = ["translate", "rotate", "scale"]
        for obj in selection:
            selOff = cmds.createNode("transform", name=obj + "_off")
            cmds.delete(cmds.parentConstraint(obj, selOff, mo=False))
            cmds.parent(obj, selOff)
            trans = cmds.createNode("transform", name=obj + "_ctrl")
            transOff = cmds.createNode("transform", name=trans + "_off")
            cmds.parent(trans, transOff)
            cmds.delete(cmds.parentConstraint(obj, transOff, mo=False))
            for attr in attrs:
                for axis in axies:
                    cmds.connectAttr(trans + "." + attr + axis, obj + "." + attr + axis)
            ctrl = self.create_curve()
            ctrlShape = cmds.listRelatives(ctrl, shapes=True)
            cmds.parent(ctrlShape, trans, relative=True, shape=True)
            cmds.delete(ctrl)

    def create_curve(self):
        """Create a curve based on the selected button's icon."""
        sender = self.sender()
        clicked_icon = self.button_icon_map.get(sender)

        if clicked_icon:
            shapeName = clicked_icon.replace('.png', '.mel')
            shapePath = os.path.join(f'{spath}/shapes/', shapeName)
            name = shapeName.split(".")[0]
            if os.path.exists(shapePath):
                trans = cmds.createNode('transform', name=name)
                mel.eval(f'source "{shapePath}";')
                return trans
            else:
                print(f"Shape file not found: {shapePath}")
        return None

    def change_curve(self):
        """Replace selected controllers with new curves."""
        oldCtrls = cmds.ls(sl=True)
        for oldCtrl in oldCtrls:
            newCtrl = self.create_curve()
            if newCtrl:
                cmds.delete(cmds.parentConstraint(oldCtrl, newCtrl))
                cmds.parent(newCtrl, oldCtrl)
                cmds.makeIdentity(newCtrl, apply=True)
                oldShapes = cmds.listRelatives(oldCtrl, type="shape")
                ctrlShapes = cmds.listRelatives(newCtrl, type="shape")

                for oldShape in oldShapes:
                    if cmds.getAttr(oldShape + ".overrideEnabled"):
                        getColor = cmds.getAttr(oldShape + ".overrideColor")
                        for ctrlShape in ctrlShapes:
                            cmds.setAttr(ctrlShape + ".overrideEnabled", 1)
                            cmds.setAttr(ctrlShape + ".overrideColor", getColor)
                for ctrlShape in ctrlShapes:
                    cmds.parent(cmds.rename(ctrlShape, oldCtrl + "Shape#"), oldCtrl, relative=True, shape=True)
                cmds.delete(newCtrl)
                cmds.delete(oldShapes)
        cmds.select(clear=True)

def launchUI():
    """Run the UI."""
    if QtWidgets.QApplication.instance():
        for win in QtWidgets.QApplication.allWindows():
            if "CreateControllerUI" in win.objectName():
                win.destroy()
    mayaMainWindowPtr = omui.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(int(mayaMainWindowPtr), QtWidgets.QWidget)
    CreateControllerUI.window = CreateControllerUI(parent=mayaMainWindow)
    CreateControllerUI.window.setObjectName("CreateControllerUI")  # code above uses this to ID any existing windows
    CreateControllerUI.window.setWindowTitle('Create Controller')
    CreateControllerUI.window.show()
