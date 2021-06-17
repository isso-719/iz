# モジュール読み込み
import codecs
import os
import sys
import datetime
import tkinter as tk
import tkinter.simpledialog as sd
import math

dt = datetime.datetime.now()
path, b = os.path.split(__file__)
sys.tracebacklimit = 10000
try:
    source = readSource(fname)
except Exception:
    print('ファイルの読み取りエラー')
    sys.exit()
splt = os.linesep
getLines(splt)
getFnnoList()
registDvar()
try:
    toInterCode()
    getLocalVarSize()
    baseReg = 0
    spReg = GVARSIZE + localVarSize[0]
    posChk()
    setStartEndAddr()
    setIfAddr()
    setBreakAddr()
    returnBreakChk()
    ret = synChk()
    if not ret:
        sys.exit()
    execute()
except Exception as e:
    print(e)
    sys.exit()
dt = datetime.datetime.now()
sys.exit()