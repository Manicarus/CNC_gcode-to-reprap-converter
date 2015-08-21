# CNC_gcode-to-reprap-converter
PyCam/HeeksCNC GCode to RepRap converter

Created by River Allen (c) 2012
Modified by me 

What it does?
- convert pycam/heekscnc g-code files into reprap gcode (just tested with marlin-firmware for now).
  (Please let me know if it works with other CAM-Software)

How to use?
1. Start Terminal(or Command Prompt for Windows) go to directory where file name "gcode_converterV03.py" exists
2. Type: python gcode_converterV03.py <feedrate_traveling> <feedrate_cutting> <feedrate_zaxis> <filename1> [filename2 ... n] (Python 2.x should be installed)

Added features:
- Adding Feedrates for Traveling/Cutting/Z-Movements
- Added support for hudbrogs Visualisation in Octoprint / http://gcode.ws (https://github.com/hudbrog/gCodeViewer/)
- Added support for converting HeeksCNC G-Codes (Based on emc2b post processor)
- Added Cutting/Traveling distance information after converting, Arcs (G2/G3) just get calculated by its diagonal distance (easyer for me :)
- Added Commets for better and quicker understanding of the script (By Manicarus)
Hope this is for some use

Fixed:
- Fixed algorithm for constructing GCode that Reprap firmwares (e.g. Marlin, Repetier) can understand (By Manicarus)

~ Hardy
