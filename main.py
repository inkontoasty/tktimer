import cube
import tkinter as tk # oh no bloat imports
import tkinter.font as font # at least its built in right..
import time
from tkinter.filedialog import askopenfilename
from datetime import datetime

root = tk.Tk(className='cube') # hardcode the colorscheme to simple black
root.tk_setPalette(background='black', foreground='white',
               activeBackground='#444444', activeForeground='white',
                highlightBackground='black',highlightColor='black',
                disabledForeground='lightgray',insertBackground='purple',
                selectColor='black',selectBackground='purple',troughColor='black')
root.defaultFont = font.nametofont("TkDefaultFont") # larger font
root.defaultFont.configure(size=18)
root.option_add("*Font", root.defaultFont) # have to code neat for tkinter mess

AVGS = ["time","mo3","ao5","ao12","ao25","ao50","ao100"] # consts and strings and stuff
COLS = ["white","yellow","lime","blue","red","orange","pink"]
AVGSTUFF = [(1,0),(3,0),(5,1),(12,1),(25,2),(50,3),(100,5)]
summary = {i:[tk.StringVar(root,"100.001"),tk.StringVar(root,"100.001")] for i in AVGS} # avg:(now,best)
scramble = cube.scramble()
last_scramble = cube.scramble()
selected_scramble = None
is_last_scramble = True
selsolvestats = None
timelist_selected = tk.StringVar(root,AVGS[0])
statstr = tk.StringVar(root,"no solves yet")
timerstr = tk.StringVar(root, "0.0")
lastpress,timeready,timerelease,timing = float('inf'),False,0,False # debouncing timer keyrepeat
cubed = cube.totaltime()
sesscubed = 0
solves = cube.solves() # counter
sessolves = 0
grind_timevar = tk.StringVar(root, f"cubed {cube.fmtsecs(int(cubed))} ({cube.fmtsecs(int(sesscubed))})")
grind_solvevar = tk.StringVar(root, f"solve {solves} ({sessolves} sess)")
start = time.time()
drawcubemove = -1

fscram,ftimelist,fgrindstats,fleft = [tk.Frame(root)for i in range(4)] # frames
fscram.pack(side=tk.TOP,fill=tk.X) # nice spiralish pattern for pack
ftimelist.pack(side=tk.RIGHT,fill=tk.Y,expand=False) # but why should i use grid instead?
fgrindstats.pack(side=tk.BOTTOM,fill=tk.X,expand=False) # i only get a couple million layout problems
fsummary, fcube, fconftime = [tk.Frame(fleft)for n in range(3)] # could just leave them under root but looks ugly
fconftime.pack(side=tk.BOTTOM,expand=True,anchor='s')
fsummary.pack(side=tk.TOP,expand=True,anchor='n')
fcube.pack(side=tk.BOTTOM,anchor='s',fill=tk.BOTH)
fleft.pack(side=tk.LEFT,fill=tk.Y)

hide = tk.Label(root,bg='black') # hiding all elements on timer
hide.place(relx=0,rely=0,relwidth=0,relheight=0)

def copycurrentscram(): # functions for stuff
    root.clipboard_clear()
    root.clipboard_append(' '.join(last_scramble if is_last_scramble else scramble))
    copyscrambtn.config(activebackground='green')
    root.after(500,copyscrambtn.config,{'activebackground':'black'})

def cubegotomove(moveidx):
    global drawcubemove
    s = last_scramble if is_last_scramble else scramble
    if 0 <= drawcubemove < 30:
        scrambuttons[drawcubemove].config(font=('TkDefaultFont',18))
    cube.reset() # you have to choose, between what is right, and what is easy
    for n in range(moveidx): # i choose easy
        cube.notate(s[n])
    drawcubemove = moveidx
    scrambuttons[moveidx].config(font=('TkDefaultFont',18,'bold'))
    drawscram()

def prevscram():
    global is_last_scramble, drawcubemove
    is_last_scramble = True
    prevscrambtn['state'] = tk.DISABLED
    cube.reset()
    for n,i in enumerate(last_scramble):
        scrambuttons[n].config(text=i)
    drawcubemove = -1 # redraw cube on new scram
    end()

def nextscram():
    global is_last_scramble, scramble, drawcubemove
    if not is_last_scramble:
        last_scramble[:] = scramble
        scramble = cube.scramble()
    is_last_scramble = False
    prevscrambtn['state'] = tk.NORMAL
    cube.reset()
    for n,i in enumerate(scramble):
        scrambuttons[n].config(text=i)
    drawcubemove = -1
    end()

def selecttime(e=None): # on the listbox to change conf time frame
    global selsolvestats
    idx = solves - timelist.curselection()[0] # bro tkinter negative listbox indexes when
    s=timelist_selected.get()
    stuff = ''
    if s != 'time':
        stuff += f"{s} {timelist.get(timelist.curselection()[0])}\nselected "
    selsolvestats = cube.getone(idx)
    stuff += f'''solve {idx}
{datetime.fromtimestamp(selsolvestats[0]).strftime("%x %X")}
{[selsolvestats[1],str(selsolvestats[1]+2)+"+","DNF("+str(selsolvestats[1])+")"][selsolvestats[3]]}'''
    statstr.set(stuff)

def copyscram(): # on selected listbox item
    if not solves: return
    root.clipboard_clear()
    root.clipboard_append(selsolvestats[2])
    copyselscrambtn.config(activebackground='green')
    root.after(500,copyselscrambtn.config,{'activebackground':'black'})

def confirm(judgement):
    if not solves: return
    a = timelist.curselection()[0]
    idx = solves-a
    cube.edit(idx,judgement)
    if timelist_selected.get()=='time':
        timelist.delete(a) #tkinter edit listbox element when
        timelist.insert(a,'DNF' if judgement == cube.DNF
                     else selsolvestats[1] + 2*(judgement==cube.PLUS2))
    else:
        updatetimelist() # affects all values above if i try to be effecient its chaos 
    updatesummary()
    timelist.selection_set(a)
    timelist.activate(a)
    timelist.yview_moveto(a)
    selecttime()

def updatesummary(): # ah yes lets make like 20+ sql calls every time i do a solve
    a = cube.gettimes() # cuz choose between what is easy and what is fast
    for b,(s,t) in enumerate(AVGSTUFF):# if you can golf this next line further put it on issues please
        m=float('inf');avgs=a if s==1 else['DNF'if j==m else j for j in['-'if n<s else round(sum(sorted(m if i=='DNF'else i for i in a[n-s:n])[t:-t if t else None])/(s-t*2),3)for n,i in enumerate(a,1)]]
        if len(avgs):
            summary[AVGS[b]][0].set(avgs[-1])
            bavg = min([i if isinstance(i,float) else float('inf') for i in avgs])
            summary[AVGS[b]][1].set(bavg if bavg!=float('inf') else 'DNF' if 'DNF' in avgs else '-')
        else:
            summary[AVGS[b]][0].set('-')
            summary[AVGS[b]][1].set('-')

def deltime():
    global solves, sessolves, cubed, sesscubed
    if not solves: return
    a = timelist.curselection()[0]
    cube.remove(solves-a)
    timelist.delete(a)
    solves -= 1
    cubed -= selsolvestats[1]
    if selsolvestats[0] >= start: # imagine flagging every solve if its at current session or not
        sesscubed -= selsolvestats[1]
        sessolves -= 1
    if solves:
        updatetimelist() # gotta do it this way
        selectfirsttime()
        updatesummary()
        timelist.yview_moveto(a)
    else:
        statstr.set("no solves yet")
    grind_solvevar.set(f"solve {solves} ({sessolves} sess)")
    grind_timevar.set(f"cubed {cube.fmtsecs(int(cubed))} ({cube.fmtsecs(int(sesscubed))})")

def begin(): # for cube scramble vis
    global drawcubemove
    if 0 <= drawcubemove < 30:
        scrambuttons[drawcubemove].config(font=('TkDefaultFont',18))
    drawcubemove = -1
    cube.reset()
    drawscram()

def prev():
    global drawcubemove
    if 0 <= drawcubemove < 30:
        scrambuttons[drawcubemove].config(font=('TkDefaultFont',18))
    if drawcubemove == 30:
        drawcubemove -= 1
    if drawcubemove >= 0:
        s = last_scramble[drawcubemove] if is_last_scramble else scramble[drawcubemove]
        cube.notate(s+"'" if len(s)==1 else s.replace("'",''))
        drawscram()
        drawcubemove -= 1
        if drawcubemove>=0: scrambuttons[drawcubemove].config(font=('TkDefaultFont',18,'bold'))
    else:
        end()

def next():
    global drawcubemove
    if 0 <= drawcubemove < 30:
        scrambuttons[drawcubemove].config(font=('TkDefaultFont',18))
    if drawcubemove < 29:
        drawcubemove += 1
        s = last_scramble if is_last_scramble else scramble
        scrambuttons[drawcubemove].config(font=('TkDefaultFont',18,'bold'))
        cube.notate(s[drawcubemove])
        drawscram()
    elif drawcubemove == 29: drawcubemove += 1
    else:
        begin()

def end():
    global drawcubemove
    s = last_scramble if is_last_scramble else scramble
    if 0 <= drawcubemove < 30:
        scrambuttons[drawcubemove].config(font=('TkDefaultFont',18))
    for n in range(29-drawcubemove,0,-1):
        cube.notate(s[-n])
    drawcubemove = 30
    drawscram()

def spaceupfr():
    global lastpress, timeready, timing
    if timeready:
        timeready = False
        timing = True
        timerloop()
    timerlabel.config(fg='white') 
    lastpress = float('inf')

def spacedown(e):
    t=time.time() # function oriented + globals = better object oriented
    global lastpress, timeready, timing, is_last_scramble, solves, sessolves, cubed, sesscubed
    if timing: # stopping timer
        solves += 1
        sessolves += 1
        cubed += t-timerelease
        sesscubed += t-timerelease
        timing = False
        timerstr.set('{:.3f}'.format(round(t-timerelease,3)))
        hide.place_forget()
        if is_last_scramble:
            scramble[:] = last_scramble
            is_last_scramble = False
        nextscram()
        if timelist_selected.get() != 'time':
            timelist_selected.set("time")
            updatetimelist()
        timelist.insert(0, timerstr.get())
        cube.new(t-timerelease, last_scramble)
        selectfirsttime()
        updatesummary()
        grind_solvevar.set(f"solve {solves} ({sessolves} sess)")
        grind_timevar.set(f"cubed {cube.fmtsecs(int(cubed))} ({cube.fmtsecs(int(sesscubed))})")
    else: # preparing timer
        if t - lastpress > .5:
            hide.place(x=0,y=0,relwidth=1,relheight=1)
            timerstr.set('0.0')
            timerlabel.config(fg='lightgreen')
            timeready = True
        elif not timeready:
            timerlabel.config(fg='yellow')
        lastpress = t

def loadcst(): # this was the final stretch yeeeee
    global cubed, solves
    try:
        cube.loadfile(askopenfilename())
        updatetimelist()
        updatesummary()
        cubed = cube.totaltime()
        solves = cube.solves() # counter
        grind_timevar.set(f"cubed {cube.fmtsecs(int(cubed))} ({cube.fmtsecs(int(sesscubed))})")
        grind_solvevar.set(f"solve {solves} ({sessolves} sess)")
        if solves: selectfirsttime()
        selecttime()
    except:
        loadcstbtn.config(activebackground='red',background='red')
        root.after(500,loadcstbtn.config,{'activebackground':'black','background':'black'})

def copytimes():
    if not solves: return
    avgstr = timelist_selected.get()
    avgof,trim = AVGSTUFF[AVGS.index(avgstr)]
    solve = solves-timelist.curselection()[0]
    times = cube.getrange(solve,avgof)
    if len(times) != avgof:
        avgof,avgstr,trim,times = 1,'time',0,[times[-1]]
    avg = times[0] if avgof==0 else round(sum(sorted([float('inf')if j==cube.DNF else i+2*(j==cube.PLUS2) for i,j in times
                                        ])[trim:-trim if trim else None])/(avgof-2*trim),3)
    if avg==float('inf'): avg = 'DNF'
    times = [[str(t),f"{t+2}+",f"DNF({t})"][j] for t,j in times]
    root.clipboard_clear()
    root.clipboard_append(f'''generated by TkTimer on {datetime.now().strftime("%x %X")}
{avg} {avgstr} from solve{"s" if avgof!=1 else ""} {solve-avgof+1} {"to "+str(solve) if avgof!=1 else ""}
{", ".join(times)}''')
    copytimebtn.config(activebackground='green')
    root.after(500,copytimebtn.config,{'activebackground':'black'})

def timerloop(): # other func not called by gui directly
    if timing:
        timerstr.set('{:.1f}'.format(time.time()-timerelease))
        root.after(100, timerloop)

def spaceup(e): # this is where timer delay comes from lel
    global timerelease
    timerelease=time.time()
    root.after(100,lambda:(spaceupfr() if time.time()-lastpress>.1 else 0))

def updatetimelist(e=None):
    timelist.delete(0, tk.END)  #clear listbox
    times = cube.gettimes()
    solves,trim = AVGSTUFF[AVGS.index(timelist_selected.get())]
    lentimes = len(times)
    s = slice(trim,-trim if trim else None)
    trim = solves-trim*2
    avgs = times if solves == 1 else [ '-' if n<solves else
            round(sum(sorted([float('inf') if i=='DNF' else i for i in times[n-solves:n]])[s]) / trim,3)
            for n,i in enumerate(times,start=1)
    ]
    for n,i in enumerate(avgs): #populate listbox again
        timelist.insert(-n, 'DNF' if i == float('inf') else i)
    if e:
        selectfirsttime()

def selectfirsttime():
    timelist.selection_clear(0,tk.END)
    timelist.selection_set(0)
    timelist.activate(0)
    timelist.yview_moveto(0)
    selecttime(0)

def drawscram():
    for face in range(6):
        for x in range(3):
            for y in range(3): # noo xy yx chaos idk why this even works
                cubecanvas.itemconfig(arr[face][x][y],fill=COLS[cube.cube[face][y][x]])

timerlabel = tk.Label(root,textvariable=timerstr,font=("TkDefaultFont",100))
timerlabel.place(anchor='center',relx=.5,rely=.5)

fscram.grid_columnconfigure(list(range(1,16)), weight=1) # individual sections
copyscrambtn = tk.Button(fscram,text='C',fg='yellow',command=copycurrentscram)
copyscrambtn.grid(row=0,column=16,rowspan=2,sticky='NSW')
scrambuttons = [tk.Button(fscram,text=i,borderwidth=0,highlightthickness=0,command=lambda x=n:cubegotomove(x))
                for n,i in enumerate(last_scramble)]
for n,i in enumerate(scrambuttons):
    i.grid(row=n//15,column=1+(n%15),sticky='NSEW')
prevscrambtn = tk.Button(fscram,text='<',fg='cyan',command=prevscram,state=tk.DISABLED)
prevscrambtn.grid(row=0,column=0,sticky='NSE') # add commands to prev and next
tk.Button(fscram,text='>',fg='lime',command=nextscram).grid(row=1,column=0,sticky='NSE')

timelist_scroll = tk.Scrollbar(ftimelist)
timelist_option = tk.OptionMenu(ftimelist,timelist_selected,*AVGS,command=updatetimelist) # select avg to view
timelist = tk.Listbox(ftimelist,width=8) # wow sizes in characters i like
timelist.config(yscrollcommand=timelist_scroll.set) #geekforgeeks is only
timelist_scroll.config(command=timelist.yview) #good at tkinter i swear
timelist_option.pack(side=tk.TOP,fill=tk.X)
timelist_scroll.pack(side=tk.RIGHT,fill=tk.Y)
timelist.pack(side=tk.RIGHT,fill=tk.Y)
timelist.bind('<<ListboxSelect>>',selecttime)

tk.Label(fgrindstats,fg='pink',textvariable=grind_timevar,anchor='e').pack(side=tk.TOP,expand=True,fill=tk.X)
tk.Label(fgrindstats,fg='orange',textvariable=grind_solvevar,anchor='e').pack(side=tk.RIGHT,expand=True,fill=tk.X)
loadcstbtn = tk.Button(fgrindstats,text='load csTimer',pady=0,borderwidth=0,highlightthickness=0,command=loadcst,anchor='w',fg='#FF0099')
loadcstbtn.pack(side=tk.LEFT,fill=tk.Y)

cubecanvas = tk.Canvas(fcube,width=100,height=100,highlightthickness=0)
cubecanvas.bind("<Configure>",
    lambda e:[cubecanvas.scale("all",0,0,*[e.width/cubecanvas.winfo_reqwidth()]*2),
              cubecanvas.config(width=e.width,height=e.width)])
stickerpoints = [ # xy and yx chaos begins here
    [[[(50 + 7*x - 7*y,18 + 4*x + 4*y)] for x in range(4)] for y in range(4)],
    [[[(50 + 7*x - 7*y,72 + 4*x + 4*y)] for x in range(4)] for y in range(4)],
    [[[(29 + 7*x, 30 + 9*y + 4*x)] for x in range(4)] for y in range(4)],
    [[[(75 + 7*x, 11 + 9*y + 4*x)] for x in range(4)] for y in range(4)],
    [[[(50 + 7*x, 42 + 9*y - 4*x)] for x in range(4)] for y in range(4)],
    [[[(4 + 7*x, 22 + 9*y - 4*x)] for x in range(4)] for y in range(4)]
]
arr = [[[cubecanvas.create_polygon([(sp[x][y],sp[x+1][y],sp[x+1][y+1],sp[x][y+1])],fill=COLS[n],outline='black')for x in range(3)] for y in range(3)]for n,sp in enumerate(stickerpoints)]
cubecanvas.pack(side=tk.TOP,expand=True,fill=tk.X)
tk.Button(fcube,text='<<',fg='red',command=begin).pack(side=tk.LEFT,fill=tk.X,expand=True)
tk.Button(fcube,text='<',fg='orange',command=prev).pack(side=tk.LEFT,fill=tk.X,expand=True)
tk.Button(fcube,text='>',fg='green',command=next).pack(side=tk.LEFT,fill=tk.X,expand=True)
tk.Button(fcube,text='>>',fg='cyan',command=end).pack(side=tk.LEFT,fill=tk.X,expand=True)

tk.Label(fsummary,text="now").grid(row=1,column=2,sticky='we')
tk.Label(fsummary,text="best").grid(row=1,column=3,sticky='we')
for n,a in enumerate(AVGS):
    tk.Label(fsummary,text=a,fg=COLS[n]).grid(row=2+n,column=1,sticky='we')
    tk.Label(fsummary,textvariable=summary[a][0]).grid(row=2+n,column=2,sticky='we')
    tk.Label(fsummary,textvariable=summary[a][1]).grid(row=2+n,column=3,sticky='we')

tk.Label(fconftime,textvariable=statstr).pack(side=tk.TOP)
copyselscrambtn = tk.Button(fconftime,text='copy scramble',command=copyscram)
copyselscrambtn.pack(side=tk.TOP,expand=False,fill=None)
copytimebtn = tk.Button(fconftime,text="copy time(s)",command=copytimes)
copytimebtn.pack(side=tk.TOP,expand=False,fill=None)
tk.Button(fconftime,text='ok',fg='lightgreen',command=lambda:confirm(cube.OK)).pack(side=tk.LEFT,fill=tk.Y,expand=True)
tk.Button(fconftime,text='+2',fg='orange',command=lambda:confirm(cube.PLUS2)).pack(side=tk.LEFT,fill=tk.Y,expand=True)
tk.Button(fconftime,text='dnf',fg='pink',command=lambda:confirm(cube.DNF)).pack(side=tk.LEFT,fill=tk.Y,expand=True)
tk.Button(fconftime,text='del',fg='red',command=deltime).pack(side=tk.LEFT,fill=tk.Y,expand=True)

end()
updatetimelist()
updatesummary()
if solves: selectfirsttime()

root.bind("<KeyPress-space>",spacedown)
root.bind("<KeyRelease-space>",spaceup)
root.bind("<Configure>",lambda e:timerlabel.configure(font=('TkDefaultFont',root.winfo_width()//15)))
root.mainloop()
