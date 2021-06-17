#---------------------------------
import codecs
import os
import sys
import datetime
import tkinter as tk
import tkinter.simpledialog as sd
import math
#---------------------------------
#グローバル変数
#
args = sys.argv
fname = args[1] #ソースコードのファイル名
_spt = 0 #ソース読み取りポインタ
fnno = 0
sourceCode  = '' #cr, lfを取り除いてEOLを入れた文字列のリスト
_chkMode = 0 #文法チェック時は1にする
_sline = 0 #読み取り中のsourceCodeの行
_line = 0 #読み取り中のInterCodeの行 
_lpt = 0 #行内のポインタ
InterCode = [] #中間コード
GVARSIZE = 0
MEMSIZE = 2 ** 10
Dmem = [0.0] * MEMSIZE #メインメモリの確保
errmsg0 = '構文エラー　行 = '
_fnno = 0 #実行中の関数の番号
fExit = 0
fBreak = 0
fReturn = 0
fElif = 0
fElse = 0
fEnd = 0
callParaList = [] #関数コール時、ここに戻り先などを保存する
LTable = [] #ローカル変数テーブル
GTable = [] #グローバル変数テーブル
VTable = [] #数値テーブル
STable = [] #文字列テーブル
FTable = [] #関数テーブル
FTable1 = [] #ここに関数名だけを先に取得
DTable = [] #配列テーブル
DArray = [] #配列の実体 #125
baseReg = 0
spReg = 0
funcAddrList = [] #関数の開始、終了行のペアを格納
localVarSize = [] #各関数内のローカル変数のサイズ
fnnoList = [] #各行が何番の関数に属しているか
ifEndList = [] #ifに対応するendの行番号のリスト
breakList = []
#---------------------------------
#トークンのkind、中間コード
#
While   = 0
Func    = 1
If      = 2
Else    = 3
Elif    = 4
End     = 5
Plus    = 6
Minus   = 7
Mult    = 8
Div     = 9
Assign  = 10
Comma   = 11
DblQ    = 12
Dot     = 13
Equal   = 14
NotEq   = 15
Less    = 16
LessEq  = 17
Great   = 18
GreatEq = 19
EOT     = 20
EOL     = 21
EOF     = 22
LParen  = 23
RParen  = 24
LBracket = 25
RBracket = 26
Mod     = 27
Doll    = 28
Under   = 29
SglQ    = 30
Comment = 31
PlusEq  = 32
MinusEq = 33
MultEq  = 34
DivEq   = 35
DblNum  = 36
Str     = 37
Digit   = 38
Letter  = 39
Not     = 40
Ident   = 41
Print   = 42
For     = 43
To      = 44
Break   = 45
Return  = 46
Exit    = 47
And     = 48
Or      = 49
Fcall   = 50
Lvar    = 51
Gvar    = 52
Pow     = 53
Step    = 54
Input   = 55
Rfile   = 56
Wfile   = 57
Toint   = 58
Sin     = 59
Cos     = 60
Tan     = 61
Dim     = 62 #配列の定義
Dvar    = 63 #配列変数の中間コード用
IDiv    = 64 #整数の商
Dsin    = 65
Dcos    = 66
Dtan    = 67
#
cEOL = chr(EOL)
#
#キーワードテーブル
KWTbl =\
    [['while',  While, ''],
     ['func',   Func,   ''],
     ['if',     If,     ''],
     ['else',   Else,   ''],
     ['elif',   Elif,   ''],
     ['end',    End,    ''],
     ['+',      Plus,   ''],#6
     ['-',      Minus,  ''],
     ['*',      Mult,   ''],
     ['/',      Div,    ''],
     ['=',      Assign, ''],#10
     [',',      Comma,  ''],
     ['"',      DblQ,   ''],
     ['.',      Dot,    ''],
     ['==',     Equal,  ''],#14
     ['!=',     NotEq,  ''],
     ['<',      Less,   ''],
     ['<=',     LessEq, ''],
     ['>',      Great,  ''],
     ['>=',     GreatEq,    ''],
     ['EOT',    EOT,    ''],#20
     ['EOL',    EOL,    ''],
     ['EOF',    EOF,    ''],
     ['(',      LParen, ''],
     [')',      RParen, ''],
     ['[',      LBracket,   ''],
     [']',      RBracket,   ''],
     ['//',     IDiv,    ''], #整数の商
     ['$',      Doll,   ''],
     ['_',      Under,  ''],
     ["'",      SglQ,   ''],#30
     ['#',     Comment,    ''],#31
     ['+=',     PlusEq, ''],
     ['-=',     MinusEq,    ''],
     ['*=',     MultEq, ''],
     ['/=',     DivEq,  ''],#35
     ['DblNum', DblNum, ''],
     ['Str',    Str,    ''],
     ['Digit',  Digit,  ''],
     ['Letter', Letter, ''],
     ['!',      Not,    ''],
     ['Ident',  Ident,  ''],#41
     ['print',  Print,  ''],
     ['for',    For,    ''],
     ['to',     To,     ''],
     ['break',  Break,  ''],
     ['return', Return, ''],
     ['exit',   Exit,   ''],
     ['and',    And,    ''],
     ['or',     Or,     ''],
     ['Fcall',  Fcall,  ''],
     ['Lvar',   Lvar,   ''],
     ['Gvar',   Gvar,   ''],#52
     ['**',     Pow,    ''],#53
     ['step',   Step,   ''],#54
     ['input',  Input,   ''],#55
     ['rfile',  Rfile,   ''],#56
     ['wfile',  Wfile,   ''],#57
     ['toint',  Toint,   ''],#58
     ['sin',    Sin,   ''],#59
     ['cos',    Cos,   ''],#60
     ['tan',    Tan,   ''],#61
     ['dim',    Dim,   ''],#62
     ['Dvar',   Dvar,   ''],#63
     ['%',      Mod,   ''],#64 剰余
     ['dsin',   Dsin,   ''],
     ['dcos',   Dcos,   ''],
     ['dtan',   Dtan,   ''],
     ]
#---------------------------------
#関数テーブルFTable[]には、このクラスを格納。
#ソースで定義される関数の名前、
#関数の番号 fnno。
#argListは引数のリスト（LTableのインデックスのリスト）。[5, 7, 8]など。
class FTableData:
    def __init__(self, name, line, endLine = -1, fnno = -1, argList = []):
        self.name = name
        self.line = line
        self.endLine = endLine
        self.fnno = fnno
        self.argList = argList #LTable[]内のインデックスのリスト
#---------------------------------
#push(), pop() を使えるようにしたクラス
#
class Stack:
    def __init__(self):
        self.stack = []
    def push(self, x):
        self.stack.append(x)
    def pop(self):
        return self.stack.pop()
    def size(self):
        return len(self.stack)
#---------------------------------
opstack = Stack() #オペランドスタック。数式の評価用。
#---------------------------------
#
class Token:
    def __init__(self, kind, val, name, idx = 0):
        #インスタンス変数の定義
        self.kind = kind #「DblNum」など
        self.val = val #「45.3」など
        self.name = name #「while」など
        self.idx = idx #文字列の登録インデックスなど
    def print(self):
        print('kind = {}\nval = {}\nname = {}\nidx = {}\n'\
              .format(self.kind, self.val, self.name, self.idx))
#---------------------------------
#変数の登録リストに入れるクラス
#
class Var:
    def __init__(self, name, fnno, len, dmmaddr, val, line, idx):
        self.name = name
        self.fnno = fnno #地のグループなら０
        self.len = len
        self.dmmaddr = dmmaddr
        #Dmem[dmmaddr + GVARSIZE + baseReg]かDmem[dmmaddr]にこの変数の中身が格納される
        self.val = val
        self.line = line
        self.idx = idx
#---------------------------------
#文字列 splt でソース(source)を分割し、行に分割してsourceCode へ入れる。
#osにより、splt は「CR, LF」か「CR」か「LF」と色々。WindowsではCR,LF。
#空行は「#」のみの行として扱う。
#
def getLines(splt):
    global sourceCode
    wk = source.split(splt)
    for i in range(len(wk)):
        wk[i] = wk[i].lstrip() #文字列の左についている空白を削除
        if len(wk[i]) == 0:
            wk[i] = '#' #空行はコメント行として扱う
        wk[i] += cEOL
    sourceCode = wk
#---------------------------------
#ソースを一括リード
#
def readSource(fname):
    f = codecs.open(fname, 'r', 'utf-8')
    s = f.read()
    f.close()
    return s
#---------------------------
#fnnoList[]に、各行の fnno を入れる。
#関数には番号（fnno）をつける。ソースの先頭から、見つかった関数に
#順につける。関数に属していない行はfnno = 0。
#
def getFnnoList():
    global fnnoList, _lpt, funcAddrList, FTable1
    FTable1.clear()
    fnnoList.clear()
    funcAddrList = []
    stk = Stack()
    for line in range(len(sourceCode)):
        _lpt = 0
        tkn = getToken1(line)
        kd = tkn.kind
        if kd == Func or kd == If or kd == For or kd == While:
            stk.push([kd, line]) 
            if kd == Func:
                tkn = getToken1(line) #関数名も取得しておく
                for i in range(len(FTable1)): #同じ関数名があればエラー
                    if FTable1[i][1] == tkn.val:
                        raise Exception(errmsg0 + str(line + 1))
                FTable1.append([line, tkn.val])
        elif kd == End:
            x = stk.pop()
            if x[0] == Func:
                funcAddrList.append([x[1], line]) #定義開始、終了行
    for i in range(len(sourceCode)):
        fnnoList.append(0)
    #ソースの各行がどの関数に属しているか、fnnoを記録
    k = 1
    for i in range(len(funcAddrList)):
        [x, y] = funcAddrList[i]
        for j in range(x, y + 1):
            fnnoList[j] = k
        k = k + 1
    return
#---------------------------
#次のトークンを取得し、sと一致しているか確認
#一致しなければ例外を発生させる
#
def nextTkn(line, s):
    x, y = getToken2(line)
    if x != s:
        raise Exception(errmsg0 + str(line + 1))
#---------------------------------
#_lpt（行内のポインタ位置)から1個、トークンを取得
#
def getToken1(line):
    global _sline
    _sline = line
    skipSpaceLine()
    c = getc()
    s = c
    #DblNum1文字目
    if ('0' <= c and c <= '9') or c == '.': 
        x = numVal(c)
        registVal(Token(DblNum, x, '')) #kind, val, name
        return Token(DblNum, x, '') #読み取ったトークンを返す。数値を表すトークン。
    #ローカル変数、グローバル変数、関数名の1文字目
    if ('A' <= c and c <= 'Z') \
                or ('a' <= c and c <= 'z') or c == '_' or c == '$':
         #'$'はグローバル変数名の先頭
        s = getIdent(c)
        idx = getKwtblIndex(s)
        if idx >= 0:#予約語なら
            return Token(KWTbl[idx][1], KWTbl[idx][0], '')
        elif c != '$':#ローカル変数名か関数名
            return Token(Lvar, s, '') #予約語でないIdent   
        else: #'$'で始まる(グローバル変数名)
            for i in range(len(DTable)):
                if DTable[i].name == s: #配列変数名だった
                    return Token(Dvar, s, '', i) #インデックスiも返す
            registGvar(Token(Gvar, s, ''), line)
            return Token(Gvar, s, '') #予約語でないIdent   
    #+, - や += , == など
    if c == '+' or c == '-' or c == '='\
               or c == '!' or c == '>' or c == '<':
        s = getOp1(c) #cで始まるトークンの文字列を取得
        idx = getKwtblIndex(s) #sからキーワードテーブル(KWTble)のインデックスを得る
        return Token(KWTbl[idx][1], KWTbl[idx][0], '')
    elif c == '*' or c == '/': # **,//
        s = getOp2(c)
        idx = getKwtblIndex(s)
        return Token(KWTbl[idx][1], KWTbl[idx][0], '')
    #1文字でトークン確定
    if c == '"' or c == '(' or c == ')' or c == ','\
                or c == '[' or c == ']'or c == '#' or c == '%':
        s = c
        idx = getKwtblIndex(s)
        if c == '"': #ダブルクォーテーションなら
            idx = registStr() #STableに登録したインデックスが返る
            return Token(Str, '', '', idx)            
        return Token(KWTbl[idx][1], KWTbl[idx][0], '')
    if c == cEOL:
        return None
    raise Exception(errmsg0 + str(line + 1)) #トークンを判断できなかった
#---------------------------------
#dimの処理専用（配列登録用）。
#_lpt（行内のポインタ位置)から1個、トークン（文字か文字列か数値）を取得。
#getToken1()と違えてある。13, DblNum など、ペアを返す。
#
def getToken2(line):
    global _sline
    _sline = line
    skipSpaceLine()
    c = getc()
    s = c
    #DblNum1文字目
    if ('0' <= c and c <= '9') or c == '.': 
        x = numVal(c)
        return x, DblNum
    #Ident1文字目
    elif ('A' <= c and c <= 'Z') \
                or ('a' <= c and c <= 'z') or c == '_' or c == '$':
        #'$'はグローバル変数名の先頭
        s = getIdent(c)
        if c != '$':#Identのうち、ローカル変数名
            raise Exception(errmsg0 + str(line + 1))
        return s, Gvar
    elif c == '[' or c == ']'or c == ',':
        return c, 0
    elif c == cEOL:
        return None, 0
    raise Exception(errmsg0 + str(line + 1)) #トークンを判断できなかった
#---------------------------------
#Tokenのインスタンス変数　 kind, val, name, idx
#KWTbl[idx][1] = 'while', KWTbl[idx][0] = While など
#---------------------------------
#sourceCodeの現在の行内で、_lpt位置からスペースをスキップ
#
def skipSpaceLine():
    global _lpt
    c = getc()
    if c != ' ':
        _lpt -= 1
        return
    while c == ' ':
        c = getc()
    _lpt -= 1
    return
#---------------------------------
#sourceCode[]からポインタ(_sline, _lpt)位置の1文字をリード
#ポインタは行内で動くだけ。_slineは動かさない。
#
def getc():
    global _lpt
    c = sourceCode[_sline][_lpt]
    _lpt += 1
    return c
#---------------------------
#先頭が文字cの数値を1個、sourceCodeから得る。
#_lpt はその数値の末位の次の桁を指した状態で返る。
#
def numVal(c):
    global _lpt
    s = ''
    ct = 0
    while ('0' <= c and c <= '9') or c == '.':
        if c == '.':
            ct += 1
            if ct >= 2: #カンマが2つ以上あればエラー
                raise Exception(errmsg0 + str(_sline + 1))
        s += c
        c = getc()
    #0～9か.以外の文字が出てきたらここへ来る
    _lpt -= 1
    return float(s)
#---------------------------
#先頭がcの関数名、変数名を取得（cは文字）
#
def getIdent(c):
    global _lpt
    s = ''
    if c == '$':
        s = c
        c = getc()
    #'Z'（大文字）から'a'（小文字）まではコード番号(ASCIIコード)は連続していないので
    #こうして分けて書く
    while ('A' <= c and c <= 'Z') or ('a' <= c and c <= 'z')\
            or ('0' <= c and c <= '9') or c == '_':
        s += c
        c = getc()
#Identの構成文字以外のものが出てきたらここへ来る
    _lpt -= 1
    return s
#---------------------------
#現在のポインタ位置から +=, -=, ==, !=, +, -, =, ! を得る
#
def getOp1(c):
    global _lpt
    s = c
    c1 = getc() #次の文字
    if c1 == '=': #+=,-=,==,!=,<=,>=
        s = s + c1
    else: #+,-,=,!,<,>
        _lpt -= 1
    return s
#---------------------------
#現在のポインタ位置から **, //, *, /, *=, */ を得る
#
def getOp2(c):
    global _lpt
    s = c
    c1 = getc() #次の文字
    if c1 == '=':
        s = s + c1
        return s # *=, /=
    if c == c1:
        s = c + c1 # **, //
    else:
        s = c
        _lpt -= 1
    return s
#---------------------------
#文字列 s をキーワードテーブル（KWTbl）から探して、インデックスを返す。
#
def getKwtblIndex(s):
    for i in range(len(KWTbl)):
        if KWTbl[i][0] == s:
            return i
    return -1
#---------------------------
#InterCode[line]に「n」を追加
#
def addCode(line, n):
    InterCode[line].append(float(n))
#---------------------------
#sourceCodeからInterCodeへ変換
#
def toInterCode():
    for i in range(len(sourceCode)):
        toInterCode1(i)
#---------------------------
#sourceCodeからInterCodeへ1行分、変換
#
def toInterCode1(line):
    global _lpt
    InterCode.append([]) #新しい行のためのリスト
    _lpt  = 0
    while True:
        ret, tkn = toInterCode0(line)
        if ret == True:
            break #1行終わった
#---------------------------
#ソースコードを中間コードに変換
#1回のコールでトークン1個分（場合による）を中間コードに変換。
#SourceCode[line]からInterCode[line]へ
#while → While, 終了行 や　関数名 → Func, 変数名　のように。
#InterCodeは、各行とも最後にcEOLは入れない（行末のマークはなし）。
#戻り値が False ならその行にはまだトークンが続く。
#
def toInterCode0(line):
    tkn = getToken1(line)
    if tkn == None: #cEOL(行の最後)だったら
        return True, tkn
    kd = tkn.kind
    addCode(line, kd) #Lvar, DblNumなどをInterCodeへappend
    if kd == While or kd == If or kd == Elif or kd == Else or kd == For:
        #あとでここにendの存在する番地などを入れるため、空けておく
        addCode(line, 123456) #パディング
        if kd == If or kd == Elif or kd == Else: #if, elif, else では2回パディング
            addCode(line, 7890) #パディング
    elif kd == Lvar:
        for i in range(len(FTable1)): #FTable1[]は予め調べておいた関数名のリスト
            if FTable1[i][1] == tkn.val: #関数名だったら
                InterCode[line][-1] = Fcall #関数呼び出しに書き直す
                addCode(line, i) #Fcallのすぐ後には関数のインデックスを格納
                return False, tkn
        #Var  name, fnno, len, dmmaddr, val, line, idx
        v = Var(tkn.val, fnnoList[line], 1, -1, -1, line, -1)
        j = registLvar(v) #関数の引数以外のローカル変数を登録
        addCode(line, j)
    elif kd == Gvar:
        tkn.kind = Gvar
        j = registGvar(tkn, line) #すでに登録済みの変数だが、jを得るためにコール
        addCode(line, j) #GTable[j]の変数であることをInterCodeに記録
    elif kd == Dvar:
        tkn.kind = Dvar
        addCode(line, tkn.idx) #この配列変数はDTable[tkn.idx]に登録してある
    elif kd == DblNum:
        tkn.kind = DblNum
        j = registVal(tkn) #すでに登録済みの変数だが、jを得るため
        addCode(line, j) #VTable[j]の変数であることをInterCodeに記録
    elif kd == Str:
        addCode(line, tkn.idx) #STable内のindexを中間コードとする
    elif kd == Break:
        addCode(line, 2222) #パディング。Breakの次にbreak実行後の飛先を入れるため。
    elif kd == Func:
        registFunc(line)
    elif kd == Comment: #「#」より後ろの部分は中間コードにしない
        return True, tkn
    elif kd == Dim: #dimより後ろの部分は中間コードにしない
        return True, tkn
    return False, tkn #False……続きがある
#---------------------------------
#STableに登録後、保存位置（STableのインデックス）を返す。
#登録済みだったら、インデックスだけ求めてそれを返す。
#
def registStr():
    s = ''
    c = getc()
    while c != '"' and c != cEOL:
        s += c
        c = getc()
    for i in range(len(STable)):
        if STable[i] == s:
            return i
    STable.append(s)
    return len(STable) - 1 #indexを返す
#---------------------------
#数値の登録。トークンを保存する。
#VTableに登録後、保存位置（VTableのインデックス）を返す。
#登録済みだったら、インデックスだけ求めてそれを返す。
#
def registVal(tkn):
    global VTable
    for i in range(len(VTable)):
        if VTable[i].val == tkn.val:
            return i #登録済みだった
    VTable.append(tkn)
    j = len(VTable) - 1 #今、追加したデータのインデックス
    return j #登録した    
#---------------------------
#グローバル変数の登録
#GTableに登録後、変数の保存位置（GTableのインデックス）を返す。
#登録済みの変数だったら、インデックスだけ求めてそれを返す。
#
def registGvar(tkn, line):
    global GTable, GVARSIZE
    for i in range(len(GTable)):
        if GTable[i].name == tkn.val:
            return i #登録済みだった
    v = Var(tkn.val, 0, 1, 0, 0, 0, 0) #name, fnno, len, dmmaddr, val, line, idx
    GTable.append(v)
    j = len(GTable) - 1
    GTable[j].dmmaddr = GVARSIZE #ここまでのGvarの個数の計
    GVARSIZE += v.len #更新
    return j #登録した    
#---------------------------
#ローカル変数の登録
#LTable内の、変数の保存位置を返す
#LTableに登録後、変数の保存位置（LTableのインデックス）を返す。
#登録済みの変数だったら、インデックスを求めてそれを返す。
#
def registLvar(v):
    global LTable
    for i in range(len(LTable)):
        if LTable[i].name == v.name and LTable[i].fnno == v.fnno:
            return i #登録済みだった
    LTable.append(v)
    j = len(LTable)-1 #今、追加した変数のインデックス
    return j #登録した    
#---------------------------
#配列変数の登録
#エラーなら例外発生
#
#dim $a[10], $bbb[30], $cc[15]　のよう1行にまとめて書いてもよい
#kind, val, name, idx
#
def registDvar():
    global DTable, _sline, _lpt
    _sline = 0
    for line in range(len(sourceCode)):
        _lpt = 0
        tkn = getToken1(line)
        if tkn.kind == Dim:
            registDvar1(line)
#---------------------------
#配列変数の登録
#dimを読んでからここへ来る
#エラーなら例外発生
#
#dim $a[10], $bbb[30], $cc[15]
#kind, val, name, idx
#
def registDvar1(line):
    global DTable, _lpt, DArray
    while True:
        varname, kind = getToken2(line) #グローバル変数名
        if kind != Gvar:
            raise Exception(errmsg0 + str(line + 1))
        nextTkn(line, '[') #'['のはず
        varsize, kind = getToken2(line)  #配列のサイズ（数値）
        if kind != DblNum:
            raise Exception(errmsg0 + str(line + 1))
        nextTkn(line, ']') #']'のはず
        for i in range(len(DTable)):
            if DTable[i].name == varname: #既に登録されている変数名ならエラー
                raise Exception(errmsg0 + str(line + 1))
        v = Var(varname, fnnoList[line], varsize, 0, 0, line, len(DTable))
        #name, fnno, len, dmmaddr, val, line, idx
        DTable.append(v)
        #配列の領域確保
        lst = [] #126
        for i in range(int(varsize)):
            lst.append(0)
        DArray.append(lst)
        c, d = getToken2(line)
        if c == None:
            _lpt -= 1
            return #無事、配列の定義が終了
        elif c != ',':
            raise Exception(errmsg0 + str(line + 1))
        #カンマだった
#---------------------------
#Func f1(x, y)の行の処理。関数名、引数などを FTable[] に登録する。
#Func を読み終わった状態でコールする。
#Funcの後に2データ(関数の終了行、FTable[]内のインデックス)、InterCodeに記録済み
#関数の番号 fnno はFTable[]のインデックスとは異なる。
#fnnoは定義された順に1,2,3,……。
#class FTableData:
#    def __init__(self, name, line, endLine = -1, fnno = -1, argList = []):
#
def registFunc(line):
    argList = [] #関数の引数リスト。LTable[]のインデックスを入れる。FTable[]に格納。
    tkn = getToken1(line) #関数名
    fname = tkn.val #'f1'など
    endLine = searchFuncAddr(line)
    if endLine == -1:
        raise Exception(errmsg0 + str(line + 1))
    addCode(line, endLine) #Funcのすぐ後に対応するendのアドレスを入れる
    addCode(line, 4444) #定義された関数のインデックスを後で入れるため。
    fdata = FTableData(fname, line, endLine, fnnoList[line]) #クラスに値をセット
    #name, line, endLine = -1, fnno = -1, argList = []
    if not checkCode(line, LParen): #次のトークンが LParen であることを確認
        raise Exception(errmsg0 + str(line + 1))
    addCode(line, LParen)
    tkn = getToken1(line)
    if tkn.kind == RParen:
        addCode(line, RParen) #変数なし、右括弧で終わり
        #変数なしの関数の登録
        fdata.argList = argList
        FTable.append(fdata) #関数の登録
        return True
    #')'でなかった
    while True:
        if tkn.kind != Lvar: #それはLvarでなければ
            raise Exception(errmsg0 + str(line + 1))
        #tknはローカル変数だった
        addCode(line, Lvar)
        #Var  name, fnno, len, dmmaddr, val, line, idx
        v = Var(tkn.val, fnnoList[line], 1, -1, -1, line, -1)
        j = registLvar(v) #LTable[j]に関数の引数であるローカル変数が格納される
        argList.append(j)
        addCode(line, j) #InterCodeのLvarの次にjを格納
        tkn = getToken1(line)
        if tkn == None:
            raise Exception(errmsg0 + str(line + 1))
        if tkn.kind == RParen: #右括弧なら無事終わり
            addCode(line, RParen)
            fdata.argList = argList
            FTable.append(fdata) #関数の登録
            InterCode[line][2] = len(FTable) - 1 #関数はFTable内のここへ登録された
            return True
        elif tkn.kind != Comma: #それはコンマでなければ終わり
            raise Exception(errmsg0 + str(line + 1))
        addCode(line, Comma)
        tkn = getToken1(line)
#---------------------------
#次のトークンの kind（While, For など） が kd ならTrue
#
def checkCode(line, kd):
    tkn = getToken1(line)
    if tkn.kind == kd:
        return True
    return False
#---------------------------
#line 行目で定義されている関数の引数のリストを得る
#（LTable[]内のインデックスのリスト）
#関数名は最初に中間コード生成時に Lvar, idx とされている。中間コードは
#Func, _, _, Lvar, idx, LParen, Lvar, _, Comma, Lvar, _, Comma, ……という並びになっている。
#Lvar, idx は以降では使わないが、詰めずに放っておく。
#だから、関数の引数は 行の先頭 +6 から。引数がなければ +6 にはRParenがある。
#
def getArgList(line):
    ret = []
    if lookIc(line, 6) == RParen:
        return []
    ret.append(lookIc(line, 7)) #Lvar のLTable[]内でのインデックス
    i = 8
    while lookIc(line, i) != RParen:
        ret.append(lookIc(line, i + 2)) #Lvar のLTable[]内でのインデックス
        i = i + 3
    return ret
#---------------------------
#各関数内のローカル変数（引数を含む）のサイズ計をlocalVarSize[]に求める
#関数番号は関数でない部分が fnno = 0、他は定義されている順に 1,2,3,…… 
#localVarSize[0]にはどの関数にも属していない(fnno = 0)ローカル変数の数、
#localVarSize[1]には fnno = 1 の関数にも属しているローカル変数の数、
#localVarSize[2]には fnno = 2 の関数にも属しているローカル変数の数。
#LTable[i].dmmaddr には LTable[i - 1] までの変数の数が入る。
#LTable[i].len にはその変数の個数が入っている。単純な変数なら1（配列ならその個数）。
#(Dmem[GVARSIZE + dmmaddr + baseReg] に LTable[i] の変数の値が入る)
#配列でないならここに例えば変数ｘの値が入る。
#（配列ならここから順にx[0], x[1], x[2], ……が入る）
#
def getLocalVarSize():
    global localVarSize
    fnnoMax = 0
    localVarSize = []
    for i in range(len(LTable)): #最大のfnnoを求める
        if LTable[i].fnno > fnnoMax:
            fnnoMax = LTable[i].fnno
    for i in range(fnnoMax + 1):
        localVarSize.append(0) #関数の個数分、初期化
    for i in range(len(LTable)):
        ln = LTable[i].len
        fnno = LTable[i].fnno
        LTable[i].dmmaddr = localVarSize[fnno]
        localVarSize[fnno] = localVarSize[fnno] + ln
#---------------------------
#関数の開始行を与えて終了行を求める。
#funcAddrListの[start, ＿]を探す。
#
def searchFuncAddr(start):
    for i in range(len(funcAddrList)):
        x = funcAddrList[i]
        if x[0] == start:
            return x[1]
    return -1
#---------------------------
#InterCodeを走査して、while, for, if, elif, elseの次に
#必要なアドレスを入れる。
#
def setStartEndAddr():
    stk = Stack()
    for i in range(len(InterCode)):
        cm = InterCode[i][0]
        if cm == While or cm == For or cm == If or cm == Func:
            stk.push(i) #行番号をプッシュ
        elif cm == Elif or cm == Else:
            j = stk.pop()
            InterCode[j][1] = i
            stk.push(i)
        elif cm == End:
            j = stk.pop()
            InterCode[j][1] = i
#---------------------------
def setIfAddr1(i):
    ln = i
    while InterCode[ln][0] != End:
        ln = InterCode[ln][1]
    endAddr = ln #ここまで来たらlnはEndのアドレス
    ln = i
    while InterCode[ln][0] != End:
        #if, elif, else の行にendのアドレスを埋め込む
        InterCode[ln][2] = endAddr
        ln = InterCode[ln][1] #次のelif, else, endのアドレス
#---------------------------
#if, elif, else の後にジャンプ先アドレスを埋め込む
#
def setIfAddr():
    for i in range(len(InterCode)):
        cm = InterCode[i][0]
        if cm == If:
            setIfAddr1(i)
#---------------------------
def setBreakAddr():
    global breakList
    breakList = []
    i = 0
    while i < len(InterCode):
        ic = lookIc(i, 0)
        if ic == While or ic == For:
            i = setBreakAddr1(i)
        i += 1
#---------------------------
#Breakの次にそのbreak文が含まれるwhileブロックなどのendの行番号を書き込む
#lineは見つかったwhile, forの行番号
#最初のwhileやforに対応するendの行番号が返る
#
def setBreakAddr1(line):
    global breakList
    stk = Stack()
    i = line + 1
    while True:
        ic = lookIc(i, 0)
        if ic == While or ic == For:
            i = setBreakAddr1(i)
        elif ic == Break:
            stk.push(i) #breakの行番号をプッシュ
            breakList.append(i)
        elif ic == End and not (i in ifEndList):
        #ifに対応するend以外のendなら
            for j in range(stk.size()):
                #endの行番号をbreakの後ろに書き込み
                InterCode[stk.pop()][1] = i
            return i #end文の行番号を返す
        i += 1
#---------------------------
#return, break文の位置が正しいかチェック
# 
def returnBreakChk():
    for i in range(len(InterCode)):
        ic = lookIc(i, 0)
        if ic == Return: #どれかの関数内にあるならok
            if fnnoList[i] == 0:
                raise Exception(errmsg0 + str(i + 1))
        elif ic == Break:
            if i not in breakList:
                raise Exception(errmsg0 + str(i + 1))
#---------------------------
def posChk():
    global _line, ifEndList
    _line = 0
    ifEndList = []
    while _line < len(InterCode):
        ic = InterCode[_line][0]
        if ic == While or ic == For:
            chkBlock()
        elif ic == Func:
            chkFuncBlock()
        elif ic == If:
            chkIfBlock()
        elif ic == Elif or ic == Else or ic == End:
            raise Exception(errmsg0 + str(_line + 1))
        _line += 1
#---------------------------
#ifを読んだらコールする
#
def chkIfBlock():
    global _line, ifEndList
    elseFlag = 0
    ln = _line
    _line += 1
    while _line < len(InterCode):
        ic = InterCode[_line][0]
        if ic == While or ic == For:
            chkBlock()
        elif ic == If:
            chkIfBlock()
        elif ic == Else or ic == Elif:
            if elseFlag == 1:
                raise Exception(errmsg0 + str(_line + 1))
            if ic == Else:
                elseFlag = 1
        elif ic == Func:
            raise Exception(errmsg0 + str(_line + 1))
        elif ic == End: #if文に対応するend文
            ifEndList.append(_line) #end文の行番号を追加
            return
        _line += 1
    #endがないときここへ来る
    raise Exception(errmsg0 + str(ln + 1))
#---------------------------
#while, for, funcを読んだらコールする
#
def chkBlock():
    global _line
    ln = _line
    _line += 1
    while _line < len(InterCode):
        ic = InterCode[_line][0]
        if ic == While or ic == For:
            chkBlock()
        elif ic == If:
            chkIfBlock()
        elif ic == End:
            return
        elif ic == Elif or ic == Else or ic == Func:
            raise Exception(errmsg0 + str(_line + 1))
        _line += 1
    raise Exception(errmsg0 + str(ln + 1))
#---------------------------
#funcを読んだらコールする
#
def chkFuncBlock():
    global _line
    ln = _line
    _line += 1
    while _line < len(InterCode):
        ic = InterCode[_line][0]
        if ic == While or ic == For:
            chkBlock()
        elif ic == If:
            chkIfBlock()
        elif ic == End:
            return
        elif ic == Elif or ic == Else or ic == Func:
            raise Exception(errmsg0 + str(_line + 1))
        _line += 1
    raise Exception(errmsg0 + str(ln + 1))
#---------------------------
#DblNum は読んである状態でコール。
#
def pushVal(): #変数から値を取り出してプッシュ
    no = nextic()
    v = VTable[no].val
    opstack.push(v)
    return
#---------------------------
#行内のポインタを単純に1だけ戻す
#
def backlpt1():
    global _lpt
    _lpt -= 1
    return
#---------------------------
#_lptが中間コードの対象の行の最後に達していなければ1戻す。
#いったん最後に達したらもう戻さない。
#
def backlpt():
    global _lpt
    if _lpt < len(InterCode[_line]):
        _lpt -= 1
    return
#---------------------------
# _line, _lpt をセット
#
def setlpt2(line, lpt):
    global _line, _lpt
    _line = line
    _lpt = lpt
    return
#---------------------------
#_line を1進める
#
def incLine():
    setlpt2(_line + 1, 0)
#---------------------------
#次の中間コードを得る
#行の最後に到達していたら -1 が返る
#
def nextic():
    global _lpt
    if _lpt >= len(InterCode[_line]):
        return -1
    ic = InterCode[_line][_lpt]
    _lpt += 1
    return int(ic)
#---------------------------
#次の中間コードが ic であることを確認。一致すれば True。
#
def checkic(ic):
    if nextic() == ic:
        return True
    return False
#---------------------------
#InterCode[i][j]を得る
#
def lookIc(i, j):
    return InterCode[i][j]
#---------------------------
#!, +, - (ファクターの前につく記号)は最優先
#例えば !8 + 9 = 10
#factorを評価してopstakにプッシュ。
#文法チェック中には1がプッシュされて返る。
#_chkMode = 1 のときは文法チェック中
#_chkMode = 0 のときは通常の実行中
#
def factor():
    if _chkMode == 1:
    #■■■このブロックは文法チェック中に実行される
        ic = nextic()
        if ic == -1: #行末だったらエラー
            raise Exception(errmsg0 + str(_line + 1))
        elif ic == Not or ic == Plus or ic == Minus:
            factor()
            x = opstack.pop()
            opstack.push(1)
            return
        elif ic == LParen:
            expression()
            if checkic(RParen):
                return
            raise Exception(errmsg0 + str(_line + 1))
        elif ic == Lvar:
            x = getLvar()
            opstack.push(1)
            return
        elif ic == Gvar:
            x = getGvar()
            opstack.push(1)
            return
        elif ic == Dvar: #99
            x = getDvar()
            opstack.push(1)
            return
        elif ic == DblNum:
            opstack.push(1)
            ic = nextic()
            return
        elif ic == Fcall: #関数呼び出しはファクター
            synChkFcall()
            #文法チェック中には実際には関数コールはしないので
            #適当な戻り値をプッシュしておく
            opstack.push(1)
        elif ic == Toint or\
                    ic == Sin or ic == Cos or ic == Tan or\
                    ic == Dsin or ic == Dcos or ic == Dtan:
            #(式)を評価。文法チェック中は1をプッシュし、ポインタを進めるだけ。
            parenExp()
            return
        else:
            raise Exception(errmsg0 + str(_line + 1))
    else:
    #■■■このブロックは通常の実行用
        ic = nextic()
        if ic == -1: #行末だったらエラー
            raise Exception(errmsg0 + str(_line + 1))
        elif ic == Not:
            factor()
            x = opstack.pop()
            if x == 0:
                opstack.push(1)
            else:
                opstack.push(0)
        elif ic == Plus or ic == Minus:
            factor()
            x = opstack.pop()
            if ic == Minus:
                opstack.push(-x)
            else:
                opstack.push(x)
        elif ic == LParen:
            expression()
            ic = nextic() #RParenのはず
            return
        elif ic == Lvar:
            x = getLvar()
            opstack.push(x)
            return
        elif ic == Gvar:
            x = getGvar()
            opstack.push(x)
            return
        elif ic == Dvar:
            x = getDvar()
            opstack.push(x)
            return
        elif ic == DblNum:
            pushVal()
            return
        elif ic == Fcall: #関数呼び出しはファクター
            opstack.push(callFunc())
            return
        elif ic == Toint:
            parenExp() #(式)を評価
            opstack.push(int(opstack.pop()))
            return
        elif ic == Sin:
            parenExp()
            opstack.push(math.sin(opstack.pop()))
            return
        elif ic == Cos:
            parenExp()
            opstack.push(math.cos(opstack.pop()))
            return
        elif ic == Tan:
            parenExp()
            opstack.push(math.tan(opstack.pop()))
            return
        elif ic == Dsin:
            parenExp()
            opstack.push(math.sin(opstack.pop() * math.pi / 180))
            return
        elif ic == Dcos:
            parenExp()
            opstack.push(math.cos(opstack.pop() * math.pi / 180))
            return
        elif ic == Dtan:
            parenExp()
            opstack.push(math.tan(opstack.pop() * math.pi / 180))
            return
    return
#---------------------------
#term(項)の評価。結果はopstackにプッシュされる。
def term():
    factor()
    x = opstack.pop()
    opstack.push(x)
    ic = nextic()
    if ic == -1: #続きがなければreturn
        return
    while ic == Mult or ic == Div\
                or ic == IDiv or ic == Mod or ic == Pow:
        factor()
        x = opstack.pop()
        y = opstack.pop()
        if ic == Mult:
            opstack.push(y*x)
        elif ic == Div:
            opstack.push(y/x)
        elif ic == IDiv:
            opstack.push(int(y//x))
        elif ic == Mod:
            opstack.push(int(y%x))
        else: #ic == Pow
            opstack.push(pow(y, x))
        ic = nextic()
        if ic == -1:
            return
    backlpt1()
    return
#---------------------------
#通常の式（4則、変数、関数などが混ざってもよい）の評価。
#結果はopstackにプッシュされる。
#
def expressionB():
    term()
    ic = nextic()
    if ic == -1:
        return
    while ic == Plus or ic == Minus:
        term()
        x = opstack.pop()
        y = opstack.pop()
        if ic == Plus:
            opstack.push(y+x)
        else: #ic == Minus
            opstack.push(y-x)
        ic = nextic()
        if ic == -1:
            return
    backlpt1()
    return
#---------------------------
#<, >, <=, >=, ==, != の混ざった式の評価。式の左から順に評価される。
#例えば 「x <= y > z == w」 だと x <= y の値 s を求め、
#s > z の値 t を求め、t == w の値を求める。
#
def expressionA():
    expressionB() #左のデータをプッシュ
    ic = nextic()
    if ic == -1:
        return
    while ic == Less or ic == LessEq or ic == Great \
                    or ic == GreatEq or ic == Equal or ic == NotEq:
        expressionB() #右のデータをプッシュ
        x = opstack.pop() #右
        y = opstack.pop() #左
        if ic == Less:
            opstack.push(y < x)
        elif ic == LessEq:
            opstack.push(y <= x)
        elif ic == Great:
            opstack.push(y > x)
        elif ic == GreatEq:
            opstack.push(y >= x)
        elif ic == Equal:
            opstack.push(y == x)
        elif ic == NotEq:
            opstack.push(y != x)
        ic = nextic()
        if ic == -1:
            return
    backlpt1()
    return
#---------------------------
# and, or の処理。式の評価はこれのコールで始める。
# expressionA()と同様、先頭から順に値を求めてゆく。
#これから評価しようとしてる式の先頭を _lpt が指した状態でコール。
#結果は opstack にプッシュされて返る。
#_lptが式の最後の次を指した状態で終了。
#
def expression():
    expressionA()
    ic = nextic()
    if ic == -1:
        return
    while ic == And or ic == Or:
        expressionA()
        x = opstack.pop()
        y = opstack.pop()
        if ic == And:
            if y and x: 
                opstack.push(1)
            else:
                opstack.push(0)
        else: #ic == Or
            if y or x: 
                opstack.push(1)
            else:
                opstack.push(0)
        ic = nextic()
        if ic == -1:
            return
    backlpt1()
    return
#---------------------------
def pushCallPara():
    callParaList.append(baseReg)
    callParaList.append(spReg)
    callParaList.append(_line)
    callParaList.append(_lpt)
    callParaList.append(_fnno)
#---------------------------
def popCallPara():
    global baseReg, spReg, _line, _lpt, _fnno
    _fnno = callParaList.pop()
    _lpt = callParaList.pop()
    _line = callParaList.pop()
    spReg = callParaList.pop()
    baseReg = callParaList.pop()
#---------------------------
#関数呼び出しコード（Fcall）を読んでから呼ぶ。
#関数をコールして値を得る。
#
def callFunc():
    global baseReg, spReg, _lpt, _fnno
    global fEnd, fReturn
    argStack = Stack() 
    argStack1 = Stack() 
    j = nextic() #Fcallの次には関数のインデックスが埋め込まれている
    argList = FTable[j].argList
    if not checkic(LParen):
        return False
    if len(argList) == 0:
        if not checkic(RParen):
            return False
    for i in range(len(argList)): #コールされた関数に引数をセット
        expression()
        x = opstack.pop()
        argStack.push(x)
        if i == len(argList) - 1:
            ic = nextic()
            if ic != RParen:
                return False
        else:
            if not checkic(Comma):
                return False
    #ここまでで引数がargStackにセットされている
    _fnno = FTable[j].fnno
    pushCallPara()
    fstart = FTable[j].line
    setlpt2(fstart + 1, 0)
    baseReg = spReg
    spReg = baseReg + localVarSize[FTable[j].fnno]
    for i in range(argStack.size()):
        argStack1.push(argStack.pop()) #引数の順を逆転させる
    #関数に引数を渡す
    for i in range(len(argList)):
        x = argStack1.pop()
        setLvar2(argList[i], x)
    execBlock() #このブロックで読んだreturn, endは以降で処理
    if fReturn == 1: #return はここで処理
        fReturn = 0 #フラグをクリア
        ic = nextic()
        if ic == -1: #戻り値なしのreturnだった
            popCallPara()
            return 1 #戻り値なしでも1を返す。
        _lpt -= 1 #ポインタを戻す
        expression() #戻り値を評価
        ret = opstack.pop()
        popCallPara()
        return ret
    elif fEnd == 1: #関数の定義終了のendを読んだ
        fEnd = 0 #フラグをクリア
        popCallPara()
        return 1 #returnなしの関数は1を返す。
    return 0 #上位の関数には何も伝えない
#---------------------------
#LTable[i]が指定する変数にｘを代入する
#baseReg, GVARSIZEに必要な値を入れておく必要がある
#(Dmemにｘを格納する)
#
def setLvar2(i, x):
    Dmem[LTable[i].dmmaddr + GVARSIZE + baseReg] = x
#---------------------------
#ローカル変数の値を取得
#行先頭の Lvar を読んだ状態でコール
#
def getLvar():
    no = nextic()
    dmmaddr = LTable[no].dmmaddr
    v = Dmem[GVARSIZE + dmmaddr + baseReg]
    return v
#---------------------------
#グローバル変数の値を取得
#行先頭の Gvar を読んだ状態でコール
#
def getGvar():
    no = nextic()
    dmmaddr = GTable[no].dmmaddr
    v = Dmem[dmmaddr]
    return v
#---------------------------
#配列変数（グローバル）の値を（メモリから）取得
#行先頭の Dvar を読んだ状態でコール
#
def getDvar(): #99
    idx = nextic() #DTable内のインデックス取得
    nextic() #'['
    expression() #配列のインデックスを計算
    #2020年12月16日(水) (A)を削除、(B)(C)を挿入
    #x = $d[3 をエラーと認識させるため
    #nextic() #']'  (A)
    if not checkic(RBracket): #(B)
        raise Exception(errmsg0 + str(_line + 1)) #(C)
    x = opstack.pop()
    v = DArray[idx][int(x)]
    return v
#---------------------------
#配列変数（グローバル）への代入文の実行 
#変数（割り当てメモリ）へ右辺の評価結果を格納
#行先頭の Dvar を読んだ状態でコール
#
def setDvar():
    global DArray
    idx = nextic()
    nextic() #'['
    expression()
    x = opstack.pop()
    nextic() #']'
    ic = nextic()
    expression() #右辺の評価
    if ic == Assign: #通常の代入文
        DArray[idx][int(x)] = opstack.pop()
    elif ic == PlusEq: #+=
        DArray[idx][int(x)] = DArray[idx][int(x)] + opstack.pop()
    elif ic == MinusEq: #-=
        DArray[idx][int(x)] = DArray[idx][int(x)] - opstack.pop()
    elif ic == MultEq: #*=
        DArray[idx][int(x)] = DArray[idx][int(x)] * opstack.pop()
    elif ic == DivEq: #/=
        DArray[idx][int(x)] = DArray[idx][int(x)] / opstack.pop()
    return
#---------------------------
#変数（グローバル・ローカル）への代入文の実行 
#変数（割り当てメモリ）へ右辺の評価結果を格納
#行先頭の Lvar か Gvar を読み、それを引数にしてコール
#kdはLvarかGvar
#
def setVar(kd):
    no = nextic()
    if kd == Lvar:
        #Dmem[addr]が問題の変数の本体
        addr = baseReg + LTable[no].dmmaddr + GVARSIZE
    elif kd == Gvar:
        addr = GTable[no].dmmaddr #Dmem[addr]が問題の変数の本体
    ic = nextic()
    expression() #右辺の評価
    if ic == Assign: #通常の代入文
        Dmem[addr] = opstack.pop()
    elif ic == PlusEq:
        Dmem[addr] = Dmem[addr] + opstack.pop()
    elif ic == MinusEq:
        Dmem[addr] = Dmem[addr] - opstack.pop()
    elif ic == MultEq:
        Dmem[addr] = Dmem[addr] * opstack.pop()
    elif ic == DivEq:
        Dmem[addr] = Dmem[addr] / opstack.pop()
    return addr
#---------------------------
#中間コードを実行する
#
def execute():
    global fExit
    setlpt2(0, 0)
    fExit = 0 #終了フラグをクリア
    while fExit == 0 and _line < len(InterCode):
        statement()
#---------------------------
#ブロックを実行する。関数ブロック、if文、while文、for文。
#statement()の実行で各フラグがセットされる。
#if文関係のフラグは、それを見たらこのルーチンからすぐ戻る。
#このルーチンがif文のブロックに使われている場合は、このif文以外の
#elif, else, end は読まない。例えばifブロック内に書かれた
#whileブロックのendはwhileブロック内で読まれるので。
#
#ifブロックでelifなどを読んだらここからはすぐに抜け、
#ひとつ上位のexecIfBlock()（本ルーチン）からはすぐに抜ける。
#さらにひとつ上位のexecIfBlock()内で処理される。
#
#if文関係のフラグも1行目で処理できるが、1行目がand
#ばかりなのでこうした方が簡潔に書ける。
#
def execBlock():
    while fExit == 0 and fReturn == 0 and fBreak == 0:
        statement()
        if fElif == 1 or fElse == 1 or fEnd == 1:
            break
    return
#---------------------------
#1行、中間コードを実行する
#
def statement():
    global fExit, fReturn, fEnd, fBreak, fElif, fElse
    ic = nextic()
    if ic == Elif:
        fElif = 1
    elif ic == Else:
        fElse = 1
    elif ic == Lvar: #代入文
        setVar(Lvar)
        incLine() #次の行へポインタを進める
    elif ic == Gvar:
        setVar(Gvar)
        incLine()
    elif ic == Dvar: #配列変数への代入文
        setDvar()
        incLine()
    elif ic == For:
        ed = nextic()
        b, stp, addr = forLineProc(_line)
        execForBlock(_line, ed, b, stp, addr)
        return
    elif ic == Fcall:
        callFunc()
        incLine()
    elif ic == Print:
        s = getStrNum()
        print(s) 
        incLine()
    elif ic == While:
        ln = nextic() #endのアドレス
        execWhileBlock(_line, ln)
        return
    elif ic == If:
        execIfBlock()
        return
    elif ic == Exit:
        fExit = 1 #終了フラグ立てる
        return
    elif ic == End:
        fEnd = 1
        return
    elif ic == Break:
        fBreak = 1
        return
    elif ic == Return: #statement()
        fReturn = 1
        return
    elif ic == Func:
        ic = nextic() #関数定義の終了行
        setlpt2(ic + 1, 0)
    elif ic == Comment or ic == Dim: #コメント行、配列の定義行は実行しない
        incLine()
    elif ic == Input:
        inputProc(_line)
        incLine()
    return
#---------------------------
#文字列、式のカンマ区切りの任意個の並びから文字列を作る
#式は評価後の値を文字列に。
#_lptが式や文字列の先頭を指した状態でコール。
#"こんにちは", 2*x + f(5), "やっほ" から
#'こんにちは 18 やっほ' という文字列を作る。
#実行時にこれを使ってprintの引数のチェックをする。
#
def getStrNum():
    s = ''
    ic = nextic()
    if ic == Str:
        no = nextic()
        s = STable[no]
        ic = nextic()              
        if ic == -1: #文字列の表示のみ
            return s #文字列を返す
        elif ic != Comma:
            raise Exception(errmsg0 + str(_line + 1))
    else:
        backlpt1()
        ic = Comma
    while ic == Comma:
        expression()
        x = opstack.pop()
        s += '  ' + str(x)
        ic = nextic()
        if ic == -1:
            return s
    raise Exception(errmsg0 + str(_line + 1))
#---------------------------
#input "文字列", x の処理
#input を読んでからコールする。xにインプットされた値を代入する。
#
def inputProc(line):
    global DArray
    s = 'INPUTBOX'
    ic = nextic()
    if ic == Str: #input box のタイトル
        sno = nextic() #文字列の登録インデックス
        s = STable[sno] #表示文字列の取得
        nextic() #カンマ読み捨て
        ic = nextic() #LvarかGvarかDvar
    no = nextic() #変数の登録インデックス
    #数値の入力にはtkinterモジュールのsimpledialogを用いる
    wd = tk.Tk()
    wd.withdraw() #小さなウィンドウを消す
    try:
        x = float(sd.askstring(s, s, initialvalue=''))
    except Exception as e: #数値に変換できなければエラー
        print(e)
        sys.exit()
    if ic == Dvar:
        bracketExp() #[xxx]の並びであることを確認し、xxx(インデックス)をスタックに積む
        DArray[no][int(opstack.pop())] = x
        return
    if ic == Lvar:
        addr = baseReg + LTable[no].dmmaddr + GVARSIZE
    else: #ic == Gvar
        addr = GTable[no].dmmaddr
    Dmem[addr] = x #Dmem[addr]が変数の本体
    return
#---------------------------
# for文から必要な情報を取り出す
#
def forLineProc(line):
    setlpt2(line, 3) #Lvar, Gvarの次を指す
    if lookIc(line, 2) == Lvar:
        addr = setVar(Lvar) #Dmem[addr]が制御変数の本体
    elif lookIc(line, 2) == Gvar:
        addr = setVar(Gvar) #Dmem[addr]が制御変数の本体
    else:
        return False
    if checkic(To) == False:
        return False
    expression() #_lptは式のすぐ次を指した状態で実行を終わる
    b = opstack.pop()
    if checkic(Step) == False: #step がないなら
        stp = 1
    else: #stepあり
        expression()
        stp = opstack.pop()
    return b, stp, addr #Dmem[addr]が制御変数の本体
#---------------------------
#forブロックの実行
#for文の行を読んだ直後に実行される
#st:    条件の書いてある行(while の行)
#ed:    end行
#b:     制御変数がb以下（以上）なら実行
#stp:   for文のstep
#addr:  Dmem[addr]が制御変数の本体
#
#forブロックで直に読まれたreturnは
#for文（ブロックを含めて）を包んでいる関数の定義にあるreturnのはず。
#だからfReturnフラグはいじらず、上位のルーチンであるcallFunc()内で
#fReturn = 0 とする。
#要するに各フラグには担当のルーチンがあり、そこでクリアする。
#
def execForBlock(st, ed, b, stp, addr):
    global fBreak, fEnd
    setlpt2(st + 1, 0)
    while (stp > 0 and Dmem[addr] <= b) or (stp < 0 and Dmem[addr] >= b):
        execBlock()
        if fEnd == 1: #for文のend以外にはあり得ない
            fEnd = 0
            setlpt2(st + 1, 0) #forブロックの最初の行へ戻る
            Dmem[addr] = Dmem[addr] + stp #制御変数にstpを加える 
            continue #ループを続ける
        if fBreak == 1:
            fBreak = 0
            setlpt2(ed + 1, 0) #break文の次のアドレス
            return #for文は抜ける。
        elif fReturn == 1:
            return #フラグはいじらない。for文は抜ける。
    setlpt2(ed + 1, 0) #forブロックを抜けるときのジャンプ先
    return #for文は抜ける
#---------------------------
#whileブロックの実行
#st:条件の書いてある行(while の行)
#ed:end行
#While の行を読んだ直後に実行される
#
def execWhileBlock(st, ed):
    global fBreak, fEnd
    while True:
        setlpt2(st, 2) #条件の書いてあるところにポインタをセット
        expression()
        cond = opstack.pop()
        if cond > 0: #条件成立なら
            setlpt2(st + 1, 0) #while の次の行へセット
            execBlock()
            if fEnd == 1:
                fEnd = 0
                continue
            elif fBreak == 1:
                fBreak = 0
                setlpt2(ed + 1, 0) #whileに対応するendのアドレス
                return #実行中のwhile文は終わり
            elif fReturn == 1:
                return #フラグはそのまま。while文は終わり。
        else: #条件不成立
            setlpt2(ed + 1, 0) #whileループのend行の次へ(ループを抜ける)
            return #実行中のwhile文は終わり。
#---------------------------
#ifブロックの実行
#st:ブロック開始行(if, elif, else)
#ed:ブロック終了行(elif, else, end)
#
#ifブロック内で読んだelif, else, end はここで始末する。
#
def execIfBlock():
    global fEnd, fElif, fElse
    ed = lookIc(_line, 1) #ifの次のelifかelseかend
    ifend = lookIc(_line, 2) #ifに対応するend
    setlpt2(_line, 3) #条件の書いてあるところ
    expression() #条件式の評価
    ret = opstack.pop()
    if ret > 0: #条件成立
        setlpt2(_line + 1, 0)
        execBlock() #ifブロック実行
        if fElif == 1 or fElse == 1 or fEnd == 1:
            fElif = 0
            fElse = 0
            fEnd = 0
            setlpt2(ifend + 1, 0)
            return 0 #if文の実行終了
        elif fReturn == 1 or fBreak == 1:
            return #フラグはいじらない。if文は終わり。
        return
    #ifで条件不成立だった
    cd = lookIc(ed, 0)
    while cd == Elif: #ここはフラグでは判定できない
        ln = ed
        ed = lookIc(ln, 1) #ifの次のelifかelseかend
        ifend = lookIc(ln, 2) #if文の最後のend
        setlpt2(ln, 3) #条件の書いてあるところ
        expression() #条件式の評価
        ret = opstack.pop()
        if ret > 0: #条件成立
            setlpt2(ln + 1, 0)
            execBlock() #ifブロック実行
            if fElif == 1 or fElse == 1 or fEnd == 1:
                fElif = 0
                fElse = 0
                fEnd = 0
                setlpt2(ifend + 1, 0)
                return #if文の実行終了
            elif fReturn == 1 or fBreak == 1:
                return #フラグはいじらない。if文は終わり。
            return
        #条件不成立
        cd = lookIc(ed, 0)
    if cd == Else: #ここはフラグでは判定できない
        ln = ed
        ed = lookIc(ln, 1) #ifの次のelifかelseかend
        ifend = lookIc(ln, 2) #if文の最後のend
        setlpt2(ln + 1, 0)
        execBlock() #ifブロック実行
        if fElif == 1 or fElse == 1 or fEnd == 1:
            fElif = 0
            fElse = 0
            fEnd = 0
            setlpt2(ed + 1, 0)
            return #if文の実行終了
        elif fReturn == 1 or fBreak == 1:
            return #フラグはいじらない。if文は終わり。
        return
    else: #cd = End
        setlpt2(ed + 1, 0)
        return
#---------------------------
# ()に囲まれた式を評価し、opstackに積む。
#左括弧を指した状態でコール。
#
def parenExp():
    if not checkic(LParen):
        raise Exception(errmsg0 + str(_line + 1))
    expression()
    if not checkic(RParen):
        raise Exception(errmsg0 + str(_line + 1))
    return
#---------------------------
#[]に囲まれた式を評価し、opstackに積む。
#左括弧を指した状態でコール。
#
def bracketExp():
    if not checkic(LBracket):
        raise Exception(errmsg0 + str(_line + 1))
    expression()
    if not checkic(RBracket):
        raise Exception(errmsg0 + str(_line + 1))
    return
#---------------------------
#文法チェック
#1カ所でもエラーがあればFalseを返す
#
def synChk():
    global _chkMode
    flag = True
    _chkMode = 1 #構文エラーチェック中フラグ
    for line in range(len(InterCode)):
        try:
            synChk1(line)
        except Exception:
            print((errmsg0 + str(line + 1)))
            flag = False
    _chkMode = 0
    return flag
#---------------------------
#1行分、文法チェック
#
def synChk1(line):
    global _lpt
    setlpt2(line, 0)
    ic = nextic()
    if ic == Comment:
        return
    elif ic == Gvar or ic == Lvar: #代入文
        nextic() #変数のインデックス
        ic = nextic()
        if ic != Assign and ic != PlusEq\
                    and ic != MinusEq and ic != MultEq and ic != DivEq:
            raise Exception(errmsg0 + str(line + 1))
        expression()
        opstack.pop()
        ic = nextic()
        if ic != -1:
            raise Exception(errmsg0 + str(line + 1))
        return
    elif ic == Dvar: #代入文
        nextic() #変数のインデックス
        if not checkic(LBracket):
            raise Exception(errmsg0 + str(line + 1))
        expression() #99
        if not checkic(RBracket):
            raise Exception(errmsg0 + str(line + 1))
        ic = nextic()
        if ic != Assign and ic != PlusEq\
                    and ic != MinusEq and ic != MultEq and ic != DivEq:
            raise Exception(errmsg0 + str(line + 1))
        expression() #ここを実行して、_lptはどこを指すか？
        opstack.pop()
        ic = nextic()
        if ic != -1:
            raise Exception(errmsg0 + str(line + 1))
        return
    elif ic == For:
        nextic()
        cd = nextic()
        if cd != Lvar and cd != Gvar:
            raise Exception(errmsg0 + str(line + 1))
        nextic()
        if not checkic(Assign):
            raise Exception(errmsg0 + str(line + 1))
        expression()
        if not checkic(To):
            raise Exception(errmsg0 + str(line + 1))
        expression()
        cd = nextic()
        if cd == -1:
            return
        if cd != Step:
            raise Exception(errmsg0 + str(line + 1))
        expression()
        if checkic(-1):
            return
        raise Exception(errmsg0 + str(line + 1))
    elif ic == While:
        nextic()
        expression()
        if checkic(-1):
            return
        raise Exception(errmsg0 + str(line + 1))
    elif ic == Return:
        cd = nextic()
        if cd == -1:
            return
        _lpt -= 1
        expression()
        cd = nextic()
        if cd == -1:
            return
        raise Exception(errmsg0 + str(line + 1))
    elif ic == Exit or ic == End:
        if len(InterCode[line]) == 1:
            return
    elif ic == Break:
        if len(InterCode[line]) == 2:
            return
    elif ic == If:
        nextic()
        nextic()
        expression()
        if checkic(-1):
            return
        raise Exception(errmsg0 + str(line + 1))
    elif ic == Else or ic == Elif:
        if len(InterCode[line]) == 3:
            return
    elif ic == Func:
        return synChkFunc()
    elif ic == Print:
        return chkPrintArg()
    elif ic == Fcall: #関数のサブルーチン的用法
        synChkFcall()
        if not checkic(-1):
            raise Exception(errmsg0 + str(line + 1))
    elif ic == Input:
        synChkInput(line)
        return
    elif ic == Dim: #配列の宣言は、中間コードに変換するのはdimのみ
        return
    else:
        raise Exception(errmsg0 + str(line + 1))
#---------------------------
#input文の構文チェック
#書式は
# input "文字列", 変数
# input 変数
#
def synChkInput(line):
    ic = nextic()
    if ic == Str: #input box のタイトル
        nextic() #文字列の登録インデックスを読み捨て
        nextic() #カンマ読み捨て
        ic = nextic() #LvarかGvarのはず
    if ic != Lvar and ic != Gvar and ic != Dvar:
        raise Exception(errmsg0 + str(line + 1))
    no = nextic() #変数の登録インデックス
    if no < 0:
        raise Exception(errmsg0 + str(line + 1))
    if ic == Lvar or ic == Gvar:
        if nextic() != -1: #行末でないなら
            raise Exception(errmsg0 + str(line + 1))
    else: #ic = Dvar
        bracketExp() #[xxx]の並びであることを確認し、xxxを評価してスタックに積む
        opstack.pop()
        if nextic() != -1:
            raise Exception(errmsg0 + str(line + 1))
#---------------------------
def chkPrintArg():
    global _lpt
    cd = nextic()
    if cd == -1:
        raise Exception(errmsg0 + str(_line + 1))
    if cd == Str:
        if checkic(-1): #行末なら誤り
            raise Exception(errmsg0 + str(_line + 1))
        if checkic(-1): #行末なら正しい
            return
        _lpt -= 1
        if not checkic(Comma):
            raise Exception(errmsg0 + str(_line + 1))
        #カンマがあった
        if not chkExpSeq():
            raise Exception(errmsg0 + str(_line + 1))
        return
    else: #引数は式で始まるはず
        _lpt -= 1
        if chkExpSeq():
            return
        raise Exception(errmsg0 + str(_line + 1))
#---------------------------
#a+1, x, 56 などのカンマで区切られた1個以上の式の並びであることをチェック。
#
def chkExpSeq():
    cd = Comma
    while cd == Comma:
        expression()
        opstack.pop()
        cd = nextic()
        if cd == -1: #末尾のチェック
            return True
    return False
#---------------------------
#Fcall を読み終わってからコール。
#関数呼び出しの書式が正しいかチェック。
#
def synChkFcall():
    no = nextic() #関数のインデックス
    if not checkic(LParen):
        raise Exception(errmsg0 + str(_line + 1))
    argNum = len(FTable[no].argList)
    if argNum == 0: #引数なしの関数のとき
        if not checkic(RParen):
            raise Exception(errmsg0 + str(_line + 1))
        return
    #引数は1個以上
    i = 0
    while True:
        expression()
        opstack.pop()
        i += 1
        ic = nextic()
        if ic ==  RParen:
            if i == argNum:
                return
            raise Exception(errmsg0 + str(_line + 1))
        if ic != Comma:
            raise Exception(errmsg0 + str(_line + 1))
#---------------------------
#Func を読み終わってからコール。
#関数定義の書式が正しいかチェック。
#
def synChkFunc():
    global _lpt
    nextic()
    nextic()
    if not checkic(LParen):
        return False
    if checkic(RParen):
        if checkic(-1):
            return True
        return False
    _lpt -= 1
    cd = Comma
    while cd == Comma:
        if not checkic(Lvar):
            return False
        nextic()
        cd = nextic()
        if cd == RParen: #末尾のチェック
            if checkic(-1):
                return True
            return False
    return False
#---------------------------
#InterCodeを走査して、while, for文（ブロックを含む）に
#return, if, elif, else, endが構文上おかしな位置にないか、一気に確認。
#
def checkWhileFor():
    global _line
    _line += 1
    if _line >= len(InterCode):
       raise Exception(errmsg0 + str(_line + 1))
    ic = nextic()
    while _line < range(len(InterCode)):
        ic = InterCode[_line][0]
        if ic == If or ic == While or ic == For:
            checkIfEtc(ic)
        elif ic == End:
            _line += 1
            return
        elif ic == Func:
            raise Exception(errmsg0 + str(_line + 1))
        _line += 1
#---------------------------
#InterCodeを走査して、while, for文（ブロックを含む）に
#return, if, elif, else, endが構文上おかしな位置にないか、一気に確認。
#
def checkFunc():
    global _line
    _line += 1
    if _line >= len(InterCode):
       raise Exception(errmsg0 + str(_line + 1))
    ic = nextic()
    while _line < range(len(InterCode)):
        ic = InterCode[_line][0]
        if ic == Func:
            raise Exception(errmsg0 + str(_line + 1))
        elif ic == If or ic == While or ic == For:
            checkIfEtc(ic)
            continue
        elif ic == End:
            _line += 1
            return
        _line += 1
#---------------------------
#InterCodeを走査して、while, for文（ブロックを含む）に
#return, if, elif, else, endが構文上おかしな位置にないか、一気に確認。
#
def checkIf():
    global _line
    _line += 1
    if _line >= len(InterCode):
       raise Exception(errmsg0 + str(_line + 1))
    ic = nextic()
    while _line < range(len(InterCode)):
        ic = InterCode[_line][0]
        if ic == If or ic == While or ic == For:
            checkIfEtc(ic)
        elif ic == Else:
            _line += 1
            break
        elif ic == End:
            _line += 1
            return
        elif ic == Func:
            raise Exception(errmsg0 + str(_line + 1))
        _line += 1
    while _line < range(len(InterCode)):
        ic = InterCode[_line][0]
        if ic == If or ic == While or ic == For:
            checkIfEtc(ic)
        elif ic == Elif or ic == Else:
            raise Exception(errmsg0 + str(_line + 1))
        elif ic == End:
            _line += 1
            return
        _line += 1    
#---------------------------
def checkIfEtc(ic):
    if ic == If:
        checkIf()
    elif ic == While or ic == For:
        checkWhileFor()
    elif ic == Func:
        checkFunc()
#---------------------------
#if-elif-else-end, while-end, for-end, func-end
#の対応などチェック
#
def checkSource():
    global _line
    if _line >= len(InterCode):
       raise Exception(errmsg0 + str(_line + 1))
    while _line < range(len(InterCode)):
        ic = InterCode[_line][0]
        if ic ==  While or ic == For or ic == If or ic == Func:
            checkIfEtc(ic)
#---------------------------
def printTkn(tkn):
        print('kind = {}\nval = {}\nname = {}\n'.format(tkn.kind, tkn.val, tkn.name))
#---------------------------
def printInterCode():
    for i in range(len(InterCode)):
        for j in range(len(InterCode[i])):
            print(i, InterCode[i][j])
#---------------------------
def printDmmaddr():
    for i in range(len(LTable)):
        print(i, 'name, fnno, dmmaddr = ', LTable[i].name, LTable[i].fnno, LTable[i].dmmaddr)
    for i in range(len(GTable)):
        print(i, 'name, fnno, dmmaddr = ', GTable[i].name, GTable[i].fnno, GTable[i].dmmaddr)
#■■■■■■■■■■■■■■■■■■■■■■■■■■■
#メイン
#■■■■■■■■■■■■■■■■■■■■■■■■■■■
#fname = "======qsort.txt" #99
dt = datetime.datetime.now()
# print('■■■ {}:{}:{}'.format(dt.hour, dt.minute, dt.second))
# print('__file__ = ', __file__)
path, b = os.path.split(__file__)
#os.sepはosによって異なるパスの区切り記号
# print('path + os.sep + fname = ', path + os.sep + fname)
sys.tracebacklimit = 10000
try:
    source = readSource(fname)
except Exception:
    print('ファイルの読み取りエラー')
    sys.exit()
splt = os.linesep #osによって異なる改行コードを得る
getLines(splt)
getFnnoList() #各行のfnnoがfnnoListに入る
registDvar() #配列変数の登録
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
    #print("■■■■■")
    #printInterCode()
    #print("■■■■■")
    #printDmmaddr()
    ret = synChk()
    if not ret:
        sys.exit()
    execute()
except Exception as e:
    print(e)
    sys.exit()
dt = datetime.datetime.now()
# print('■■■ {}:{}:{}'.format(dt.hour, dt.minute, dt.second))
sys.exit()