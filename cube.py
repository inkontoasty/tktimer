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
    reset()
    visited = []
    axis1, axis2 = -1, -2
    for n in range(30): # random + depth 1 check + axis check
        ok = [t+a for n,t in enumerate(TURNS) for a in ['',"'",'2'] if axis1!=axis2 or n//2!=axis1]
        for m in ok[:]:
            c = notate(m,[[y[:] for y in f] for f in cube[:]])
            if c in visited:
                ok.remove(m)
            else:
                visited.append(c)
        if not ok: # can be empty maybe
            return scramble() # lol
        turn = random.choice(ok)
        scram.append(turn)
        notate(turn)
        axis1, axis2 = TURNS.index(turn[0])//2, axis1
    reset()
    return scram

try: # fix the a
    import kociemba # oh well non built in things
    # you dont want to see the code that generated these
    JPERMS=[{48: 5, 45: 8, 2: 20, 9: 11, 10: 14}, {43: 52, 42: 51, 53: 17, 35: 33, 34: 30}, {30: 21, 27: 18, 24: 6, 38: 44, 41: 43}, {37: 19, 38: 20, 18: 9, 8: 6, 7: 3}, {23: 32, 26: 35, 29: 51, 17: 15, 16: 12}, {50: 30, 53: 27, 33: 24, 44: 42, 43: 39}, {7: 41, 6: 44, 38: 27, 24: 18, 21: 19}, {25: 43, 24: 42, 44: 53, 33: 27, 30: 28}, {19: 10, 20: 11, 9: 45, 2: 8, 5: 7}, {3: 50, 0: 53, 47: 33, 42: 36, 39: 37}, {34: 39, 33: 36, 42: 0, 47: 53, 50: 52}, {16: 25, 15: 24, 26: 44, 27: 29, 28: 32}, {32: 48, 35: 45, 51: 2, 11: 17, 14: 16}, {14: 34, 17: 33, 35: 42, 53: 51, 52: 48}, {39: 1, 36: 2, 0: 11, 45: 47, 46: 50}, {46: 37, 47: 38, 36: 18, 6: 0, 3: 1}, {5: 23, 8: 26, 20: 29, 15: 9, 12: 10}, {1: 14, 2: 17, 11: 35, 51: 45, 48: 46}, {10: 46, 11: 47, 45: 36, 0: 2, 1: 5}, {52: 16, 51: 15, 17: 26, 29: 35, 32: 34}, {28: 12, 29: 9, 15: 8, 20: 26, 23: 25}, {21: 3, 18: 0, 6: 47, 36: 38, 37: 41}, {12: 7, 9: 6, 8: 38, 18: 20, 19: 23}, {41: 28, 44: 29, 27: 15, 26: 24, 25: 21}]
    def scramble(): # no sane me gonna implement 2 phase on my own
        cubestr = [i for i in 'URFDLB' for j in range(9)] #umm its not str
        for n in range(30):
            for k,v in random.choice(JPERMS).items(): # yes random state means spamming Jb perms
                cubestr[k],cubestr[v]=cubestr[v],cubestr[k] # swapping trick is so neat how i realised this only last week
        solve = kociemba.solve(''.join(cubestr)).split(' ')[::-1] # gonna inverse the solve
        scramcube = [[[ cubestr['URFDLB'.index(f)*9+y*3+x] 
            for x in range(3) ] for y in range(3)] for f in TURNS]
        reset()
        for n,i in enumerate(solve):
            notate(i)
            if cube == scramcube: # hmm empty scramble?
                return solve[:n]
            solve[n] = i[0]+("'" if len(i)==1 else '' if i[-1]=="'" else '2')
        reset()
        return solve
except:
    print("To use random state scrambles instead of random move scrambles, "
        "please install the python kociemba package:\n"
        "python3 -m pip install kociemba\n"
        "or visit https://pypi.org/project/kociemba for more information")

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
