from io import StringIO
import turtle
import sys

def execute(stm):
    tokens = stm.split(" ")
    func = tokens[0]
    arg = int(tokens[1])
    if func == "FD":
        t.forward(arg)
    if func == "RIGHT":
        t.right(arg)
    if func == "LEFT":
        t.left(arg)

t = turtle.Pen()
f = open(sys.argv[1], 'r')
line = f.readline()

while line:
    execute(line)
    line = f.readline()
f.close()

turtle.Screen().mainloop()