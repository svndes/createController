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
        self.setFixedSize(356, 250)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        mainLayout = QtWidgets.QVBoxLayout(self)
        self.createRadio = QtWidgets.QRadioButton("Create")
        self.changeShapeRadio = QtWidgets.QRadioButton("Change Shape")
        self.createRadio.setChecked(True)
        self.rangeCombo = QtWidgets.QComboBox()
        self.rangeCombo.addItems(["Only Ctrl", "Constraint", "Joint Based", "Connection"])
        self.rangeCombo.setFixedWidth(188)

        radioComboLayout = QtWidgets.QHBoxLayout()
        radioComboLayout.addWidget(self.createRadio)
        radioComboLayout.addWidget(self.rangeCombo)
        radioLayout = QtWidgets.QVBoxLayout()
        radioLayout.addLayout(radioComboLayout)
        radioLayout.addWidget(self.changeShapeRadio)
        mainLayout.addLayout(radioLayout)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        mainLayout.addWidget(scrollArea)
        self.scrollWidget = QtWidgets.QWidget()
        scrollArea.setWidget(self.scrollWidget)
        self.gridLayout = QtWidgets.QGridLayout(self.scrollWidget)

        buttonSize = 50
        self.shapeFolder = os.path.join(spath, 'icons')
        self.shapeFiles = [f for f in os.listdir(self.shapeFolder) if f.endswith('.png')]
        self.buttonIconMap = {}

        for i, shapeFile in enumerate(self.shapeFiles):
            button = QtWidgets.QPushButton()
            button.setFixedSize(buttonSize, buttonSize)
            iconPath = os.path.join(self.shapeFolder, shapeFile)
            button.setIcon(QtGui.QIcon(iconPath))
            button.setIconSize(QtCore.QSize(buttonSize, buttonSize))
            row, col = i // 5, i % 5
            self.gridLayout.addWidget(button, row, col)
            self.buttonIconMap[button] = shapeFile
            button.clicked.connect(self.buttonClicked)

        self.changeShapeRadio.toggled.connect(self.toggleComboLock)

    def toggleComboLock(self, checked):
        """Toggle the combo box based on the radio button state."""
        self.rangeCombo.setEnabled(not checked)

    def buttonClicked(self):
        """Handle button clicks to create or change controllers."""
        cmds.undoInfo(openChunk=True)
        sender = self.sender()
        selectedRange = self.rangeCombo.currentText()

        if self.createRadio.isChecked():
            sel = cmds.ls(sl=True)
            if not sel:
                self.createCurve()
            else:
                if selectedRange == 'Only Ctrl':
                    self.createOnlyCtrl(sel)
                elif selectedRange == 'Constraint':
                    self.createConstraint(sel)
                elif selectedRange == 'Joint Based':
                    self.createJointBased(sel)
                elif selectedRange == 'Connection':
                    self.createConnection(sel)

        if self.changeShapeRadio.isChecked():
            self.changeCurve()

        cmds.undoInfo(closeChunk=True)

    def createOnlyCtrl(self, selection):
        """Create controllers and parent them to selected objects."""
        for obj in selection:
            ctrl = self.createCurve()
            cmds.parentConstraint(obj, ctrl, mo=False)
            cmds.delete(ctrl, cn=True)

    def createConstraint(self, selection):
        """Create controllers with constraints to selected objects."""
        for obj in selection:
            trans = cmds.createNode("transform", name=obj + "_ctrl")
            transOff = cmds.createNode("transform", name=trans + "_off")
            cmds.parent(trans, transOff)
            ctrl = self.createCurve()
            ccshape = cmds.listRelatives(ctrl, shapes=True)
            cmds.delete(cmds.parentConstraint(obj, transOff, mo=False))
            cmds.parentConstraint(trans, obj, mo=True)
            cmds.scaleConstraint(trans, obj, mo=True)
            cmds.parent(ccshape, trans, relative=True, shape=True)
            cmds.delete(ctrl)

    def createJointBased(self, selection):
        """Create joint-based controllers for selected objects."""
        for obj in selection:
            trans = cmds.createNode("transform", name=obj + "_ctrl")
            transOff = cmds.createNode("transform", name=trans + "_off")
            cmds.parent(trans, transOff)
            jnt = cmds.createNode("joint", name=obj + "_jj")
            ctrl = self.createCurve()
            ctrlShape = cmds.listRelatives(ctrl, shapes=True)
            cmds.delete(cmds.parentConstraint(obj, transOff, mo=False))
            cmds.parentConstraint(trans, jnt, mo=False)
            cmds.scaleConstraint(trans, jnt, mo=True)
            cmds.parent(ctrlShape, trans, relative=True, shape=True)
            cmds.delete(ctrl)
            cmds.skinCluster(jnt, obj)

    def createConnection(self, selection):
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
            ctrl = self.createCurve()
            ctrlShape = cmds.listRelatives(ctrl, shapes=True)
            cmds.parent(ctrlShape, trans, relative=True, shape=True)
            cmds.delete(ctrl)

    def createCurve(self):
        """Create a curve based on the selected button's icon."""
        sender = self.sender()
        clickedIcon = self.buttonIconMap.get(sender)

        if clickedIcon:
            shapeName = clickedIcon.replace('.png', '.mel')
            shapePath = os.path.join(f'{spath}/shapes/', shapeName)
            name = shapeName.split(".")[0]
            if os.path.exists(shapePath):
                trans = cmds.createNode('transform', name=name)
                mel.eval(f'source "{shapePath}";')
                shape = cmds.listRelatives(trans, s=True)[0]
                print(shape)
                cmds.rename(shape, f'{name}Shape')
                return trans
            else:
                print(f"Shape file not found: {shapePath}")
        return None

    def changeCurve(self):
        """Replace selected controllers with new curves."""
        oldCtrls = cmds.ls(sl=True)
        for oldCtrl in oldCtrls:
            newCtrl = self.createCurve()
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
