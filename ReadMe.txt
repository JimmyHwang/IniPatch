Usage:
  python ini-patch.py -i ini_file -j '{"Default":{"XYZ":0}}'
  python ini-patch.py -i ini_file -j '{"ABC":{"DEF":0}}'
  python ini-patch.py -i ini_file -u "ABC/DEF=1"
  python ini-patch.py -d -i ini_file -u "ABC/DEF=1"
    Auto generate temporary section for update ini when no section
