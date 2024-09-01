Welcome to the Maya Custom Controller UI script! This tool simplifies your rigging workflow with an intuitive interface for creating and modifying control curves in Autodesk Maya.

✨ Features
Create Controllers:
Only Ctrl: Quickly create and parent controllers to your selected objects.
Constraint: Automatically set up controllers with constraints.
Joint Based: Easily generate joint-based controllers.
Connection: Create controllers that directly connect to object attributes for precise control.
Change Shape: Need a different look? Swap out the shape of existing controllers with just a few clicks.

🚀 Installation
Download the Script: Save the script file to Maya's default "scripts" folder:
Windows: Documents/maya/scripts
macOS: ~/Library/Preferences/Autodesk/maya/scripts
Linux: ~/maya/scripts

Run the Script in Maya:
Open Maya and head over to the Script Editor.
Switch to a Python tab and run the following lines:
from createController import createController
createController.launchUI()

