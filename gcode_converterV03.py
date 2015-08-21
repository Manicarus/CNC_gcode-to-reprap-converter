#!/usr/bin/python

# 2015.08.21 Added by Manicarus
#
# I am planning to work on GUI tool based on this script
#
# For reporting bugs and asking questions, contact me on GitHub or by swkang7229@gmail.com 
# -*- coding: utf-8 -*-
# Set encoding UTF-8 for putting comments in Korean
# Required Python Version: 2.7.6 (3.x definitely doesn't work, but I am not sure about other 2.x version)
# Developing Environment: Mac OS X Yosemite(10.10.4) + Eclipse Luna(4.4.1) + PyDev + Python 2.7.6

##Copyright (c) 2012, River Allen
##Modified 2015, Benjamin Hirmer aka Hardy
##
##Modifikation Information:
##Added Visualisation-Support for PyCam-Gcode in GCode Analyzer/Visualizer (c) hudbrog (used in OctoPrint and on his side http://gcode.ws )
##Added Feedrates for traveling/cutting/z-movements
##Added Support for HeeksCNC generated G-Codes with Arc-Commands (G3 / G4) // Visualisation wont work with Arcs
##Added Travel/Cutting-Distance Information, Arcs (G3 / G4) just get calculated by its diagonal distance
##
##All rights reserved.
##
##Redistribution and use in source and binary forms, with or without modification,
##are permitted provided that the following conditions are met:
##* Redistributions of source code must retain the above copyright notice, this list
##  of conditions and the following disclaimer.
##* Redistributions in binary form must reproduce the above copyright notice,
##  this list of conditions and the following disclaimer in the documentation and/or
##  other materials provided with the distribution.
##
##THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
##EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
##OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
##SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
##INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
##TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
##BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
##CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
##ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
##DAMAGE.

from datetime import datetime
import os
import re
import sys
import shutil
import math

class GCodeConverter:
    def __init__(self):
        self.invalid_commands = [
            'M2',
            'M5',
            'M6',
            'M3',
            'T1',
            'T4',
            'S1', # Surface command does not work (this is a hack)
            'G40', # Hardy: Marlin would not understand
            'G49', # Hardy: Marlin would not understand
            'G80', # Hardy: Marlin would not understand
            'G54', # Hardy: Marlin would not understand
            'G61' # Hardy: Marlin would not understand
            ]
        
        # PyCAM uses parentheses as comment 
        # but reprap firmwares (e.g. Repetier, Marlin)  do not understand these 
        self.invalid_comment = '()'
    def convert(self, filename):
        pass


class PyCamGCodeConverter(GCodeConverter):
    def __init__(self):
        GCodeConverter.__init__(self)

    def convert(self, filename, final_pos=None):
        # Add and remove g-code commands to make a pycam g-code
        # file more mendel compatible. Ouput to <filename_converted.ext>.
        # When cutting is complete, move to final pos (x, y, z).
        final_pos = final_pos or (0., 0., 18.)
        write_fname = '%s_converted%s' % os.path.splitext(filename)
        with open(filename, 'rb') as rf:
            with open(write_fname, 'wb') as wf:
                # Add some metadata to the file (not really used at this point)
                wf.write('; CONVERTED FOR MENDEL: %s\n' % str(datetime.now()))
                # Copy the contents of the original gcode file devoid
                # of the pycam gcode commands that do not work on the
                # mendel gcode firmware.
                for l in rf.readlines():
                    l = self.check_valid_comment(l) # by Manicarus
                    if self.check_valid_commands(l):
                        wf.write(l)
                # Some finish up commands to make it easier to remove the
                # completed part.
                wf.write("; FINISH THE CUT BY MOVING BIT TO SAFER POSITION\n")
                wf.write("G1 Z%f ; MOVE BIT ABOVE PIECE\n" % final_pos[2])
                wf.write("G1 X%f Y%f ; HOME X AND Y\n" % final_pos[:2])

        return write_fname

    def check_valid_commands(self, line):
        for cmd in self.invalid_commands:
            if cmd in line:
                return False
        return True

    def check_valid_comment(self, line):
        '''
        By Manicarus
        PyCAM makes comments parentheses but Reprap firmwares do not understand these
        Put them in valid comment form
        (This work is not complete yet)
        
        :param line: (string) a GCode line to check
        '''
        validLine = line
        
        if (self.invalid_comment[0] in line) and (self.invalid_comment[1] in line):
            leftRoundBracket = line.find(self.invalid_comment[0])
            rightRoundBracket = line.find(self.invalid_comment[1])
            
            if ';' in line:
                comment = line.find(';')
                if comment > rightRoundBracket:
                    validLine = line[:leftRoundBracket] + '; ' + line[leftRoundBracket + 1:rightRoundBracket] + line[rightRoundBracket + 1:comment] + line[comment + 1:]
                else:
                    pass
            else:
                validLine = line[:leftRoundBracket] + '; ' + line[leftRoundBracket + 1:rightRoundBracket] + line[rightRoundBracket + 1:]
                
                
        elif (self.invalid_comment[0] in line):
            if (';' in line) and line.find(';') < line.find(self.invalid_comment[1]):
                pass
            else:
                # remove the left rounded bracket
                # unfinished
                pass
        elif (self.invalid_comment[1] in line):
            if (';' in line) and line.find(';') < line.find(self.invalid_comment[1]):
                pass
            else:
                # remove the right rounded bracket
                # unfinished
                pass
        else:
            pass

        return validLine
    
class MarlinGCodeConverter(PyCamGCodeConverter):
    def __init__(self):
        PyCamGCodeConverter.__init__(self)

    def getAxis(self, line, axis, GCodeComponent):
        '''
        By Manicarus
        
        @param line: (string) original GCode line
        @param axis: (string) either 'X', 'Y' or 'Z'
        @param GCodeComponent: (dictionary) a place to save information
        '''
        if ';' in line:
            self.getAxis(line[:line.find(';')], axis, GCodeComponent)
        else:
            if (axis in line):
                begin = line.find(axis)
                temp_end1 = line[begin:].find(' ') + begin
                temp_end2 = line[begin:].find('\r') + begin
                
                if line[begin:].find(' ') == -1:
                    end = temp_end2
                elif line[begin:].find('\r') == -1:
                    end = temp_end1
                elif temp_end1 < temp_end2:
                    end = temp_end1
                else:
                    end = temp_end2
                GCodeComponent[axis] = line[begin:end]
            else:
                GCodeComponent[axis] = ''
        
    def getComment(self, line, GCodeComponent):
        '''
        By Manicarus
        Sort out comment parts from line
        and put it in dictionary with key 'Comment' 
        
        :param line: (string) a GCode line
        :param GCodeComponent: (dictionary) a place to save information
        '''
        if ';' in line:
            begin = line.find(';')
            end = line[begin:].find('\r') + begin
            
            GCodeComponent['Comment'] = line[begin:end]
        else:
            GCodeComponent['Comment'] = ''
            begin = len(line);
        return begin
    
    def getMoveType(self, line, GCodeComponent, prevMoveType):
        '''
        By Manicarus
        Cannot guarantee that there're only four kinds of move types
        G03 G02 G01, G00, G04, G21, ... etc 
        For move types other than G3, G2, G1, G0,
        update GCodeComponent with their move types
        but return the value of prevMoveType without change
        
        @param line: (string) a GCode line
        @param GCodeComponent: (dictionary) a place to save information
        @param prevMoveType: (string) a move type that current command may dependent on
        '''
        if 'G' in line:
            begin = line.upper().find('G')
            end = line[begin:].find(' ') + begin
            
            moveType = line[begin:end]
            
            # Handling invalid syntax
            if (moveType == 'G03') or (moveType == 'G3'):
                moveType = 'G3'
            elif (moveType == 'G02') or (moveType == 'G2'):
                moveType = 'G2'
            elif (moveType == 'G01') or (moveType == 'G1'):
                moveType = 'G1'
            elif (moveType == 'G00') or (moveType == 'G0'):
                moveType = 'G0'
            else:
                # For other move types (e.g. G04, G21), update GCodeComponent with their own values.
                # However, return the value of given prevMoveType without change
                GCodeComponent['MoveType'] = moveType
                
                # Assigning the value of prevMoveType to moveType.
                # 
                moveType = prevMoveType
            
        else:
            # if no move type is specified, update GCodeComponent with the value of preMoveType
            moveType = prevMoveType
            GCodeComponent['MoveType'] = moveType
            
        return moveType

    def constructGCode(self, GCodeComponent):
        '''
        Construct GCode from given GCodeComponent
        
        @param GCodeComponent: a dictionary that contains information about a GCode line
        '''
        l = ''
        if not GCodeComponent['MoveType'] == '':
            l += GCodeComponent['MoveType'] + ' ' 
        if not GCodeComponent['X'] == '':
            l += GCodeComponent['X'] + ' ' 
        if not GCodeComponent['Y'] == '':
            l += GCodeComponent['Y'] + ' ' 
        if not GCodeComponent['Z'] == '':
            l += GCodeComponent['Z'] + ' ' 
        if not GCodeComponent['Feedrate'] == '':
            l += GCodeComponent['Feedrate'] + ' ' 
        if not GCodeComponent['Comment'] == '':
            l += GCodeComponent['Comment']
        l += '\r\n'    
        return l

    def getGCodeComponent(self, line, GCodeComponent, prevMoveType):
        comment = self.getComment(line, GCodeComponent)
        
        self.getAxis(line[:comment], 'X', GCodeComponent)
        self.getAxis(line[:comment], 'Y', GCodeComponent)
        self.getAxis(line[:comment], 'Z', GCodeComponent)
        
        return self.getMoveType(line[:comment], GCodeComponent, prevMoveType)
        

    def convert(self, filename, feedrate, final_pos=None):
        # All of this code is written to compensate for the fact Marlin is
        # less robust with the format of g-code. Specifically, on the old mendel
        # the following commands:
        # ~ G1 X30
        # ~  Y30
        # ~  X50
        # would work. These commands do not work on Marlin. Hence, this code
        # converts the above commands to:
        # ~ G1 X30
        # ~ G1 Y30
        # ~ G1 X50

        # Convert pycam gcode for mendel
        convert_fname = PyCamGCodeConverter.convert(self, filename, final_pos)
        # Store this new conversion in a temp file
        temp_fname = '.temp_convert'
        temp_calc = '.temp_calc'
        temp_sum = '.temp_sum'
        pattern = re.compile('([gG01]{1,2})+\s([xX0-9.]{1,15})+\s([yY0-9.]{1,15})+\s([zZ0-9.]{1,15})+\s([fF0-9.]+[0-9.]{1,15})+\s') #Hardy: RegEx for Detect and Slice G-Code which mess with Visualisation
        distances = re.compile('([gG0-3]{1,3})+\s{1,2}[xX]([0-9.]{1,15})|\s[yY]-?([0-9.]{1,15})|\s[zZ]-?([0-9.]{1,15})') #Hardy: RegEx for Calculating Distances
        with open(convert_fname, 'rb') as f_pycc:
            with open(temp_fname, 'wb') as f_temp:
                with open(temp_calc, 'wb') as f_calc:
                    move_type = None
                    AF = 0 #Declare False at first
                    BZ = 'M103 ; Support for Visualisation\n'
                    AZ = 'M101 ; Support for Visualisation\n'
                    
                    GCodeComponent = {}
                    prevMoveType = ''

                    for l in f_pycc.readlines():
                        prevMoveType = self.getGCodeComponent(l, GCodeComponent, prevMoveType)
                        '''
                        By Manicarus
                        
                        The main reason for all these work is because the original code had following problems:
                            1. Indentations were not consistent (mixed usage of 4 spaces and tab).
                                - I recommend using eclipse + PyDev for other developers
                                - Solved by using built-in module named 'reindent.py'
                                    - You can find it in "C:\Python2X\Scripts" 
                            2. Generated file(yourfilename_converted.yourfiletype) from original code had invalid new line characters 
                                that makes GCode incomprehensible for Reprap.
                                I redesigned algorithm which works in this way:
                                    1. For each line, crop informations about MoveType, Comment, Axis and Feedrate. 
                                        When cropping is done, save them in dictionary
                                    2. Construct a new GCode line using dictionary
                        '''
                        
                        # Encountering Z movement that is not dependent on previous move type.
                        # The RepRap firmware spec treats G0 and G1 as the same command, since it's just as efficient as not doing so.
                        # Source: http://reprap.org/wiki/G-code#G0_.26_G1:_Move
                        # Currently, I don't know the logic behind explicitly assinging G1 as move type for Z movement and configuring AF and ZAV.
                        # I am commenting out original author's code for comparison
                        if (GCodeComponent['X'] == '') and (GCodeComponent['Y'] == '') and (GCodeComponent['Z'] != ''):
                            GCodeComponent['MoveType'] = 'G1'
                            GCodeComponent['Feedrate'] = 'F' + str(feedrate[2]).strip()
                            l = self.constructGCode(GCodeComponent)
                            AF = AF + 1
                            ZAV = True
                            
                        elif GCodeComponent['MoveType'] == 'G3':
                            GCodeComponent['Feedrate'] = 'F' + str(feedrate[1])
                            l = self.constructGCode(GCodeComponent)
                            ZAV = False
                            
                        elif GCodeComponent['MoveType'] == 'G2':
                            GCodeComponent['Feedrate'] = 'F' + str(feedrate[1])
                            l = self.constructGCode(GCodeComponent)
                            ZAV = False
                            
                        elif GCodeComponent['MoveType'] == 'G1':
                            GCodeComponent['Feedrate'] = 'F' + str(feedrate[1])
                            l = self.constructGCode(GCodeComponent)
                            ZAV = False
                            
                        elif GCodeComponent['MoveType'] == 'G0':
                            GCodeComponent['Feedrate'] = 'F' + str(feedrate[0])
                            l = self.constructGCode(GCodeComponent)
                            ZAV = False
                           
                        # Original author's code 
                        '''
                        first_3_chars = l[:3].upper()
                        first_2_chars = l[:2].upper()
                        first_char = l[:1].upper()
                        # determine move type
                        if first_3_chars == 'G1 ' or first_3_chars == 'G01':
                            move_type = 'G1'
                        elif first_3_chars == 'G0 ' or first_3_chars == 'G00':
                            move_type = 'G0'
                        elif first_3_chars == 'G02':
                            move_type = 'G2'
                        elif first_3_chars == 'G03':
                            move_type = 'G3'
                        # if there's no move type specified
                        elif first_2_chars == ' X' or first_char == 'X' or first_2_chars == ' Y' or first_char == 'Y' or first_2_chars == ' Z' or first_char == 'Z':
                            #Hardy: Check if HeeksCNC is on HightSave at Surface
                            # encountered Z movement that is not dependent on previous move type
                            if first_char == 'Z': 
                                l = "%s%s" % ("G1 ",l)
                            else:
                                # Change ' X100' to 'G0 X100'
                                l = "%s%s" % (move_type + " ", l)
                        # Hardy: Check if G0/G1 given and change its Feedrate at the end of the G-Code-Line
                        # Also adds space between if not already placed
                        second_chars = l[2:4].upper()
                        last_chars = len(str(l))
                        if second_chars == ' Z' or second_chars == 'Z ':
                            l1 = l[:last_chars-1]
                            l2 = l[last_chars-1:]
                            lf = " F" + str(feedrate[2])
                            l = l1 + lf + l2
                            AF = AF + 1
                            ZAV = True
                        elif move_type == 'G3':
                            l1 = l[:last_chars-1]
                            l2 = l[last_chars-1:]
                            l3 = l[last_chars-2:last_chars-1]
                            if ' ' in l3:
                                lf = "F" + str(feedrate[1])
                            else:
                                lf = " F" + str(feedrate[1])
                            l = l1 + lf + l2
                            ZAV = False
                        elif move_type == 'G2':
                            l1 = l[:last_chars-1]
                            l2 = l[last_chars-1:]
                            l3 = l[last_chars-2:last_chars-1]
                            if ' ' in l3:
                                lf = "F" + str(feedrate[1])
                            else:
                                lf = " F" + str(feedrate[1])
                            l = l1 + lf + l2
                            ZAV = False
                        elif move_type == 'G1':
                            l1 = l[:last_chars-1]
                            l2 = l[last_chars-1:]
                            l3 = l[last_chars-2:last_chars-1]
                            if ' ' in l3:
                                lf = "F" + str(feedrate[1])
                            else:
                                lf = " F" + str(feedrate[1])
                            l = l1 + lf + l2
                            ZAV = False
                        elif move_type == 'G0':
                            l1 = l[:last_chars-1]
                            l2 = l[last_chars-1:]
                            l3 = l[last_chars-2:last_chars-1]
                            if ' ' in l3:
                                lf = "F" + str(feedrate[0])
                            else:
                                lf = " F" + str(feedrate[0])
                            l = l1 + lf + l2
                            ZAV = False
                            
                        '''
                        # Hardy: Crop out necesary Values for calculating Travel and Cutting-Distances and Write it in a Temp-File
                        if distances.findall(str(l)):
                            regline = distances.findall(str(l))

                            for i in regline:
                                if i[1]:
                                    f_calc.write("X" + i[1] + "\n")
                                elif i[2]:
                                    f_calc.write("Y" + i[2] + "\n")
                                elif i[3]:
                                    if i[3][:1] == "0":
                                        f_calc.write("C" + i[3] + "\n")
                                    else:
                                        f_calc.write("T" + i[3] + "\n")

                        # Hardy: Look for something like that (pycam make this sometimes) "G1 X122.12 Y152.123 Z1204 F1500" and change it to "G1 X122.12 Y152.123 F150 \n G0 Z1204 F800 because this will mess with the Visualisation
                        if pattern.match(str(l)):
                            regline = pattern.match(str(l))
                            gvalue = regline.group(1)
                            xvalue = regline.group(2)
                            yvalue = regline.group(3)
                            zvalue = regline.group(4)
                            fvalue = regline.group(5)
                            f_temp.write("G1" + " " + xvalue + " " + yvalue + " F" + str(feedrate[1]) + "\n")
                            f_temp.write(BZ)
                            AF = AF + 1
                            f_temp.write("G0 " + zvalue + " F" + str(feedrate[2]) + "\n")
                        else:
                            if AF == 1 and ZAV:
                                f_temp.write(BZ)

                            f_temp.write(l)

                            if AF == 2 and ZAV:
                                f_temp.write(AZ)
                                AF = 0

        # Hardy: Calculate Distances with Triangles
        with open(temp_calc, 'rb') as f_calc:
            with open(temp_sum, 'wb') as f_sum:

                value = ""
                cache = []
                summaster1 = [] #Collecting SUM of Cutting-Distances
                summaster2 = [] #Collecting SUM of Travel-Distances
                calc = False #Turn of Summing of Cutting-Distances first

                for c in f_calc.readlines():
                    command = c[:2]
                    axis = c[:1]
                    stringcount = len(str(c))

                    f_sum.write(c)
                    value = float(c[1:stringcount-1])

                    cache.append((value, axis))
                    counts = len(cache)

                    if counts >= 4:
                        f_sum.write(str(cache) + str(counts) + "\n\n")
                        if cache[0][1] == "X":
                            if cache[1][1] == "Y":
                                if cache[2][1] == "C":
                                    del cache[2]
                                    f_sum.write("Cutting active\n")
                                    calc = True
                                elif cache[2][1] == "T":
                                    del cache[2]
                                    f_sum.write("Travel active\n")
                                    calc = False
                                elif cache[2][1] == "X":
                                    if cache[3][1] == "Y":
                                        f_sum.write("Calculate?\n")
                                        if calc:
                                            summaster1.append(math.sqrt(((cache[0][0]-cache[2][0])**2)+((cache[1][0]-cache[3][0])**2)))
                                        else:
                                            summaster2.append(math.sqrt(((cache[0][0]-cache[2][0])**2)+((cache[1][0]-cache[3][0])**2)))
                                            f_sum.write("Sum Traveling\n")
                                        del cache[0:2]
                                    elif cache[3][1] == "X":
                                        f_sum.write("Linear 1 Calculate?\n")
                                        if calc:
                                            summaster1.append(abs(cache[2][0]-cache[3][0]))
                                            f_sum.write(" Calculate: " + str(cache[2][0]) + " " + str(cache[3][0]) + "\n")
                                        else:
                                            summaster2.append(abs(cache[2][0]-cache[3][0]))
                                            f_sum.write("Sum Traveling\n")
                                        del cache[2]
                                    elif cache[3][1] == "T":
                                        f_sum.write("Linear 2 Calculate? Then Travel active\n")
                                        if calc:
                                            summaster1.append(abs(cache[0][0]-cache[2][0]))
                                            f_sum.write(" Calculate: " + str(cache[0][0]) + " " + str(cache[2][0]) + "\n")
                                        else:
                                            summaster2.append(abs(cache[0][0]-cache[2][0]))
                                            f_sum.write("Sum Traveling\n")
                                        del cache[0]
                                        del cache[2]
                                        cache[0], cache[1] = cache[1], cache[0]
                                    elif cache[3][1] == "C":
                                        f_sum.write("Linear 3 Calculate? Then Cutting active\n")
                                        summaster2.append(abs(cache[0][0]-cache[2][0]))
                                        f_sum.write("Sum Traveling\n")
                                        del cache[0]
                                        del cache[2]
                                        cache[0], cache[1] = cache[1], cache[0]
                                        calc = True
                                elif cache[2][1] == "Y":
                                    f_sum.write("Linear 4 Calculate?\n")
                                    if calc:
                                        summaster1.append(abs(cache[1][0]-cache[2][0]))
                                        f_sum.write(" Calculate: " + str(cache[1][0]) + " " + str(cache[2][0]) + "\n")
                                    else:
                                        summaster2.append(abs(cache[1][0]-cache[2][0]))
                                        f_sum.write("Sum Traveling\n")
                                    del cache[1]
                        elif cache[0][1] == "T":
                            f_sum.write("Traveling active\n")
                            del cache[0]
                            calc = False
                        elif cache[0][1] == "C":
                            f_sum.write("Cutting active\n")
                            del cache[0]
                            calc = True
                        else:
                            del cache[0]


                # Sum all Distances
                cuttingdistance = sum(summaster1)
                travelingdistance = sum(summaster2)

                if cuttingdistance != 0:
                    print "Total Cutting Distance: " + str(cuttingdistance) + " mm"
                    print "Total Travel Distance: " + str(travelingdistance) + " mm"
                    print "Total Distance: " + str(cuttingdistance+travelingdistance) + " mm"
                else:
                    print "Could not determine Cutting-Distance: Z-Cutting-Level is not at 0"
                    print "Total Distance: " + str(cuttingdistance+travelingdistance) + " mm"

        # Copy the temp file conversion over to the pycam conversion
        # for cleanliness
        shutil.copy(temp_fname, convert_fname)
        # Get rid of temp files
        os.remove(temp_fname)
        os.remove(temp_calc)
        os.remove(temp_sum)
        return convert_fname


if __name__ == '__main__':
    # Simple command line script. Can be used, but mostly added for testing.
    # Hardy: Added Feedrate Support and some Error-Check/Feedback for Command-Line
    error = 0
    if len(sys.argv) < 2:
        print 'CNC_to_RepRap <feedrate_traveling> <feedrate_cutting> <feedrate_zaxis> <filename1> [filename2 ... n]'
    elif len(sys.argv) >= 5:
        if sys.argv[1].isdigit():
            print "Feedrate Traveling: " + sys.argv[1]
        else:
            print 'Feedrate Traveling is not a Number!'
            error = 1
        if sys.argv[2].isdigit():
            print "Feedrate Cutting: " + sys.argv[2]
        else:
            print 'Feedrate Cutting is not a Number!'
            error = 1
        if sys.argv[3].isdigit():
            print "Feedrate X-Axis Traveling: " + sys.argv[3]
        else:
            print 'Feedrate X-Axis is not a Number!'
            error = 1
        if len(sys.argv[4]) > 0 and error == 0:
            endfile = len(sys.argv[0:])
            for args in range(4, endfile):
                print "File: " + sys.argv[args]
        elif error == 1:
            print 'Dont accept File(s)'
        else:
            print 'No File selected!'
            error = 1
    else:
        print 'Arguments are Missing'

    #Hardy: check for errors
    if error == 0:
        ffrates = sys.argv[1:4]
        fnames = sys.argv[4:]
        fr = []
        for frate in ffrates:
            fr.append(frate)
        gc_converter = MarlinGCodeConverter()
        for fname in fnames:
            gc_converter.convert(fname, fr)
