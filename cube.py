import random # dumb 3x3 implementation
import sqlite3 # and db stuff here
import time
import json

UP = 0 # directions set to COLS by default
DOWN = 1
FRONT = 2
BACK = 3
RIGHT = 4
LEFT = 5
COLS = 'WYGBRO' # for pretty printing cube
TURNS = 'UDFBRL' # following directions 'enum'
RELFACES = [[BACK,RIGHT,FRONT,LEFT], # face at top, right, bottom, left
            [FRONT,RIGHT,BACK,LEFT],
            [UP,RIGHT,DOWN,LEFT],
            [UP,LEFT,DOWN,RIGHT],
            [UP,BACK,DOWN,FRONT],
            [UP,FRONT,DOWN,BACK]]
RELIDXS = [[(0,0),(0,1),(0,2)], # indxes of face for relfaces
           [(0,2),(1,2),(2,2)],
           [(2,2),(2,1),(2,0)],
           [(2,0),(1,0),(0,0)]]
cube = [[[face for x in range(3)] # the cube itself
                for y in range(3)] # 6 x 3 x 3
                for face in range(6)] # nobody needs numpy

def reset():
    for face in range(6): cube[face][:] = [[face for x in range(3)] for y in range(3)]

def show(cube=cube):
    for y in range(3):
        print(' '*3,''.join([COLS[s] for s in cube[UP][y]]))
    for y in range(3):
        print(' '.join([''.join([COLS[s] for s in cube[f][y]])
                    for f in [LEFT,FRONT,RIGHT,BACK]]))
    for y in range(3):
        print(' '*3,''.join([COLS[s] for s in cube[DOWN][y]]))

def notate(move,cubee=cube):
    face = TURNS.index(move[0])
    turns = 0 if len(move)==1 else 1 if move[-1]=="'" else 2
    oldcubee = [[y[:]for y in f]for f in cubee]
    cubee[face] = [[cubee[face][ [2-x,x,2-y][turns] ][ [y,2-y,2-x][turns] ]
                    for x in range(3)] for y in range(3)] # double turn rfaces has 2 elements per iteration
    rfaces = [RELFACES[face], RELFACES[face][::-1], RELFACES[face][::2]][turns]
    cface2 = rfaces[-1] # get face
    idxs2 = RELIDXS[RELFACES[cface2].index(face)] # indxes of face
    for n,cface in enumerate(rfaces): # face which idx is replaced by
        idxs = RELIDXS[RELFACES[cface].index(face)] # idx2 vals of cface2
        for i,(y,x) in enumerate(idxs):
            cubee[cface][y][x] = oldcubee[cface2][idxs2[i][0]][idxs2[i][1]]
        cface2 = cface # next
        idxs2 = idxs[:]
    if turns==2: # loops dont exist 
        rfaces = RELFACES[face][1::2]
        cface2 = rfaces[-1] # get face
        idxs2 = RELIDXS[RELFACES[cface2].index(face)] # indxes of face
        for n,cface in enumerate(rfaces): # face which idx is replaced by
            idxs = RELIDXS[RELFACES[cface].index(face)] # idx2 vals of cface2
            for i,(y,x) in enumerate(idxs):
                cubee[cface][y][x] = oldcubee[cface2][idxs2[i][0]][idxs2[i][1]]
            cface2 = cface # next
            idxs2 = idxs[:]
    return cubee

def scramble(): # fun fact this takes ~8.5 ms per scramble
    scram = []
    dummycube = [[[face for x in range(3)] # the cube itself
                for y in range(3)] # 6 x 3 x 3
                for face in range(6)] # nobody needs numpy
    visited = []
    axis1, axis2 = -1, -2
    for n in range(30): # random + depth 1 check + axis check
        ok = [t+a for n,t in enumerate(TURNS) for a in ['',"'",'2'] if axis1!=axis2 or n//2!=axis1]
        for m in ok[:]:
            c = notate(m,[[y[:] for y in f] for f in dummycube[:]])
            if c in visited:
                ok.remove(m)
            else:
                visited.append(c)
        if not ok: # can be empty maybe
            return scramble() # lol
        turn = random.choice(ok)
        scram.append(turn)
        dummycube = notate(turn,dummycube)
        axis1, axis2 = TURNS.index(turn[0])//2, axis1
    return scram

OK, PLUS2, DNF = 0,1,2

con = sqlite3.connect("tktimer.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS times(during, time, scramble, judgement)")

def new(score,scram): # same some space in scramble
    scram = ''.join([chr(32 + TURNS.index(i[0])*3 + len(i)-1 + (i[-1]=='2')) for i in scram])
    cur.execute("INSERT INTO times (during,time,scramble,judgement) VALUES(?, ?, ?, ?)",[int(time.time()),int(score*1000),scram,OK])
    con.commit()

def solves():
    fetch= cur.execute('SELECT ROW_NUMBER() OVER(ORDER BY ROWID) as ROWID FROM times ORDER BY ROWID DESC LIMIT 1').fetchone()
    return fetch[0] if fetch else 0

def gettimes():
    return [[t/1000,t/1000+2,'DNF'][j]
        for t,j in cur.execute("SELECT time,judgement FROM times ORDER BY ROWID")]

def edit(idx,judgement): # chatgpt sql is crazy
    cur.execute("UPDATE times SET judgement=? WHERE ROWID in (SELECT ROWID FROM (SELECT ROWID, ROW_NUMBER() OVER (ORDER BY ROWID) AS rn FROM times) AS subquery WHERE rn=?)",[judgement,idx])
    con.commit()

def remove(idx):
    cur.execute("DELETE FROM times WHERE ROWID in (SELECT ROWID FROM (SELECT ROWID, ROW_NUMBER() OVER (ORDER BY ROWID) AS rn FROM times) AS subquery WHERE rn=?)",[idx]) # fix auto increment
    con.commit()

def totaltime():
    t= cur.execute("SELECT SUM(time) AS total FROM times").fetchone()[0]
    return 0 if not t else t/1000

def getone(idx):
    s = list(cur.execute('''SELECT during,time,scramble,judgement FROM 
             (SELECT *, ROW_NUMBER() OVER (ORDER BY ROWID) AS rn FROM times)
            AS subquery WHERE rn = ?''',[idx]).fetchone())
    s[1] /= 1000
    s[2] = ' '.join([TURNS[(i-32)//3] + ['',"'",'2'][(i-32)%3] for i in map(ord,s[2])])
    return s

def getrange(end,solves):
    return [(round(i/1000,3),j) for i,j in cur.execute('''SELECT time,judgement FROM 
             (SELECT *, ROW_NUMBER() OVER (ORDER BY ROWID) AS rn FROM times)
            AS subquery WHERE rn BETWEEN ? and ?''',[end-solves+1,end])]

def loadfile(filename):
    load = json.load(open(filename,'r'))
    sani = []
    for k,v in load.items():
        if k!= 'properties':
            sani += [(i[-1],i[0][1],
                  ''.join([chr(32 + TURNS.index(j[0])*3 + len(j)-1 + (j[-1]=='2')) for j in i[1].split()]),
                 [0,2000,-1].index(i[0][0]) ) for i in v]
    sani.sort(key=lambda i:i[0])
    cur.executemany("INSERT INTO times (during,time,scramble,judgement) VALUES(?, ?, ?, ?)",sani)
    con.commit()

fmtsecs = lambda s:f'{s//86400}d {(s%86400)//3600}h {(s%3600)//60}m {s%60}s'

