#!/usr/bin/python
import subprocess
import os
import sys
import hashlib
import subprocess
import re
import json
import getopt
from datetime import datetime
import codecs
import time
from configupdater import ConfigUpdater
import tempfile
import logging

VerboseFlag = False
DefaultSection = "[Default]"
Log = False

def Execute(cmds):
  global VerboseFlag
  stderr_value = ""
  stdout_value = ""
  skip_waiting = False
  p = subprocess.Popen(cmds, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True)
  output, errors = p.communicate()
  errcode = p.returncode
  output = output.decode()
  return (errcode, output)
  
def IsLinux():  
  if os.name == 'nt':
    st = False
  else:
    st = True
  return st
  
def WriteDataToFile(fn, text):
  fp = open(fn, "w")
  fp.write(text)
  fp.close()    

def ReadDataFromFile(fn):
  fp = open(fn, 'r')
  data = fp.read()  
  fp.close()
  return data
  
def DeleteFile(fn):
  if os.path.isfile(fn):
    os.remove(fn)

def MakeFolder(folder):
  if not os.path.exists(folder):
    os.makedirs(folder)

def MoveFile(src, dest):
  dir = os.path.dirname (dest)
  MakeFolder(dir)
  os.rename(src, dest)

def json_encode(data):
  return json.dumps(data, sort_keys=True, indent=4)
  
def json_decode(data):
  return json.loads(data)

def isset(variable):
  st = True
  try:
    variable
  except NameError:
    st = False
  return st
  
def ReadFileToArray(fn):
  with open(fn) as f:
    lines = f.readlines()
    f.close()
  return lines

def WriteArrayToFile(fn, lines):
  fo = open(fn, "w")
  line = fo.writelines(lines)
  fo.close()

def GetFileMTime(fn):
  mtime = os.stat(fn).st_mtime
  return mtime

def SetFileMTime(fn, mtime):
  os.utime(fn, (mtime, mtime))

def GetFileExtension(fn):
  filename, file_extension = os.path.splitext(fn)
  return file_extension

def RemoveComments(lbuf):
  p = lbuf.find("#")
  if p != -1:
    lbuf = lbuf[:p]
  return lbuf

def GetStringBetweenTags(line, tag1, tag2):
  result = False
  p1 = line.find(tag1)
  if p1 != -1:
    p1 = p1 + len(tag1)
    p2 = line.find(tag2, p1)
    if p2 != -1:
      result = line[p1:p2]
  return result

def PrintLineArray(fn, lines):
  logging.info("-------------------------------------------------------------------------------")
  logging.info(" Output file = %s" % (fn))
  logging.info("-------------------------------------------------------------------------------")
  for line in lines:
    logging.info(line)
    
#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
  
#------------------------------------------------------------------------------
# Classes
#------------------------------------------------------------------------------
def GetTempFile():
  temp_folder = tempfile.gettempdir()
  temp_fn = os.path.join(temp_folder, "config.temp")
  return temp_fn
  
class INI_CLASS():
  def __init__(self, fn, default_flag):
    self.File = fn
    self.DefaultFlag = default_flag
    self.TempFile = GetTempFile()
    #
    # Workaround if no section
    #
    if self.DefaultFlag:    
      cfg_fn = self.TempFile
      fp = open(self.TempFile, "w")
      fp.write("%s\n" % DefaultSection)
      lines = ReadFileToArray(fn)
      for line in lines:
        fp.write(line)
      fp.close()
      self.DefaultFlag = True
    else:
      cfg_fn = fn
    #
    # Load Config
    #
    self.Config = ConfigUpdater()
    self.Config.read(cfg_fn)
    
  def __del__(self):
    if self.DefaultFlag:
      cfg_fn = self.TempFile
    else:
      cfg_fn = self.File
    #
    # Export Config to file
    #
    cfg = self.Config
    cfg_fp = open(cfg_fn, "w")
    cfg.write(cfg_fp)
    cfg_fp.close()    
    #
    # Remove [Default] when DefaultFlag == True
    #
    if self.DefaultFlag:
      lines = ReadFileToArray(cfg_fn)
      lines.pop(0)                      # Remove [Default] section
      WriteArrayToFile(self.File, lines)
      
  def Set(self, section, key, value):        
    cfg = self.Config
    if cfg.has_section(section) == False:
      cfg.add_section(section)
    if cfg.has_option(section, key) == False:
      cfg[section][key] = value
    else:
      cfg[section][key].value = value

  def JsonSet(self, jobj):      
    cfg = self.Config
    for section in jobj:    
      if cfg.has_section(section) == False:
        cfg.add_section(section)
      items = jobj[section]
      for key in items:    
        value = items[key]
        self.Set(section, key, value)

#------------------------------------------------------------------------------
# Startup
#------------------------------------------------------------------------------
def Usage():
  print("Usage: python3 ini-patch.py -i xxx.ini -u 'ABC/DEF=1'")
  print("       -v              Enable verbose flag")   # for update with mtime
  print("       -i xxxx         Specific ini file")
  print("       -d              Fix no section issue")
  print("       -j xxxx         Update data by json")
  print("       -u xxxx         Update data")
  
def main():
  global VerboseFlag
  
  VerboseFlag = False  
  IniFile = False
  JsonStr = False
  UpdateStr = False
  DefaultFlag = False
  TestFlag = False
    
  LogFile = sys.argv[0].replace(".py",".log")
  if "/usr" in LogFile:
    log_folder = tempfile.gettempdir()
    LogFile = os.path.join(log_folder, os.path.basename(LogFile))
    if ".log" not in LogFile:
      LogFile = LogFile + ".log"      
  FORMAT = '%(asctime)s %(levelname)s: %(message)s'  
  logging.basicConfig(level=logging.DEBUG, filename=LogFile, filemode='a', format=FORMAT)

  try:
    opts, args = getopt.getopt(sys.argv[1:], "i:j:h:u:dv?t", ["help"])
  except getopt.GetoptError as err:
    print (err)  # will print something like "option -a not recognized"
    usage()
    sys.exit(2)
  output = None
  
  for opt, arg in opts:
    arg = arg.strip()
    if opt in ("-?", "--help"):
      Usage()
      sys.exit()
    elif opt in ("-v"):
      VerboseFlag = True
    elif opt in ("-t"):
      TestFlag = True
    elif opt in ("-d"):
      DefaultFlag = True
    elif opt in ("-i"):
      IniFile = arg
    elif opt in ("-j"):
      JsonStr = arg
    elif opt in ("-u"):
      UpdateStr = arg
    else:
      assert False, "unhandled option"
  
  logging.info("INI File        = %s" % IniFile);
  logging.info("Json String     = %s" % JsonStr);
  logging.info("Update String   = %s" % UpdateStr);
  logging.info("Default Flag    = %d" % DefaultFlag);
  logging.info("Log File        = %s" % LogFile);
 
  if IniFile != False:
    if JsonStr != False:
      iobj = INI_CLASS(IniFile, DefaultFlag)
      iobj.JsonSet(json_decode(JsonStr))
    if UpdateStr != False:
      iobj = INI_CLASS(IniFile, DefaultFlag)
      items = UpdateStr.split("|")
      for item in items:
        temp = item.split("=")
        if len(temp) == 2:
          key = temp[0]
          value = temp[1]
          temp = key.split("/")
          if len(temp) == 2:
            section = temp[0]
            key = temp[1]
            iobj.Set(section, key, value)
          else:
            Log.Error("Invalid data format without section name")
        else:
          Log.Error("Invalid data format without '='")
    
  if TestFlag:
    iobj = INI_CLASS("abc", 1)
    iobj.Set("ABC","DEF", 123)
    # iobj.JsonSet(UpdateJson)

if __name__ == "__main__":
  main()

#  
# Source code in GitHub, https://github.com/JimmyHwang/SetProxy
#
 