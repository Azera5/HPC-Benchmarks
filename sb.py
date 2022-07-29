import os
import os.path
import subprocess
import datetime
import inspect
import shutil
import time
import math
import fnmatch
import re
import argparse
from os.path import exists 
from argparse import RawTextHelpFormatter

#Für das Debugging
import sys
from io import StringIO

"""
Hilfsvariablen
"""
#Anzahl unterstützter Benchmarks (HPL, OSU, ...)
benchcount = 2
misc_id = 0
hpl_id = 1
osu_id = 2
#Unterstützte IDs sollten in der Liste unten auftauchen *und* vom tag-id-switcher beherrscht werden
bench_id_list = [misc_id, hpl_id, osu_id]

#Das Verzeichnis an dem das Programm ausgeführt wird (autogeneriert)
loc = ''

#Project Folder (Results and Run)
project_pth=''

#Binary-Pfade zu relevanten Programmen
spack_xpth = ''
hpl_handler_xpth = ''

#Python Version für matplotlib (z.B. python%gcc@8.5.0)
python_matplotlib = ''

#Pfade zu den Benchmarks (Index <=> Benchmark-ID; Ersteintrag führt zur allg. config!)
bench_pths = []
#Info-Arrays für Verfügbarkeit von packages (Index <=> Benchmark-ID; Ersteintrag ist ein Dummy!)
#Muster: [[<<verfügar>>, <<miss>>, <<error>>], ...]
pkg_info = []

#Sammelt kürzliche Fehlermeldungen
errorstack = []
#Trägt Informationen des Config-Ordners; Ersteintrag für Metadaten
#Index: [Benchmark-id][Profil-Nr.][Abschnitt][Zeile im Abschnitt]
cfg_profiles = [[],[],[],[]]
#Initialnachricht
initm = ''
#Ob der Info-Refresh erzwungen werden soll
get_info = False
#Dieser Faktor definiert die Breite verschiedener Menüelemente
form_factor_menu = 0
#Beschreibt die Breite des Terminals
t_width = 0
#Menüpadding links
ml = ''
#Menüpadding rechts
mr = ''
#Aktualisierungsrate für package-Infos
refresh_intervall = 0
#Aktualisierungsrate für package-Infos
colour_support = 0
#Variable zum Sammeln von Informationen für die Menüausgabe
menutxt=''
#Debug-Informationen anzeigen
dbg=True

#Schriftfarb-Konstanten
"""
0 = grau '\33[90m'
1 = schwarz '\33[30m'
2 = weiß '\33[37m'
3 = weiß2 '\33[97m'
4 = grün '\33[32m'
5 = grün2 '\33[92m'
6 = gelb '\33[33m'
7 = gelb2 '\33[93m'
8 = rot '\33[31m'
9 = rot2 '\33[91m'
10 = blau '\33[34m'
11 = blau2 '\33[94m'
12 = violett '\33[35m'
13 = violett2 '\33[95m'
14 = beige/türkis '\33[36m'
15 = beige/türkis2 '\33[96m'
"""
FCOL = [ '\33[90m', '\33[30m', '\33[37m', '\33[97m', '\33[32m', '\33[92m', '\33[33m', '\33[93m', '\33[31m', '\33[91m', '\33[34m', '\33[94m', '\33[35m', '\33[95m', '\33[36m', '\33[96m' ]
FCOL_M = [ '\33[90m', '\33[30m', '\33[37m', '\33[97m', '\33[32m', '\33[92m', '\33[33m', '\33[93m', '\33[31m', '\33[91m', '\33[34m', '\33[94m', '\33[35m', '\33[95m', '\33[36m', '\33[96m' ]

#Hintergrundfarb-Konstanten
"""
0 = grau '\33[100m'
1 = schwarz '\33[40m'
2 = weiß '\33[47m'
3 = weiß2 '\33[107m'
4 = grün '\33[42m'
5 = grün2 '\33[102m'
6 = gelb '\33[43m'
7 = gelb2 '\33[103m'
8 = rot '\33[41m'
9 = rot2 '\33[101m'
10 = blau '\33[44m'
11 = blau2 '\33[104m'
12 = violett '\33[45m'
13 = violett2 '\33[105m'
14 = beige/türkis '\33[46m'
15 = beige/türkis2 '\33[106m'
"""
FBGR = [ '\33[100m', '\33[40m', '\33[47m', '\33[107m', '\33[42m', '\33[102m', '\33[43m', '\33[103m', '\33[41m', '\33[101m', '\33[44m', '\33[104m', '\33[45m', '\33[105m', '\33[46m', '\33[106m' ]
FBGR_M = [ '\33[100m', '\33[40m', '\33[47m', '\33[107m', '\33[42m', '\33[102m', '\33[43m', '\33[103m', '\33[41m', '\33[101m', '\33[44m', '\33[104m', '\33[45m', '\33[105m', '\33[46m', '\33[106m' ]

#Formatierungs-Konstanten
"""
0 = dick (bold) '\33[1m'
1 = kursiv (italic) '\33[3m'
2 = unterstr. (url) '\33[4m'
3 = markiert '\33[7m'
4 = blinkend '\33[5m'
5 = blinkend2 '\33[6m'
ggf. nicht alle unterstützt! (z.B. blinkend & kursiv)
"""
FORM = [ '\33[1m', '\33[3m', '\33[4m', '\33[7m', '\33[5m', '\33[6m' ]
FORM_M = [ '\33[1m', '\33[3m', '\33[4m', '\33[7m', '\33[5m', '\33[6m' ]

#Formatierung beenden
FEND = '\33[0m'

#Testtabellen zum ausdrucken, später kann man highlight Werte tabellarisch organisieren und darstellen
best_list = [['test', 'liste'],['1000', 'GB/s'],['47', 'TFLOPS'],['...', '...']]
test_list1 = [['141535', '5.25', 'asfasf'],['GB/s', 'GB/s', 'GB/s'],['111111', '22222222', '333333'],['...', '...', '...']]
test_list2 = [['aaaaaa'],['bbbbbb'],['ccccccc'],['dddddddd']]


"""
Command-Line-Parameter
"""
def cl_arg():
    global cfg_profiles
    
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument('-i','--install',nargs='+',type=str,help=''+
    '<Benchmark> <cfg>,<cfg>,...,<cfg>\n'+
    '     e.g.: -i hpl 1,3-4,example\n\n'+
    'all: Install all benchmarks/cfg\n'+
    '     e.g.: -i all\n'+
    '           -i osu all\n\n')
    
    parser.add_argument('-r','--run',nargs='+',type=str,help=''+   
    'hpl <cfg>,<cfg>,...,<cfg>\n'+     
    '     e.g.: -r hpl 1,3-4,Test1\n' +
    '           -r hpl all <=> -r hpl\n\n' +
    'osu <test> <cfg>,<cfg>,...,<cfg> \n'+
    '     tests:{latency, bw, bcast, barrier, allreduce}\n'+
    '     e.g.: -r osu latency 1,3-4,example\n'+
    '           -r osu latency all <=> -r osu latency\n')
    
    parser.add_argument('-c','--clean',nargs=1,type=str,help=''+
    'projects: remove projects folder\n'+
    'install: remove all install scripts\n'+
    'log: remove log.txt (error-log file)\n' +
    'mem: remove mem.txt (run time variables)\n'+
    'all: remove projects, install scripts, log.txt and mem.txt\n'+
    '     e.g.: -c projects\n'+
    '     e.g.: -c all\n')
    
    evaluate_paths()
    args= parser.parse_args()
    
    #Clean files
    if args.clean:       
        return  print(clean(args.clean[0]))
    
    prepare_array()
    check_data()
    check_dirs()   
    
    get_cfg(tag_id_switcher(misc_id))
   

    
    #Install Benchmarks
    if args.install:        
        expr=[]
        #Alle Profile aller Benchmarks werden installiert
        if args.install[0]=='all':
            #expr=get_all_specs('hpl')+get_all_specs('osu') <--- Überholt!
            for id in bench_id_list:
                if id==misc_id:
                    continue
                get_cfg(tag_id_switcher(id))
                expr+=get_all_specs(tag_id_switcher(id))   
        
        #Nur bestimmte Benchmarks werden installiert    
        else:            
            #Nur bestimmte Profile werden installiert
            if len(args.install)>1 and args.install[1]!= 'all':
                names=farg_to_list(args.install[1],args.install[0])                
                get_cfg(args.install[1])
                
                for _ in names:
                    expr=get_all_specs(args.install[0],names)
            
            #Alle Profile werden installiert
            else:
                get_cfg(args.install[0],args.install[1])
                expr=get_all_specs(args.install[0])                
        install_spec(expr)
    
    #Run Benchmarks
    if args.run:        
        args_len=len(args.run)        
        
        #run hpl
        if args.run[0]=='hpl':            
            if args_len < 2 or args.run[1]=='all':
                get_cfg(args.run[0])
                pth=bench_run(tag_id_switcher(args.run[0]),'all')            
                print(shell(str('sbatch '+pth[pth.find('/'):pth.find('.sh')+3])))
            else:
                get_cfg(args.run[0],args.run[1])               
                pth=bench_run(tag_id_switcher(args.run[0]),args.run[1])            
                print(shell(str('sbatch '+pth[pth.find('/'):pth.find('.sh')+3])))
       
        #run osu
        if args.run[0]=='osu':
            if args_len < 3 or args.run[2]=='all':
                get_cfg(args.run[0])
                pth=bench_run(tag_id_switcher(args.run[0]),'all',args.run[1])
                print(shell(str('sbatch '+pth[pth.find('/'):pth.find('.sh')+3])))
            else:
                get_cfg(args.run[0],args.run[2])
                pth=bench_run(tag_id_switcher(args.run[0]),args.run[2],args.run[1])
                print(shell(str('sbatch '+pth[pth.find('/'):pth.find('.sh')+3])))
        
    #Start via Menu   
    if not args.install and not args.run and not args.clean:
        for id in bench_id_list:
            if id==misc_id:
                continue
            get_cfg(tag_id_switcher(id))
        menu()



"""
Wichtige Vorlauf-Funktionen
""" 
#Die meisten Funktionen besitzen hier eine .time Attribut zum Merken des Zeitverbrauchs 

#Bestimmt die genutzten Pfade
def evaluate_paths():
    timestart = time.time()
    global initm, spack_xpth, hpl_handler_xpth, loc, project_pth  
         
    loc = str(os.path.dirname(os.path.abspath(__file__)))
    #Vorbereitung der Pfad- & Info-Arrays (letztere nicht hier befüllt)
    for id in bench_id_list:
        bench_pths.append('empty')
        pkg_info.append(['empty', 'empty', 'empty'])
    
    #Kalkulation der Pfade: der tag_id_switcher muss die IDs natürlich kennen!
    for id in bench_id_list:
        if id==misc_id:
            pth = loc+'/configs/'
        else:
            pth = loc+'/configs/{}/'.format(tag_id_switcher(id))
        bench_pths[id]=pth
        loadprogress()

    #Hier werden die statischen Pfade zu den Binaries (<<Name>>_xpath) bestimmt 
    spack_xpth = str(file_r(bench_pths[misc_id]+'config.txt', 4)).rstrip()
    if check_path(spack_xpth)==False:
        r_list = str(shell('find ~ -executable -name spack -path \'*/spack/bin/*\'')).replace('\n',' ').split()        
        #Wir nehmen die erstbeste spack Binary, wenn nichts per Hand spezifiziert wurde
        spack_xpth = r_list[0].strip()
        file_w(bench_pths[misc_id]+'config.txt',spack_xpth,4)
        initm+='Da kein Verzeichnis zur spack Binary spezifiziert war, wurde das Erstbeste von ~/... aus genommen:\n'+spack_xpth+'\n' 
        
    #Hier kommen spezielle Pfade für verschiednste Teilaufgaben
    hpl_handler_xpth = loc+'/hpl_dat_handler.py'
    evaluate_paths.time+=time.time()-timestart
    project_pth=str(file_r(bench_pths[misc_id]+'config.txt', 6)).rstrip()
    if check_path(project_pth[:project_pth.find('/project')])==False:
        project_pth=loc+'/projects'
        file_w(bench_pths[misc_id]+'config.txt',project_pth,6)
evaluate_paths.time=0

#Vorbereitung des Arrays mit den Profildaten
def prepare_array():
    timestart = time.time()
    #Hinweis: ['test']*n <=> ['test, 'test', ...] vgl. ['test'*n] = ['testtesttest...']
    global cfg_profiles
    #Spezielle Angaben z.B. welche Partition/Nodes usw. gelten für Installationsdienste etc.
    cfg_profiles[misc_id].append([[]]*4)  
    #Für jeden Bench eine Liste, in jeder dieser Listen... 
    for id in bench_id_list:
        if id==misc_id:
            continue
        #...eine Liste pro Profil
        for _ in range(len(get_names(bench_pths[id]))):
            #Für jedes Profil existieren verschiedene Blöcke an Informationen (z.B. über SLURM-Einstellungen)
            cfg_profiles[id].append([[]]*5)
            loadprogress()
    prepare_array.time+=time.time()-timestart
prepare_array.time=0

#Nachsehen ob Fehlerlogs etc. existieren, welche Einstellungen herrschen
def check_data():
    timestart = time.time()
    loadprogress()
    global initm, mr, ml, colour_support, refresh_intervall, form_factor_menu ,loc
    if os.path.isfile('{}/log.txt'.format(loc))==False:     
        shell('touch {}/log.txt'.format(loc))
        initm+='Ein Errorlog (log.txt) wurde erstellt ...\n'
    if os.path.isfile('{}/mem.txt'.format(loc))==False:     
        txt='---------Param. stehen in eckigen Klammern---------'
        txt+='\nform_factor_menu\t\t\t[3]'
        txt+='\nrefresh_intervall\t\t\t[0]'
        txt+='\ncolour_support\t\t\t[0]'
        txt+='\ndebug_mode\t\t\t[0]'
        txt+='\n--------------------Zeitmessung--------------------'
        txt+='\n---------------automatische Eingaben---------------'
        txt+='\nevaluate_paths\t\t\t[]'
        txt+='\nprepare_array\t\t\t[]'
        txt+='\ncheck_data\t\t\t[]'
        txt+='\ncheck_dirs\t\t\t[]'
        txt+='\nget_cfg\t\t\t[]'
        txt+='\ncreate_mem\t\t\t[]'
        file_w('{}/mem.txt'.format(loc), txt, 'a')
        initm+='Ein Einstellungsarchiv (mem.txt) wurde erstellt ...\n'
    else:
        form_factor_menu = int(get_mem_digit(1))
        refresh_format_params()
        refresh_intervall = int(get_mem_digit(2))
        colour_support = int(get_mem_digit(3))
        color_check()
        debug_mode_switch(int(get_mem_digit(4)))
    check_data.time+=time.time()-timestart
check_data.time=0

#Nachsehen ob config-Verzeichnisse etc. existieren
def check_dirs():
    global initm
    timestart = time.time()
    for pth in bench_pths:
        loadprogress()
        if bench_pths.index(pth)==0:
            continue
        if os.path.isdir(pth[:-1])==False:
            #Hinweis: '/dir1/dir2/.../'[:-1] <=> '/dir1/dir2/...'
            shell('mkdir -p '+pth[:-1])
            initm+='Ein Config-Verzeichnis (.../configs/{}) für {} wurde erstellt ...\n'.format(tag_id_switcher(bench_pths.index(pth)))
    check_dirs.time+=time.time()-timestart
check_dirs.time=0

#Liest die Profile aus den lokalen Configs aus
def get_cfg(bench,farg='all'):
    timestart = time.time()
    global cfg_profiles
    print('\nlade {}'.format(bench))
    
    sublist, spec_ = [], []
    id = tag_id_switcher(bench)
    
    if farg=='all':
        names = get_cfg_names(get_cfg_path(bench), bench)
    else:
        names = farg_to_list(farg,bench)
        cfg_profiles[id]=cfg_profiles[id][:len(names)]
    

    #Für jedes Profil...
    for p in names:
        abschnitt = 1
        txtfile = open(get_cfg_path(bench)+p, 'r')
        txtlist = txtfile.readlines()
        #...jede Zeile passend einsortieren!
        for ln in txtlist:
            #Eine reguläre Zeile wird in der Subliste gesammelt
            if (ln.find('---')==-1) and (ln.find('[Pfad')==-1):
                sublist.append(config_cut(ln))
                if abschnitt==1:
                    spec_.append(ln)
            #Eine Trennzeile löst die Eingliederung eines gefüllten Blocks aus
            elif (len(sublist)>0) and (ln.find('---')>-1):
                cfg_profiles[id][names.index(p)][abschnitt]=sublist
                abschnitt+=1
                sublist=[]
                continue
            #Eine folgende Trennzeile macht gar nichts
            else:
                continue                   
        #Normale Profile brauchen auch noch Metadaten
        if id != misc_id:
            spec = get_spec(spec_,bench)
            cfg_profiles[id][names.index(p)][0] = [p, get_cfg_path(bench)+p, get_target_path(spec), spec]  
        #Letzter Block & Resett der Variablen
        cfg_profiles[id][names.index(p)][abschnitt]=sublist
        sublist, spec_, spec = [], [], '' 
        #Kleine Illustration des Ladestandes
        progressbar(names.index(p)+1, len(names))        
        txtfile.close()
    get_cfg.time+=time.time()-timestart    
get_cfg.time=0

def save_times():
    c = count_line('{}/mem.txt'.format(loc))
    file_w('{}/mem.txt'.format(loc),'evaluate_paths[{}]'.format(str(evaluate_paths.time)),c-5)
    file_w('{}/mem.txt'.format(loc),'prepare_array[{}]'.format(str(prepare_array.time)),c-4)
    file_w('{}/mem.txt'.format(loc),'check_data[{}]'.format(str(check_data.time)),c-3)
    file_w('{}/mem.txt'.format(loc),'check_dirs[{}]'.format(str(check_dirs.time)),c-2)
    file_w('{}/mem.txt'.format(loc),'get_cfg[{}]'.format(str(get_cfg.time)),c-1) 

#Sucht Matplotlib (installiert falls nicht Vorhanden)
def find_matplot_python_hash():
    pth_spack=spack_xpth[:spack_xpth.find('spack')+5]
    pth=shell('find {} -name matplotlib'.format(pth_spack))
   
    #Kein matplotlib installiert 
    if pth=='':
        sourcen='source {}/share/spack/setup-env.sh; '.format(spack_xpth[:-9])
        py=shell('find '+pth_spack+' -name python | grep bin').split('\n')
        count=len(py)-1
        #Eine Pythonversion vorhanden
        if  count==1:
            print(shell(sourcen+'spack load python; python -m pip install matplotlib'))
            return ''
            
        #Mehrere Pythonversionen vorhanden
        #py in Form von: spack/opt/spack/linux-centos8-zen3/gcc-12.1.0/python-3.9.12-6ewjgugumhth6r56gvjxhdtq6tvowln7/bin/python 
        #Wir brauchen den hash: 6ewjgugumhth6r56gvjxhdtq6tvowln7
        else:
            py=py[0][py[0].find('python-')+7:py[0].find('/bin')]
            py_hash=py[py.find('-')+1:]
            print(shell(sourcen+'spack load python /'+py_hash+'; python -m pip install matplotlib'))
            return '/'+py_hash
            
    #Matplotlib ist installiert 
    #Pfad- bzw. Hashsuche
    pth=pth[pth.find('python'):].replace('-','',1)
    pth=pth[pth.find('-')+1:pth.find('/')]
    return '/'+pth
   
"""
Debug- & Hilfs-Funktionen
"""

#Fortschrittsanzeige als Prozentzahl, wieviele Aufgaben haben wir gegenwärtig (curr) prozentual bzgl. aller (full) erledigt? 
def progressper(curr, full, name):
    #time.sleep(0.1)
    if curr!=full:
        print('lade '+name+'... '+str(int(curr/full*100))+'%', end='\r')
    elif curr==full:
        print('lade '+name+'... '+str(int(curr/full*100))+'%')

#Fortschrittsanzeige als sich füllender Balken
def progressbar(curr, full):
    #time.sleep(0.1)
    if form_factor_menu!=0:
        width = form_factor_menu
    else:
        width = int(t_width/4)
    perc = str(int(curr/full*100))+'%'
    sym_p = int(width * (curr/full))     
    sym_e = width-sym_p
    if sym_e > len(perc):
        sym_e = width-(sym_p+len(perc))
        print('[{}]'.format('='*sym_p+' '*sym_e+perc), end='\r')
    else:
        print('[{}]'.format('='*sym_p+' '*sym_e), end='\r')

#Aktivitätsanzeige in . -> .. -> ... -> . etc.
def loadprogress(txt = ''):
    #time.sleep(0.1)
    if(loadprogress.c<3):
        loadprogress.c+=1
    else:
        loadprogress.c=1
    print(txt+'.'*loadprogress.c, end='\r')
loadprogress.c=0

#In welcher Funktion ist wann, welche Exception o.a. Unregelmäßigkeit aufgetreten?
def error_log(txt):
    global errorstack
    t = time.localtime()
    txt = str(inspect.stack()[1][3])+' [Funktion] '+time.strftime("%d-%m-%Y---%H:%M:%S", t)+' [Zeitpunkt] '+txt+'\n'
    file_w('{}/log.txt'.format(loc), txt, 'a')
    errorstack.append(FCOL[15]+str(inspect.stack()[1][3])+FEND+' [Funktion] '+time.strftime("%d-%m-%Y---%H:%M:%S", t)+' [Zeitpunkt] '+txt+'\n')

#Prüft ob der Fehlerstack leer ist
def check_err_stack():
    if len(errorstack)!=0:
        return '...entries available'
    else:
        return ''

#Noch nicht fertig: Es klappt mit den Verzeichnissen noch nicht ganz! <--- TODO
#Prüft ob Projekte fertig geworden sind
def check_status():
    global menutxt
    if os.path.isdir(loc+'/projects')==True:
        print('#Wir haben den Projekte Ordner gefunden')
        dir_list = get_dirs(loc+'/projects/')
        for d in dir_list:
            print('untersuchen ->>> '+loc+'/projects/'+str(d)+'/ready_signal')
            #Das Signal wird nur in die Resultat Ordner geschrieben
            if d.find('[results]')==-1:
                print('#Der Pfad interessiert uns nicht: '+d)
                continue
            if os.path.isfile(loc+'/projects/'+str(d)+'/ready_signal')==True:
                print('#In diesem Ordner gab es ein Signal!')
                menutxt+=FBGR[13]+str(d)+' is ready!'+FEND+'\n'
                if dbg==True:
                    print('#Wir setzen noch einen Zeitstempel')
                    menutxt+=FCOL[15]+os.path.getmtime(loc+'/projects/'+str(d)+'/ready_signal')+FEND+'\n'
    else:
        print('#nichts passiert')
        menutxt+=''
            

#Wertet einen Terminalbefehl aus
def shell(cmd):
    global menutext
    try:
        #Ausgabe soll nicht direkt auf's Terminal
        p = subprocess.run(str(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        if(p.returncode==0 and dbg==True):
            error_log('{} used the subshell for >>'.format(str(inspect.stack()[1][3]))+cmd+'<< with a non zero return')
            #menutxt=ml+FCOL[15]+'{} used the subshell for >>'.format(str(inspect.stack()[1][3]))+cmd+'<< with a non zero return'+FEND
        #.stdout liefert einen Binärstring desw. die Dekodierung
        return p.stdout.decode('UTF-8')
    except Exception as exc:
        error_log(' {} [Exception]'.format(type(exc).__name__)+'\nshell wurde aufgerufen aus: '+str(inspect.stack()[1][3]))

#Wertet einen Python-Ausdruck aus
def code_eval(expr):   
    #Vorbereitung; Umleidung der Standardausgabe (print() hat z.B. keinen direkten return...)
    primary_stdout = sys.stdout
    aux_stdout = StringIO()
    sys.stdout = aux_stdout 
    
    #Ausführung
    r = eval(expr)    
    #sto = aux_stdout.getvalue()
    sys.stdout = primary_stdout
    inftxt=''
    
    if dbg==True and colour_support==1:
        inftxt+=ml+FCOL[0]+'teal or beige colored text \t\t<=> return'+FEND+'\n'
        inftxt+=ml+FCOL[0]+'white colored text \t\t\t<=> stdout'+FEND+'\n'
        inftxt+='\n\n'
    
    #Passend formatierte Ausgabe
    try:
        headtxt=FORM[0]+str(type(r))+' [type]'+FEND
        return inftxt+'{}'.format(FBGR[14]+headtxt+' '*(int(t_width*0.5)-len(headtxt))+'\n'+FCOL[15]+FORM[0]+str(r)+FEND+'\n'+FCOL[3]+FORM[0]+aux_stdout.getvalue()+FEND)+'\n'
        
    except Exception as exc:
        error_log(' {} [Exception]'.format(type(exc).__name__))
        headtxt=FORM[0]+str(type(r))+' [type] --- '+' {} [Exception]'.format(type(exc).__name__)+FEND
        return inftxt+'{}'.format(FBGR[14]+headtxt+' '*(int(t_width*0.5)-len(headtxt))+'\n'+FCOL[15]+FORM[0]+str(r)+FEND+'\n'+FCOL[3]+FORM[0]+aux_stdout.getvalue()+FEND)+'\n'
    
#Liefert für eine Configzeile "123.4.5   [Parameter x]" nur die Zahl
def config_cut(line):
    c = line.find("[")
    if(c!=-1):
        line = line[:c]
    return line.strip()

#Ein Art Prompt für den Nutzer
def input_format():
    print(' ')
    print(FCOL[11]+FORM[0]+'Input:'+FEND+' ', end='')
    return input()

def clear():
    os.system('clear')
    #print('\n\n\n---Debugprint---\n\n\n')

#Bug: Liefert z.T. auch Verzeichnisse! <--- TODO
#Liefert Files, keine Verz.; Erwartet Pfade in der Form /dir1/dir2/.../
def get_names(pth):
    #print(pth)
    r = os.listdir(pth)
    #print(r)
    for _ in r:
        if os.path.isdir(_)==True:
            print(FCOL[8]+'gelöschter Pfad ->>>'+_+FEND)
            r.remove(_)
    return r

#Bug: Liefert z.T. Verzeichnisse auch nicht! <--- TODO
#Liefert alle Verzeichnis; Erwartet Pfade in der Form /dir1/dir2/.../
def get_dirs(pth):
    r = os.listdir(pth)
    for _ in r:
        if os.path.isdir(_)==False:
            print(FCOL[8]+'gelöschter Pfad ->>>'+_+FEND)
            r.remove(_)
    return r

#Liefert Textfiles eines bestimmten Typs (z.B. hpl_cfg_(...).txt)
def get_cfg_names(pth, typ):
    if typ == 'misc':
        return ['config.txt']
    else:
        return fnmatch.filter(get_names(pth), str(typ)+'_cfg_*.txt')

#Bekommt eine Liste bzgl. der Packages aus einer Config, liefert die package spec
def get_spec(cfg_list,bench):
    if bench == 'osu':
        bench='osu-micro-benchmarks'
    spec = bench    
    for _ in cfg_list:      
        _ = _.split('[')
        if len(_[0]) > 0:
            _[0]=_[0].rstrip()            
            if _[1].find('Version')!=-1:
                spec = spec+'@'
            elif _[1].find('Compiler')!=-1:
                spec = spec+'%'
            else:
                spec=spec+'^'                
            spec=spec+_[0]    
    return spec

#Liefert alle Specs einer Config-Liste bzw. eines Benchmarktyps
#Erhält Benchmarkname und (optional) Liste mit Config-Namen
def get_all_specs(bench,cfgs='all'):
    expr=[]
    for s in cfg_profiles[tag_id_switcher(bench)]:
        if cfgs=='all' or s[0][0] in cfgs:
            expr.append(s[0][3])    
    return expr

def config_out(bench_id):
    s=''
    for p in cfg_profiles[bench_id]:
        #Metadaten
        s +='\n'+ml+FCOL[15]+'- '*(int(t_width*0.2))+FEND+'\n'
        s +=ml+FBGR[15]+FCOL[1]+'{}'.format(p[0][0])+FEND+'\n'
        #Abschnitte der Profile
        for b in range(0,len(p)):
            s +=ml+FCOL[15]+'- - -{}. block- - -'.format(str(b))+FEND+'\n'
            #individuelle Lines des Blocks (=Strings) sind konkatenierbar
            for l in p[b]:
                if l=='':
                    s +=ml+ml+FCOL[0]+'leer'+FEND+'\n'
                else:
                    if l.strip()=='Kein Pfad gefunden!':
                        s +=ml+ml+FCOL[9]+l+FEND+'\n'
                    else:
                        s +=ml+ml+l+'\n'
    s +='\n'+ml+FCOL[15]+'- '*(int(t_width*0.2))+FEND+'\n\n'
    return s

#Switcht Bench-ID/Tag
def tag_id_switcher(bench):
    switcher={
        '0': 'misc',
        '1': 'hpl',
        '2': 'osu',
      
        'misc': misc_id,
        'hpl': hpl_id,
        'osu': osu_id
    }
    return switcher.get(str(bench))  

#Configpfad
def get_cfg_path(bench):
    if bench == 'hpl':
        return bench_pths[hpl_id]
    if bench == 'osu':
        return bench_pths[osu_id]
    if bench == 'misc':
        return bench_pths[misc_id]
    else:
        return -1 

#Zielpfad zu Binary&HPL.dat
def get_target_path(spec):
    pth = shell(spack_xpth+' find --paths '+spec)
    _ = pth.find('/home')
    r = (pth[_:]).strip()
    if r!='':
        return r+'/bin'
    else:
        error_log('Ein Pfad für '+spec[:spec.find('^')]+' konnte nicht gefunden werden!')
        return 'Kein Pfad gefunden!'

#Überschreibt die Zeilen von s_line (int) bis inkl. e_line (int) von file1 nach (ggf. mit Offset) file2
def transfer_lines(fpath_1, fpath_2, s_line = 0, e_line = -1, offset = 0):
    if e_line==-1:
        e_line = sum(1 for line in open(fpath_1))
    for _ in range(s_line,e_line+1):
        file_w(fpath_2,file_r(fpath_1,_),_+offset)

#Erwartet: Argumentliste zu -r/-i und der Benchname (String)
def farg_to_list(farg, bench):
    names = farg.split(',')
    for e in names:
        _ = str(e).find('-')
        #Umwandeln von Bindestrichnotation zu konkreten Zahlen: 3-5 -> 3 4 5
        if _!=-1:
            #Hinweis zum Slicen: string[a:b] <=> mit Index a aber ohne Index b
            #Hinweis zu range(x,y): Inkl. Index x aber kleiner Index y
            for i in range(int(e[:_]),int(e[_+1:])+1):
                names.append(i)
            #Eintrag abgearbeitet
            del names[names.index(e)]
    for e in names:
        #print('farg-to-list:'+str(names[names.index(e)]))
        names[names.index(e)] = bench+'_cfg_'+str(e)+'.txt'
    return names

#Eine Partition muss angegeben werden, sonst wird der User aufgefordert zu ergänzen
def eval_partition(profile, name): 
    error_log('Für '+name+' wurde keine Partition angegeben!')
    while True:
        #clear()
        print('Für '+name+' wurde keine Partition angegeben!')
        avail_part = shell('sinfo -h --format=%R')
        print('Vorschläge: '+avail_part)
        inp = input_format()
        if inp in avail_part.split():
            return inp
        else:
            continue

def write_slurm_params(profile, type):    
    #Shebang
    txt='#!/bin/bash\n'
    #Partition
    if profile[3][0]!='':
        txt+='#SBATCH --partition={}\n'.format(profile[3][0])
    else:         
        if type=='jobskript':             
            eval_partition(profile, profile[0][0])         
        if type=='batchskript':             
            eval_partition(profile, 'das Batch-Skript (<=> allg. config)')
    #Nodezahl
    if profile[3][1]!='':
        txt+='#SBATCH --nodes={}\n'.format(profile[3][1])
    #Anzahl der Prozesse
    if profile[3][2]!='':
        txt+='#SBATCH --ntasks={}\n'.format(profile[3][2])
    #Anzahl der Prozesse pro Node
    if profile[3][3]!='':       
        txt+='#SBATCH --ntasks-per-node={}\n'.format(profile[3][3])
    #Anzahl der CPUs pro Task/Prozess(default lt. SLURM-Doku: 1 Kern per Task)
    if profile[3][4]!='':
        txt+='#SBATCH --cpus-per-task={}\n'.format(profile[3][4])
    #Anzahl an allokiertem Speicher pro CPU
    if profile[3][5]!='':
        txt+='#SBATCH --mem-per-cpu={}\n'.format(profile[3][5])
    #Startzeitpunkt (z.B. now+180 <=> in drei Minuten starten)
    if profile[3][6]!='':
        txt+='#SBATCH --begin={}\n'.format(profile[3][6])
    #Zeitlimit 
    if profile[3][7]!='':
        txt+='#SBATCH --time={}\n'.format(profile[3][7])
    #Ziel-User für Emailbenachrichtigungen
    if profile[3][8]!='':
        txt+='#SBATCH --mail-user={}\n'.format(profile[3][8])
    #Valide Trigger für Benachrichtigungen
    if profile[3][9]!='':
        txt+='#SBATCH --mail-type={}\n'.format(profile[3][9])
    
    return txt

def find_binary(profile, bench_id):  
    if check_expr_syn(profile[0][3]):
        bin_path = shell(spack_xpth+' find --paths '+profile[0][3])
        #Die Benchmarks sollten vom home-Verzeichnis aus erreichbar sein... <-- TODO: klären ob das den Anforderungen entspricht
        _ = bin_path.find('/home')
        if _ == -1:
            error_log('Das package {} scheint nicht verfügbar zu sein! Profil: '.format(profile[0][3])+profile[0][0])+'\n'
        else:
            bin_path = ((bin_path[_:]).strip()+'/bin/')
        return bin_path
    else:
        error_log('Aus dem Profil '+profile[0][0]+'wird ein syntaktisch falsches spec extrahiert'+': {} '.format(profile[0][3]))
        return bin_path

def delete_dir(pth):
    shutil.rmtree(pth)

def clean(inpt = 'all'):
    pth = loc
    rtxt = ''
    if inpt=='log' or inpt=='all':
        if os.path.isfile('{}/log.txt'.format(loc))==False:
            rtxt+=FCOL[6]+'there was no log-file to be found:\na new one was created!\n'+FEND
            shell('touch log.txt')
        else:
            shell('rm {}/log.txt'.format(loc))
            shell('touch {}/log.txt'.format(loc))
    if inpt=='mem' or inpt=='all':
        if os.path.isfile('{}/mem.txt'.format(loc))==False:
            rtxt+=FCOL[6]+'there was no log-file to be found:\na new one was created!\n'+FEND
        else:
            shell('rm {}/mem.txt'.format(loc))
        txt='---------Param. stehen in eckigen Klammern---------'
        txt+='\nform_factor_menu\t\t\t[3]'
        txt+='\nrefresh_intervall\t\t\t[0]'
        txt+='\ncolour_support\t\t\t[0]'
        txt+='\ndebug_mode\t\t\t[0]'
        txt+='\n--------------------Zeitmessung--------------------'
        txt+='\n---------------automatische Eingaben---------------'
        txt+='\nevaluate_paths\t\t\t[]'
        txt+='\nprepare_array\t\t\t[]'
        txt+='\ncheck_data\t\t\t[]'
        txt+='\ncheck_dirs\t\t\t[]'
        txt+='\nget_cfg\t\t\t[]'
        txt+='\ncreate_mem\t\t\t[]'
        file_w('{}/mem.txt'.format(loc), txt, 'a')
        form_factor_menu = int(get_mem_digit(1))
        refresh_format_params()
        refresh_intervall = int(get_mem_digit(2))
        colour_support = int(get_mem_digit(3))
        color_check()
        debug_mode_switch(int(get_mem_digit(4)))
    if inpt=='projects' or inpt=='all':    
        if os.path.isdir(pth+'/projects')==False:
            rtxt+=FCOL[6]+'there was no /projects directory to be found!\n'+FEND
        else:
            delete_dir(pth+'/projects')
    
    if inpt=='install' or inpt=='all':
        if os.path.isfile(pth+'/install.sh')==False:
            rtxt+=FCOL[6]+'there was no install.sh to be found\n'+FEND
        else:
             shell('rm {}/install.sh'.format(loc))
        
        if os.path.isfile(pth+'/install.err')==False:
            rtxt+=FCOL[6]+'there was no install.err to be found\n'+FEND
        else:
             shell('rm {}/install.err'.format(loc))
        
        if os.path.isfile(pth+'/install.out')==False:
            rtxt+=FCOL[6]+'there was no install.out to be found\n'+FEND
        else:
             shell('rm {}/install.out'.format(loc)) 
             
    return rtxt+'done!'    
    

def color_check():
    global FCOL, FBGR, FORM
    if colour_support==1:
        for i in range(len(FCOL)):
            FCOL[i] = FCOL_M[i]
        for i in range(len(FBGR)):
            FBGR[i] = FBGR_M[i]
        for i in range(len(FORM)):
            FORM[i] = FORM_M[i]
    else:
        for i in range(len(FCOL)):
            FCOL[i] = ''
        for i in range(len(FBGR)):
            FBGR[i] = ''
        for i in range(len(FORM)):
            FORM[i] = ''

def debug_mode_switch(val):
    global dbg
    if val==0:
        dbg=False
    else:
        dbg=True

def refresh_format_params():
    global ml, mr
    if form_factor_menu!=0:
        ml = ' '*(int(form_factor_menu/5))
        mr = ' '+' '*(int(form_factor_menu/12))
    else:
        ml = ' '*(int((t_width/2)-(t_width/20)))
        mr = ' '*(int(t_width/20))

def calc_terminal_size():
    global t_width
    size=str(os.get_terminal_size())
    cut_left=size.find('columns=')
    cut_right=size.find(', ')
    t_width = int(size[cut_left+8:cut_right])

def draw_table(array, size = t_width, offset = 0, factor = 0.8, title='Highlights', COLH = FBGR[13], COL1 = FBGR[2], COL2 = FBGR[3]):
    
    #Größen zum Interieren
    crange = range(len(array[0]))
    lrange = range(len(array))
    
    linesize = int(size*factor)

    #Verkleinerung bis zu einer glatt teilbaren Tabellengröße
    while True:
        if linesize%len(array[0])==0:
            break
        else:
            if linesize>30:
                linesize-=1
            else:
                break
    
    #Tabelle (roh)
    tbl = ''
    
    if linesize<30:
        tbl+='\n'+'\t'*offset+FCOL[9]+'warning: terminal-window is very small!'+FEND+'\n'
    
    #Breite der Einträge (d.h. Elemente einer Zeile)
    entry_width = int(linesize/len(crange))
    
    #Was bleibt übrig? (sollte stets 0 sein wg. Schrumpfung von t_width auf glatt teilbares linesize!)
    if linesize-(entry_width*len(crange))>0:
        rest = linesize-(entry_width*len(crange))
    else:
        rest = 0
    
    #Debug-Informationen
    if dbg==True:
        dbg_txt=''
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'--Debug-Hints--'+FEND+'\n'
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'t_width: '+'\t\t'+str(t_width)+FCOL[0]+'\t<=> real terminal size\n'+FEND
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'array: '+'\t\t\t'+str(len(lrange))+'x'+str(len(crange))+FCOL[0]+'\t<=> array structure\n'+FEND
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'linesize: '+'\t\t'+str(linesize)+FCOL[0]+'\t<=> used table size\n'+FEND
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'entry_width: '+'\t\t'+str(entry_width)+FCOL[0]+'\t<=> size per table entry\n'+FEND
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'scaling fac.: '+'\t\t'+str(factor)+FCOL[0]+'\t<=> scales targeted size\n'+FEND
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'tab. offset: '+'\t\t'+str(offset)+FCOL[0]+'\n'+FEND
        
        print(dbg_txt)
    
    #Tabellenbau
    for i in lrange:       
        if i==0:
            #Kopfzeile mit Überschrift
            tbl+=ml+'\t'*offset+COLH+FORM[0]+'{:^{pos}}'.format('---'+title[-linesize+3:linesize-3]+'---', pos=linesize)+FEND+'\n'
        newl = ''
        #Abarbeitung der Elemente in einer Zeile
        for j in crange:
            #Differenzierung in gerade/ungerade für wechselnde Farben zwischen Spalten
            if j%2==0:
                newl+='{:<{pos}}'.format(COL2+FCOL[1]+(array[i][j]+' '*(entry_width-len(array[i][j])))[:entry_width], pos=entry_width)
            else:
                newl+='{:<{pos}}'.format(COL1+FCOL[1]+(array[i][j]+' '*(entry_width-len(array[i][j])))[:entry_width], pos=entry_width)
        newl+=' '*rest+FEND
        tbl+=ml+'\t'*offset+'{txt:<{pos}}'.format(txt=newl, pos=linesize)+'\n'      
        
    return tbl
  
def avail_pkg(id):
    global pkg_info
    avl = len(cfg_profiles[id])
    full = avl
    miss = 0
    err = 0
    for p in cfg_profiles[id]:
        loadprogress()
        res = shell('{} find '.format(spack_xpth)+p[0][3])
        if res.find('Kommando nicht gefunden')>-1 or res.find('command not found')>-1:
            pkg_info[id][0] = FCOL[9]+'?/? (command not available!)'+FEND
            pkg_info[id][1] = FCOL[9]+'?'+FEND
            pkg_info[id][2] = FCOL[9]+'?'+FEND
            error_log('Informationen zum Verfügbarkeitsgrad der packages konnten nicht geholt werden, ggf. ist der Pfad zu spack falsch!\n{}'.format(spack_xpth))
        else:
            if str(res[0:14])=='==> No package':
                avl-=1
                miss+=1
            elif str(res[0:9])=='==> Error':
                avl-=1
                err+=1
    if avl==full:
        pkg_info[id][0] = FCOL[5]+str(avl)+FEND+'/'+str(full)+FORM[1]+' packages pot. av. '+FEND
    elif avl!=0:
        pkg_info[id][0] = FCOL[7]+str(avl)+FEND+'/'+str(full)+FORM[1]+' packages pot. av. '+FEND
    else:
        pkg_info[id][0] = FCOL[9]+str(avl)+FEND+'/'+str(full)+FORM[1]+' packages pot. av. '+FEND
    if miss>0:
        pkg_info[id][1] = '('+FCOL[7]+str(miss)+FEND+FORM[1]+' misses, '+FEND
    else:
        pkg_info[id][1] = '('+str(miss)+FORM[1]+' misses, '+FEND
    if err>0:
        pkg_info[id][2] = FCOL[9]+str(err)+FEND+FORM[1]+' errors'+FEND+')'
    else:
        pkg_info[id][2] = str(err)+FORM[1]+' errors'+FEND+')'

#Prüft ob ein Pfad existiert 
def check_path(pth):
    eval_path=shell('find '+pth)
    if len(pth) > 0 and eval_path.find('find:')==-1:       
        return True
    else:       
        return False
        
"""
Skriptbau-Funktionen
"""

#Default Argument <=> wir wollen alle Profile laufen lassen
def bench_run(bench_id, farg = 'all', extra_args = ''):
    #Vorschlag: Überarbeitung der Menü-Ausgabe, vll über eine globale String-Variable, das würde simultane Menü und Flag-Nutzung erlauben
    #z.B. global menutxt und in der menu-Fkt das printen immer über diese globale Variable
    #Falls das überhaupt nötig ist...
    menutxt, tag = '', tag_id_switcher(bench_id)    
    pth = get_cfg_path(tag)
    
    """ 
    >>>>>    ÜBERHOLT (läd nur noch nötige profile) <<<<
    >>>>>    ACHTUNG! MENÜ EVTL: ANPASSEN!   <<<<<<<<<<
    #Aufarbeitung des Argumentstrings
    if farg == 'all':
        names = get_cfg_names(pth, tag)
    else:
        names = farg_to_list(farg, tag)
    """
    #Die Liste der Namen der verfügbaren Profile
    #avail_names = get_cfg_names(pth, tag)
    #Die Liste der Namen der nicht verfügbaren Profile
    #unavail_names = []
    
    #Die Liste der geladenen Profile aus dem Config-Ordner
    selected_profiles = cfg_profiles[bench_id].copy()   
    """
    #Namen von verfügbaren aber nicht ausgewählten Profilnamen
    unselected_names = []

    #Indizes der zu entfernenden Profile
    dlist=[]
    
    for i in range(len(selected_profiles)):
        #Der Profilname ist nicht in der Liste der zu nutzenden Profile dabei...
        if selected_profiles[i][0][0] not in names:
            #...also vormerken zum Entfernen
            dlist.append(i)
            unselected_names.append(selected_profiles[i][0][0])
    dlist.reverse()
    
    #Entfernung der unerwünschten Profile
    for i in dlist:
        del selected_profiles[i]
    
    for name in names:
        if name not in avail_names:
            error_log('Profil: '+name+' war nicht verfügbar!')
            menutxt+='Profil: '+name+' war nicht verfügbar!'+'\n'
            unavail_names.append(name)
    for profile in selected_profiles:
        menutxt+='Ausgewählt: '+profile[0][0]+'\n'
    """   
    
    #Skriptbau, ggf. mit zusätzlichen Argumenten
    if extra_args!='':
        skript=build_batch(selected_profiles, bench_id, extra_args)
        menutxt+='...an srun würde übergeben werden: \n'+skript
    else:
        skript=build_batch(selected_profiles, bench_id)
        menutxt+='...an srun würde übergeben werden: \n'+skript    
    
    #shell('sbatch '+skript) <--- sollte umgebaut werden sobald der Rest stimmt
    return FCOL[13]+skript+FEND

#Hiermit soll das Skript gebaut werden 
def build_batch(selected_profiles, bench_id, extra_args = ''):    
    first_job=True
    tag = tag_id_switcher(bench_id)
    
    tstamp = time.strftime("%d-%m-%Y_%H:%M:%S", time.localtime())
    
    #Namen der Auftragsordner
    run_dir='{}/{}_[{}]_[run]/'.format(project_pth,tag,tstamp)
    res_dir='{}/{}_[{}]_[results]/'.format(project_pth,tag,tstamp)
    
    if os.path.isdir(run_dir[:-1])==False:     
        shell('mkdir -p '+run_dir[:-1])
    if os.path.isdir(res_dir[:-1])==False:     
        shell('mkdir -p '+res_dir[:-1])
    
    #Bauen des Batch-Skripts, anhand der Parameter aus der allgemeinen Config
    batchtxt=write_slurm_params(cfg_profiles[0][0], 'batchskript')
    batchtxt+='#SBATCH --job-name='+tag+'_run'+'['+tstamp+']'+'\n'
    batchtxt+='#SBATCH --output='+run_dir+tag+'_run'+'['+tstamp+']'+'.out'+'\n'
    batchtxt+='#SBATCH --error='+run_dir+tag+'_run'+'['+tstamp+']'+'.err'+'\n\n'  
    
    #Einzelne Jobskripte je Profil
    for profile in selected_profiles:    
        if bench_id == hpl_id:
            #Anpassung z.B. für den Fall: versch. Profile benutzen gleiches hpl package mit untersch. HPL.dat Parametern
            #print(profile[0][2])
            if profile[0][2]!='Kein Pfad gefunden!':
                batchtxt+='python3 '+hpl_handler_xpth+' '+profile[0][1]+' '+profile[0][2]+'/\n'
            else:
                #Wenn der Ort der Binary nicht klar ist, soll auch kein Jobscript gebaut werden...
                continue
        
        #Der erste Job kann direkt loslegen, die folgenden müssen auf den Abschluss der Vorgänger warten
        if first_job:
            first_job=False
            batchtxt+='id'+str(selected_profiles.index(profile))+'=$(sbatch '            
        else:
            batchtxt+='id'+str(selected_profiles.index(profile))+'=$(sbatch --dependency=afterany:${id'+str(selected_profiles.index(profile)-1)+'##* } '
        
        if extra_args!='':
            batchtxt+=build_job(profile, bench_id, run_dir, res_dir, extra_args)+')\n'
        elif len(extra_args)==0:
            batchtxt+=build_job(profile, bench_id, run_dir, res_dir)+')\n'        
    
    batchtxt+='source {}/share/spack/setup-env.sh\n'.format(spack_xpth[:-9])
    batchtxt+='spack load python '+find_matplot_python_hash()+'\n'
    batchtxt+='sbatch --dependency=afterany:${id'+str(len(selected_profiles)-1)+'##* } ' + build_plot(tstamp,tag_id_switcher(bench_id),run_dir)
    #batchtxt+='sbatch --dependency=afterany:${id'+str(len(selected_profiles)-1)+'##* } python3 plot.py '+tstamp+' '+tag_id_switcher(bench_id) 
    
    
    #Niederschreiben des Skripts & Rückgabe des entspr. Pfads hin
    file_w(run_dir+'{}.sh'.format(tag+'_run_batchscript'),batchtxt,'a')
    shell('chmod +x '+run_dir+'{}.sh'.format(tag+'_run_batchscript'))    
    return run_dir+'{}.sh'.format(tag+'_run_batchscript')    

def build_job(profile, bench_id, run_dir, res_dir, extra_args = ''):

    #Manche Dinge werden direkt ermittelt...
    if bench_id != osu_id:
        bin_path = find_binary(profile, bench_id)        
    else:
        bin_path = ''
    #Im vierten Config-Block eines Profils steht potentiell ein händisch gebautes Skript     
    if len(profile[4])==0:
        jobtxt=write_slurm_params(profile, 'jobskript')
        #Jobname (<=> Profilname)
        jobtxt+='#SBATCH --job-name={}\n'.format(profile[0][0][:-4])
        #Ziel für Output (sollte in (...)[results] landen)
        if profile[3][10]=='':
            jobtxt+='#SBATCH --output={}\n'.format(res_dir+'/'+profile[0][0][:-4]+'.out')
        #Ziel für Fehler (sollte in (...)[results] landen)
        if profile[3][11]=='':
            jobtxt+='#SBATCH --error={}\n'.format(res_dir+'/'+profile[0][0][:-4]+'.err')
        jobtxt+='\n'
        #Sourcen von spack   
        jobtxt+='source {}/share/spack/setup-env.sh\n'.format(spack_xpth[:-9])
        #Laden der passenden Umgebung
        jobtxt+= 'spack load {}\n'.format(profile[0][3])   
        jobtxt+='\n'
        #Skriptzeile in der eine Binary ausgeführt wird
        jobtxt+=execute_line(bench_id, bin_path, profile[3][1], profile[3][2], extra_args, res_dir+profile[0][0][:-4]+'.out')
        #TODO: Entladen von Modulen, nötig? Das ist ja ein abgeschlossenes Jobscript...
        #jobtxt+= 'spack unload {}\n'.format(profile[0][3])
    else:
        jobtxt=''
        for i in range(len(profile[4])):
            jobtxt+=profile[4][i]
    
    #Niederschreiben des Skripts & Rückgabe des entspr. Pfads hin
    if os.path.isdir(run_dir[:-1])==True:
        file_w(run_dir+'{}.sh'.format(profile[0][0][:-4]),jobtxt,'a')
        shell('chmod +x '+run_dir+'{}.sh'.format(profile[0][0][:-4]))
    return run_dir+'{}.sh'.format(profile[0][0][:-4])

def execute_line(bench_id, bin_path, node_count, proc_count, extra_args, output):

    txt = ''    
    if bench_id==hpl_id:
        txt+='cd {}'.format(bin_path)+'\n' #<--- TODO: schöner lösen?
        txt+='mpirun -np {pcount} {bpath}xhpl'.format(pcount = proc_count, bpath = bin_path,out=output)        
    elif bench_id==osu_id:
        txt+='mpirun -n {ncount} osu_{exargs}'.format(ncount=node_count,exargs=extra_args,out=output)
    return txt

def build_plot(tstamp, bench,run_dir):
    jobtxt=write_slurm_params(cfg_profiles[0][0], 'plotskript')
    jobtxt+='#SBATCH --job-name='+bench+'_plot\n' 
    jobtxt+='#SBATCH --error='+run_dir+bench+'_plot.err\n\n'
    jobtxt+='#SBATCH --output='+run_dir+'plot.out'+'\n'
    jobtxt+='#SBATCH --error='+run_dir+'plot.err'+'\n\n'     
    jobtxt+= 'python3 {}/plot.py '.format(loc)+tstamp+' '+bench
    
    #Niederschreiben des Skripts & Rückgabe des entspr. Pfads hin
    if os.path.isdir(run_dir[:-1])==True:
        file_w(run_dir+bench+'{}.sh'.format('_plotskript'),jobtxt,'a')
        shell('chmod +x '+run_dir+bench+'{}.sh'.format('_plotskript'))
    return run_dir+bench+'{}.sh'.format('_plotskript')

"""
Installation
"""
""
def view_installed_specs(name=0):
    try:
        if name==0:
            return shell('{} find --show-full-compiler'.format(spack_xpth))
        else:
            print('{} find --show-full-compiler '.format(spack_xpth)+name)
            return shell('{} find --show-full-compiler '.format(spack_xpth)+name)  
    
    except Exception as exc:
        error_log(' {} [Exception]'.format(type(exc).__name__)+'\nspec:'+str(name))

#Prüft Specausdruck auf grobe Syntaxfehler
def check_expr_syn(expr):
    expr_list=['@%','%@','^%','%^','^@','@^']
    """
    Hinweis bzgl. regulärem Ausdruck:
    {min,max} min/max vorkommen der vorrangegangenen Zeichenkette 
    \w Symbolmenge: [a-z, A-Z, 0-9, _]            
    * Vorangegangene Zeichenkette kommt beliebig oft vor (inkl. 0 mal)
    (...) Gruppe -> praktisch eine Zeichenkette
    \. Punktsymbol, da einfach nur . für einzelnes Zeichen steht            
    """
    if re.search(r'@{1,1}(\w*\.*[%]{0,0}\w*)*@{1,}',expr):
        return False
    for _ in expr_list:
        r=expr.find(_)        
        if r != -1:
            print('Syntaxfehler an Position: '+str(r))
            return False
    return True


#Schreibt Script zum installieren der specs 
#Übergibt alle benötigen Argumente an Install.py
def install_spec(expr):  
    #Slurmparameter 
    meta=cfg_profiles[0][0][2][0]+'#'+cfg_profiles[0][0][2][1]+'#'+cfg_profiles[0][0][2][2]+'#'+cfg_profiles[0][0][2][3]+'#'+spack_xpth[:-9]   
    expr_=''
    timer=0
    #String aller Specs
    for e in expr:
        expr_+=e+'#'            
   
    #Erstellt Batchscript zum Starten der Installation
    if (os.path.isfile('start_install.sh'))==False: 
            shell('touch {}/start_install.sh'.format(loc))
            shell('chmod +x {}/start_install.sh'.format(loc))
            file_w('{}/start_install.sh'.format(loc),'','a')
    else:
        #Clear install.sh
        shell('echo a > {}/start_install.sh'.format(loc))   
    
    #Slurmparameter für die Installation
    slurm='#!/bin/bash\n' \
    +'#SBATCH --nodes=1\n' \
    +'#SBATCH --partition='+cfg_profiles[0][0][2][0]+'\n' \
    +'source {}/share/spack/setup-env.sh\n\n'.format(spack_xpth[:-9])+'\n' \
    +'python3 {}/install.py {} {}'.format(loc,meta,expr_[:len(expr_)-1])   
    
    file_w('{}/start_install.sh'.format(loc),slurm,0)
    shell('chmod +x {}/start_install.sh'.format(loc))
    shell('sbatch {}/start_install.sh'.format(loc))
    shell('rm {}/start_install.sh'.format(loc))
    
    #Wartet bis install.sh erstellt und befüllt wurde
    while exists('{}/install.sh'.format(loc))==False or os.stat('{}/install.sh'.format(loc)).st_size==0: 
        time.sleep(5)
        timer+=1
        if timer > 120:
            print('timeout error')
            return error_log('Installationsfehler!')
    shell('chmod +x {}/install.sh'.format(loc))
    print(shell('sbatch {}/install.sh'.format(loc)))
    
    
    

"""
Menüfunktionen
"""

#Hauptmenü
def print_menu(txt = ''):
    global menutxt, get_info
    calc_terminal_size()
    refresh_format_params()
    clear()
    print(FBGR[11]+FORM[0]+'{:^{pos}}'.format('Main Menu', pos=t_width))
    print(FEND+ml+'(0)'+mr+' Exit')
    print(ml+'(1)'+mr+' Options')
    print(ml+'(2)'+mr+' Info')
    if (refresh_intervall!=0 and ((time.time()-print_menu.updatetime)>refresh_intervall or print_menu.updatetime==0)) or get_info:
        print_menu.updatetime=time.time()
        opt_lines=''
        try:         
            for id in range(len(bench_id_list)):
                if id==misc_id:
                    continue
                avail_pkg(id)
                get_info = False
                opt_lines+=ml+'({})'.format(id+2)+mr+' {} ... '.format(tag_id_switcher(id)).upper()+pkg_info[id][0]+pkg_info[id][1]+pkg_info[id][2]+'\n'
            print(opt_lines[:-1])
        except Exception as exc:     
            error_log(' {} [Exception]'.format(type(exc).__name__))
            for id in range(len(bench_id_list)):
                if id==misc_id:
                    continue
                print(ml+'({})'.format(id+2)+mr+' {}'.format(tag_id_switcher(id)).upper()+'... package information refresh failed')               
    else:
        for id in range(len(bench_id_list)):
            if id==misc_id:
                continue
            if pkg_info[id][0]!='empty':
                print(ml+'({})'.format(id+2)+mr+' {} ... '.format(tag_id_switcher(id)).upper()+pkg_info[id][0]+pkg_info[id][1]+pkg_info[id][2]+' {}s ago'.format(int(time.time()-print_menu.updatetime)))
            else:
                print(ml+'({})'.format(id+2)+mr+' {} '.format(tag_id_switcher(id)).upper())           
    print(ml+'({})'.format(len(bench_id_list)+2)+mr+' Fehleranzeige '+check_err_stack())
    print(' ')
    print(menutxt+str(txt))
    #angesammelte Nachrichten leeren...
    menutxt=''
print_menu.updatetime=0

def menu():
    save_times()
    global errorstack, get_info
 
    #Damit man die Optionen sehen kann
    print_menu(initm)
    
    #Interaktivität mit Nutzereingabe
    while True:
        opt = input_format()

        if opt == '0' or opt == 'q':
            clear()
            #SystemExit(0)
            break
        elif opt == '1' or opt == 'Options':       
            options_menu()
        elif opt == '2' or opt == 'Info':
            #Könnte man noch füllen... z.B. mit highlight Werten etc.
            info='\n\n'
            info+=ml+FCOL[0]+'subshell-use \t\t\t<=> $>>cmd<< \t\t(Debugging)'+FEND+'\n'
            info+=ml+FCOL[0]+'code eval. \t\t\t<=> code:>>code<< \t(Debugging)'+FEND+'\n'
            info+=ml+FCOL[0]+'form-factor equals zero \t<=> center aligned text'+FEND+'\n'
            info+='\n\n'
            
            info+=draw_table(best_list, t_width, 0, 0.5)
                
            #Wir wollen auf jeden Fall auch die package Infos, selbst wenn refresh aus oder zu früh ist
            get_info = True
            print_menu(info)
        elif opt.isdigit() and int(opt)>2 and int(opt)<=len(bench_id_list)+1:
            #-2 ist der Offset der die Positionen 'Option' und 'Info' ausgleicht
            func = globals()['{}_menu'.format(tag_id_switcher(int(opt)-2))]
            func()    
        elif opt == str(len(bench_id_list)+2):
            elist = ''
            while len(errorstack)!=0:
                elist = elist + '\n' + errorstack.pop()
            print_menu('Zuletzt aufgetretene Fehler... {}'.format(elist))
        elif opt[0:5] == 'code:':
            r = code_eval(opt[5:])
            print_menu(r)
        elif opt[0] == '$':
            r = str(shell(opt[1:]))
            print_menu(FBGR[14]+'stdout:'+FEND+'\n'+r)
        else:
            print_menu(FORM[1]+'Eingabe ungültig: Bitte eine Ganzzahl, z.B. 1'+FEND)   

#Options-Menü
def print_options_menu(txt = ''):
    global menutxt
    calc_terminal_size()
    refresh_format_params()
    clear()
    print(FBGR[11]+FORM[0]+'{:^{pos}}'.format('Options', pos=t_width))
    print(FEND+ml+'(0)'+mr+' return to main menu')
    print(ml+'(1)'+mr+' change form-factor')
    print(ml+'(2)'+mr+' change refresh-intervall')
    print(ml+'(3)'+mr+' dis-/enable colour & format')
    print(ml+'(4)'+mr+' dis-/enable debug mode')
    print(ml+'(5)'+mr+' show bench profiles')
    print(ml+'(6)'+mr+' clean run-time variables (mem.txt)')
    print(ml+'(7)'+mr+' clean error-log (log.txt)')
    print(ml+'(8)'+mr+' clean projects')
    print(' ')
    print(menutxt+str(txt))
    #angesammelte Nachrichten leeren...
    menutxt=''

def options_menu():    
    print_options_menu()
    global menutxt, colour_support, refresh_intervall, form_factor_menu
    while True:
        opt = input_format()
        if opt == '0' or opt == 'q':
            clear()
            print_menu()
            break
        elif opt == '1' or opt == 'form-factor':
            print_options_menu('...current form-factor: {}\n...please insert the new value'.format(form_factor_menu))
            form_factor_menu = int(input_format())
            file_w('{}/mem.txt'.format(loc),'form_factor_menu\t\t\t[{}]'.format(str(form_factor_menu)),1)
            calc_terminal_size()
            refresh_format_params()
            print_options_menu('done!')
        elif opt == '2' or opt == 'refresh-intervall':
            if refresh_intervall!=0:
                print_options_menu('...current refresh-intervall is {}\n...please insert the new value'.format(refresh_intervall))
            else:
                print_options_menu('...refresh-intervall is 0: information about package availability won\'t be evaluated!\n...please insert the new value')
            refresh_intervall = int(input_format())
            file_w('{}/mem.txt'.format(loc),'refresh_intervall\t\t\t[{}]'.format(str(refresh_intervall)),2)
            print_options_menu('done!')
        elif opt == '3' or opt == 'colour':
            if colour_support==1:
                colour_support = 0
                file_w('{}/mem.txt'.format(loc),'colour_support\t\t\t[{}]'.format(str(colour_support)),3)
                color_check()
                print_options_menu('done!'+FORM[1]+' ...colour & format off'+FEND)
            elif colour_support==0:
                colour_support = 1
                file_w('{}/mem.txt'.format(loc),'colour_support\t\t\t[{}]'.format(str(colour_support)),3)
                color_check()
                print_options_menu('done!'+FORM[1]+' ...colour & format on'+FEND)
            else:
                print_options_menu(FCOL[9]+'invalid value! (error)'+FEND+'\n colour_support has to be either 0 or 1!')
        elif opt == '4' or opt == 'debug':
            if dbg==True:
                debug_mode_switch(0)
                file_w('{}/mem.txt'.format(loc),'debug_mode\t\t\t[0]',4)
                print_options_menu('done!'+FORM[1]+' ...debug mode off'+FEND)
            else:
                debug_mode_switch(1)
                file_w('{}/mem.txt'.format(loc),'debug_mode\t\t\t[1]',4)
                print_options_menu('done!'+FORM[1]+' ...debug mode on'+FEND)
        elif opt == '5' or opt == 'show':
            i = 0
            txt=ml+FCOL[13]+FORM[0]+'which bench do you wish to inspect?'+FEND
            txt+='\n\n'+ml+FBGR[0]+'possible choices:'+FEND+'\n'+ml
            left_size=t_width-len(ml)
            for id in bench_id_list:
                if left_size<len(str(id)+' ('+tag_id_switcher(id)+')'+mr):
                    left_size-=len(ml)
                    txt+='\n'+ml
                txt+=FORM[0]+str(id)+' ('+tag_id_switcher(id)+')'+FEND+mr
                left_size-=len(str(id)+' ('+tag_id_switcher(id)+')'+mr)
            print_options_menu(txt)
            print_options_menu(config_out(int(input_format())))
        elif opt == '6' or opt == 'clean mem':
            print_options_menu(clean('mem'))
        elif opt == '7' or opt == 'clean log':
            print_options_menu(clean('log'))
        elif opt == '8' or opt == 'clean projects':
            print_options_menu(clean('projects'))
        else:
            print_hpl_menu(FORM[1]+'Eingabe ungültig: Bitte eine Ganzzahl zw. 0-6, z.B. 1'+FEND)

#OSU-Menü
def print_osu_menu(txt = ''):
    global menutxt
    calc_terminal_size()
    refresh_format_params()
    clear()
    print(FBGR[11]+FORM[0]+'{:^{pos}}'.format('OSU', pos=t_width))
    print(FEND+ml+'(0)'+mr+' return to main menu')
    print(ml+'(1)'+mr+' run')
    print(ml+'(2)'+mr+' view installed packages')
    print(ml+'(3)'+mr+' install packages')
    print(' ')
    print(menutxt+str(txt))
    #angesammelte Nachrichten leeren...
    menutxt=''

def osu_menu():    
    print_osu_menu()
        
    while True:
        opt = input_format()
        if opt == '0' or opt == 'q':
            clear()
            print_menu()
            break
        elif opt == '1' or opt == 'run':
            print('Info: Noch nicht implementiert...')
            #Funktioniert sicher anders als bei HPL, das wäre die dortige Variante...
            #Formatierungskonzept aber bitte kopieren
        elif opt == '2' or opt == 'view':
            print_osu_menu(view_installed_specs(tag_id_switcher(osu_id)))
        elif opt == '3'or opt == 'install':
            print_osu_menu('Welche specs sollen installiert werden?\n'+install_spec(str(input_format())))
        else:
            print_osu_menu(FORM[1]+'Eingabe ungültig: Bitte eine Ganzzahl zw. 0-3, z.B. 1'+FEND)

#HPL-Menü
def print_hpl_menu(txt = ''):
    global menutxt
    calc_terminal_size()
    refresh_format_params()
    clear()
    print(FBGR[11]+FORM[0]+'{:^{pos}}'.format('HPL', pos=t_width))
    print(FEND+ml+'(0)'+mr+' return to main menu')
    print(ml+'(1)'+mr+' run')
    print(ml+'(2)'+mr+' view installed packages')
    print(ml+'(3)'+mr+' install packages')
    print(' ')
    print(menutxt+str(txt))
    #angesammelte Nachrichten leeren...
    menutxt=''

def hpl_menu():    
    print_hpl_menu()
        
    while True:
        opt = input_format()
        if opt == '0' or opt == 'q':
            clear()
            print_menu()
            break
        elif opt == '1' or opt == 'run':
            i = 0
            txt=ml+FCOL[13]+'which profiles do you wish to run?'+FEND
            txt+=ml+FCOL[0]+'\n'+'how to reference profiles: '+ml+'\ne.g. hpl_cfg_test.txt => test \n'+ml+'e.g. hpl_cfg_1.txt,hpl_cfg_2.txt,...,hpl_cfg_5.txt => 1-5 \n'+ml+'e.g. valid input: 1-3,test,9\n'+FEND
            txt+='\n\n'+ml+FBGR[0]+'found profiles:'+FEND+'\n'+ml
            left_size=t_width-len(ml)
            for name in get_cfg_names(bench_pths[hpl_id],tag_id_switcher(hpl_id)):
                if left_size<len(name+mr):
                    left_size-=len(ml)
                    txt+='\n'+ml
                txt+=FORM[0]+name+FEND+mr
                left_size-=len(name+mr)
            print_hpl_menu(txt)
            print_hpl_menu(bench_run(hpl_id, input_format().replace(' ','')))                         
        elif opt == '2' or opt == 'view':
            print_hpl_menu(view_installed_specs(tag_id_switcher(hpl_id)))
        elif opt == '3'or opt == 'install':
            print_hpl_menu('Welche specs sollen installiert werden?\n'+install_spec(str(input_format())))
        else:
            print_hpl_menu(FORM[1]+'Eingabe ungültig: Bitte eine Ganzzahl zw. 0-3, z.B. 1'+FEND)


    
"""
Allgemeine I/O Funktionen
"""

#Lesefunktion: In welche Datei? An welche Position?  
def file_r(name, pos):  
    try:     
        with open(name, 'r') as f:      
            stringlist = f.readlines()
            return stringlist[int(pos)]
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__)+'\nfile_r wurde aufgerufen aus: '+str(inspect.stack()[1][3])+'\nZieldatei: '+name+'\nPosition: '+str(pos))        

def count_line(name):
     with open (name, 'r') as f:
        num_lines = sum(1 for line in f if line.rstrip())
        return num_lines

#Schreibfunktion: In welche Datei? Welchen Text? An welche Position? bzw. 'a' für anhängen/append
def file_w(name, txt, pos):
    try:
        if(pos!='a'):
            #Wir holen uns eine Stringliste...
            with open(name, 'r') as f:      
                stringlist = f.readlines()
            #...ändern den passenden Index ab...
            org_size = len(stringlist)    
            while len(stringlist)<=pos:
                stringlist.append('\n')
                
            stringlist[int(pos)]=txt+'\n'
            
            with open(name, 'w') as f:
                f.writelines(stringlist)
        else:
            with open(name, "a") as f:     
                f.write(txt+'\n')
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__)+'\nfile_w wurde aufgerufen aus: '+str(inspect.stack()[1][3])+'\nZieldatei: '+name+'\nPosition: '+str(pos))

def get_mem_digit(pos):
    r = str(file_r('{}/mem.txt'.format(loc), pos))
    r = r[r.find('[')+1:r.find(']')]
    if len(r)>0:
        return int(r)
    else:
        return 0


"""
    try:     
        
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__)) 
"""

#Startpunkt
clear()
cl_arg()
