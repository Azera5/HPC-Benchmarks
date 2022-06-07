import os
import os.path
import subprocess
import datetime
import inspect
import time
import math
import fnmatch
import re
import argparse
from argparse import RawTextHelpFormatter



"""
Potentielle Usereingaben
"""
hpl_cfg_pth = ''
osu_cfg_pth = ''
misc_cfg_pth= ''
spack_binary = ''
hpl_handler_xpth = 'hpl_dat_handler'


"""
Hilfsvariablen
"""
#Anzahl unterstützter Benchmarks (HPL, OSU, ...)
benchcount = 2
misc_id = 0
hpl_id = 1
osu_id = 2

#Sammelt kürzliche Fehlermeldungen
errorstack = []
#Trägt Informationen des Config-Ordners; Ersteintrag für Metadaten
#Index: [Benchmark-id][Profil-Nr.][Abschnitt][Zeile im Abschnitt]
cfg_profiles = [[],[],[],[]]
#Initialnachricht
initm = ''


"""
Command-Line-Parameter
"""
def cl_arg():
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)    
    parser.add_argument('-i','--install',nargs='+',type=str,help=''+
    '<Benchmark> <cfg>,<cfg>,...,<cfg>\n'+
    '     z.B.: -i hpl 1,3-4,Test1\n'+
    'all: Installiert alle Benchmarks/cfg\n'+
    '     z.B.: -i all\n\n'+
    '           -i osu all\n\n')
    
    parser.add_argument('-r','--run',nargs='+',type=str,help=''+   
    'hpl <cfg>,<cfg>,...,<cfg>\n'+     
    '     z.B.: -r hpl 1,3-4,Test1\n' +
    '           -r hpl all <=> -r hpl\n\n' +
    'osu <Test> <cfg>,<cfg>,...,<cfg>\n'+
    '     Tests:{latency, bw, bcast, barrier, allreduce}\n'+
    '     z.B.: -r osu latency 1,3-4,Test1\n'+
    '           -r osu latency all <=> -r osu latency\n') 
 
    print('laden ...')
    find_paths()
    check_data()
    check_dirs()
    get_cfg('osu')
    get_cfg('hpl') 
    get_cfg('misc')
    #Hilfestellung
    config_out(hpl_id)
   
    args= parser.parse_args()
    
    #Install Benchmarks
    if args.install:        
        expr=[]
        #Alle Profile aller Benchmarks werden installiert
        if args.install[0]=='all':
            expr=get_all_specs('hpl')+get_all_specs('osu')
        
        #Nur bestimmte Benchmarks werden installiert
        else:           
            #Nur bestimmte Profile werden installiert
            if len(args.install)>2 and args.install[1]!= 'all':
                names=farg_to_list(args.install[1],args.install[0])
                for _ in names:                   
                    expr=get_all_specs(args.install[0],names)
            #Alle Profile werden installiert
            else:
                expr=get_all_specs(args.install[0])
                
        install_spec(expr)
    
    #Run Benchmarks
    if args.run:
        if len(args.run)<2 or (len(args.run)<3 and args.run[0]=='osu'):
            print('Zu wenig Argumente:\n'+
            'HPL (2): -r [hpl] [cfg]\n'+
            'OSU (3): -r [osu] [test] [cfg]')
        elif args.run[0]=='hpl':
            print('#TODO hpl-run')
            #hpl_run(args.run[1])
        elif args.run[0]=='osu':
            print('#TODO osu-run')
            #osu_run(args.run[1],args.run[2])           
    
     
    #Start via Menu   
    if not args.install and not args.run:
        menu()



"""
Wichtige Vorlauf-Funktionen
"""

#Ermittelt Pfade relevanter Verzeichnisse und Binaries, wenn nichts spezifiziert wurde
def find_paths():
    global hpl_cfg_pth, osu_cfg_pth, spack_binary,misc_cfg_pth  
    #An der Stelle, an der das Programm ausgeführt wird, sollten auch die configs sein
    if hpl_cfg_pth=='':
        hpl_cfg_pth = str(shell('pwd')+'/config/hpl/').replace('\n','').strip()
    if osu_cfg_pth=='':
        osu_cfg_pth = str(shell('pwd')+'/config/osu/').replace('\n','').strip()
    if misc_cfg_pth=='':
        misc_cfg_pth = str(shell('pwd')+'/config/').replace('\n','').strip()    
    if spack_binary=='':
        r_list = str(shell('find ~ -executable -name spack -path \'*/spack/bin/*\'')).replace('\n',' ').split()
        #Wir nehmen die erstbeste spack Binary, wenn nichts per Hand spezifiziert wurde
        spack_binary = r_list[0].strip()

def check_data():
    global cfg_profiles
    #Für jeden Bench eine Liste, in jeder dieser Listen eine Liste pro Profil

    #Struktur: cfg_profiles[Benchmarktyp][Profil][Block][Zeile]
    for _ in range(0, len(get_cfg_names(hpl_cfg_pth,'hpl'))):
        #Für jedes Profil existieren verschiedene Blöcke an Informationen (z.B. über SLURM-Einstellungen)
        cfg_profiles[hpl_id].append([[]]*4)
    for _ in range(0, len(get_cfg_names(osu_cfg_pth,'osu'))):
        #Für jedes Profil existieren verschiedene Blöcke (analog zu s. oben)
        cfg_profiles[osu_id].append([[]]*4)
    #Hinweis: ['test']*n <=> ['test, 'test', ...] vgl. ['test'*n] = ['testtesttest...']
    
    #Spezielle Angaben z.B. welche Partition/Nodes usw. gelten für Installationsdienste etc.
    cfg_profiles[misc_id].append([[]]*4)

#Existieren überhaupt log.txt, config/hpl/, config/hpl/hpl_cfg_[d, 1, ..., n] etc.
def check_dirs():
    global initm
    #Hinweis: '/dir1/dir2/.../'[:-1] <=> '/dir1/dir2/...'
    if os.path.isfile('log.txt')==False:     
        shell('touch log.txt')
        initm = initm+'errorlog erstellt ...\n'
    if os.path.isdir(hpl_cfg_pth[:-1])==False:     
        shell('mkdir -p '+hpl_cfg_pth[:-1])
        initm = initm+'Config-Verzeichnis für HPL erstellt ...\n'
        #Hier sollte noch eine Funktion sinnvolle Werte reinschreiben! <---TODO
    if os.path.isdir(osu_cfg_pth[:-1])==False:     
        shell('mkdir -p '+osu_cfg_pth[:-1])
        initm = initm+'Config-Verzeichnis für OSU erstellt ...\n'
        #Hier sollte noch eine Funktion sinnvolle Werte reinschreiben! <---TODO
    if os.path.isfile(hpl_cfg_pth+'hpl_cfg_d.txt')==False:     
        shell('touch '+hpl_cfg_pth+'hpl_cfg_d.txt')
        initm = initm+'default Config für HPL: \'hpl_cfg_d.txt\' erstellt ...\n'

"""
#Liest die Profile aus den lokalen Configs aus
def get_cfg(bench):
    global cfg_profiles
    names = get_cfg_names(get_cfg_path(bench), bench)
    sublist = []
    spec_ = [] #Hilfsvariable zum Ermitteln des specs    
    id = tag_id_switcher(bench)    
    #l-te Configzeile (int), p für Profil (string)
    for p in names:
        abschnitt = 1
        line_=1        
        while file_r(get_cfg_path(bench)+p,line_):                        
            line = file_r(get_cfg_path(bench)+p,line_)
            line_+=1            
            if line.find('------')!=-1:
                if len(sublist)>0: 
                    cfg_profiles[id][names.index(p)][abschnitt] = sublist
                    if abschnitt==1 and len(spec_)>0:                        
                        spec = get_spec(spec_,bench)
                        spec_ = []
                    abschnitt+=1
                    sublist = []                    
                continue            
            else:
                if (id != misc_id or line[0:5]!='[Pfad'):
                    sublist.append(config_cut(line))
                if abschnitt==1 and id != misc_id:
                    spec_.append(line) #get_spec benötigt die ganze Zeile der config 
                    
        #Ersteintrag ist nur Platzhalter für Metadaten: Name, Configpfad, Zielpfad zu Binary&HPL.dat
        if len(sublist)>0:            
            cfg_profiles[id][names.index(p)][abschnitt]=sublist 
            sublist=[]
        if id != misc_id:
            cfg_profiles[id][names.index(p)][0] = [p, get_cfg_path(bench)+p, get_target_path(spec),spec]  
        print('...')  
"""
    
def get_cfg(bench):
    global cfg_profiles
    names = get_cfg_names(get_cfg_path(bench), bench)
    sublist, spec_ = [], []
    id = tag_id_switcher(bench)
    #Für jedes Profil...
    for p in names:
        abschnitt = 1
        txtfile = open(get_cfg_path(bench)+p, 'r')
        txtlist = txtfile.readlines()
        #...jede Zeile passend einsortieren!
        for ln in txtlist:
            #Eine Reguläre Zeile wird in der Subliste gesammelt
            if (ln.find('-----')==-1) and (ln.find('[Pfad')==-1):
                sublist.append(config_cut(ln))
                if abschnitt==1:
                    spec_.append(ln)
            #Eine Trennzeile löst die Eingliederung eines gefüllten Blocks aus
            elif (len(sublist)>0) and (ln.find('-----')>-1):
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
        print('...') 
        txtfile.close()

"""
Debug- & Hilfs-Funktionen
"""

#In welcher Funktion ist wann, welche Exception o.a. Unregelmäßigkeit aufgetreten?
def error_log(txt):
    global errorstack
    txt = str(inspect.stack()[1][3])+' [Funktion] '+str(datetime.datetime.now())+' [Zeitpunkt] '+txt+'\n'
    file_w('log.txt', txt, 'a')
    errorstack.append(txt)

#Prüft ob der Fehlerstack leer ist
def check_err_stack():
    if len(errorstack)!=0:
        return '...Einträge vorhanden'
    else:
        return ''

#Wertet einen Terminalbefehl aus
def shell(cmd):
    try:
        #Ausgabe soll nicht direkt auf's Terminal
        p = subprocess.run(str(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        if(p.returncode!=0):
            error_log('returncode der Eingabe \''+cmd+'\' war nicht null!')
        #.stdout liefert einen Binärstring desw. die Dekodierung
        return p.stdout.decode('UTF-8')
    except Exception as exc:
        error_log(' {} [Exception]'.format(type(exc).__name__)+'\nshell wurde aufgerufen aus: '+str(inspect.stack()[1][3]))

#Wertet einen Python-Ausdruck aus
def code_eval(expr):
    #Auskommentiert für volle Fehlermeldungen
    """
    try:
        return eval(expr)
    except Exception as exc:
        error_log(' {} [Exception]'.format(type(exc).__name__))
    """
    return eval(expr)

#Liefert für eine Configzeile "123.4.5   [Parameter x]" nur die Zahl
def config_cut(line):
    c = line.find("[")
    if(c!=-1):
        line = line[:c]
    return line.strip()


#Ein Art Prompt für den Nutzer
def input_format():
    print(' ')
    print('Eingabe: ', end='')
    return input()

def clear():
    os.system('clear')
    #print('\n\n\n---Debugprint---\n\n\n')

#Liefert Files, keine Verz.; Erwartet Pfade in der Form /dir1/dir2/.../
def get_names(pth):
    r = os.listdir(pth)
    for _ in r:
        if os.path.isdir(_)==True:
            r.remove(_)
    return r

#Liefert Textfiles eines bestimmten Typs (z.B. hpl_cfg_(...).txt)
def get_cfg_names(pth, type):
    if type == 'misc':
        return ['config.txt']
    else:
        return fnmatch.filter(get_names(pth), type+'_cfg_*.txt')


#Bekommt eine Liste bzgl. der Packages aus einer Config, liefert die package spec
def get_spec(cfg_list,bench):
    if bench is 'osu':
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
        s += 'Profil: '+p[0][0]+'\n'
        #Abschnitte der Profile
        for b in range(0,len(p)):
            s += '->Block: '+str(b)+'\n'
            #individuelle Lines des Blocks (=Strings) sind konkatenierbar
            for l in p[b]:
                if l=='':
                    s += 'leer'+'\n'
                else:
                    s += l+'\n'
    s += '\n-----------------------------\n'
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
    if bench is 'hpl':
        return hpl_cfg_pth
    if bench is 'osu':
        return osu_cfg_pth
    if bench is 'misc':
        return misc_cfg_pth
    else:
        return -1 

#Zielpfad zu Binary&HPL.dat
def get_target_path(spec):
    if(spec.find('^')==-1):
        pth = shell(spack_binary+' find --paths '+spec)
    else:
        pth = shell(spack_binary+' find --paths '+spec[:spec.find('^')])
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
def eval_partition(profile):
    if profile[3][0]!='':
        return profile[3][0]
    else:
        error_log('Partition unterspezifiziert im Profil: '+profile[0][0])
        while True:
            #clear()
            print('Eine Partition im Profil {} wurde nicht spezifiziert...'.format(profile[0][0]))
            avail_part = shell('sinfo -h --format=%R')
            print('Vorschläge: '+avail_part)
            inp = input_format()
            if inp in avail_part.split():
                return inp
            else:
                continue

#Falls keine Nodezahl spezifiziert ist, erst mal Benchunabhängig
def eval_node_count(profile):
    if profile[3][1]!='':
        if profile[3][2]!='' and profile[3][3]!='':
            if profile[3][1]<math.ceil(int(profile[3][2])/int(profile[3][3])):
                error_log('Nodezahl unstimmig bzgl. Prozess-&task-per-node-Zahl im Profil: '+profile[0][0])
        else:
            return profile[3][1]
    elif profile[3][2]!='' and profile[3][3]!='':
        #z.B. 7 Prozesse, 3 task per node -> Aufrundung von 7/3 -> 3 Nodes allokieren
        return math.ceil(int(profile[3][2])/int(profile[3][3]))
    else:
        error_log('Nodezahl unterspezifiziert im Profil: '+profile[0][0])
        return 1

#Sollte >1 und überhaupt spezifiziert sein, denn z.B. hpl will mit einem Prozess gar nicht erst starten!
def eval_proc_count(profile):
    if profile[3][2]!='' or profile[3][2]>1:
        return profile[3][2]
    else:
        error_log('Prozesszahl unter- bzw. falsch (gleich 1) spezifiziert im Profil: '+profile[0][0])
        #clear()
        if profile[3][2]=='':
            print('Die Prozesszahl im Profil {} wurde nicht spezifiziert...'.format(profile[0][0]))
        elif profile[3][2]==1:
            print('Die Prozesszahl (=1) im Profil {} ist nicht unbedingt sinnvoll...'.format(profile[0][0]))
        print('Korrektur?')
        return input_format()

def find_binary(profile, bench_id):
    #Primärpackage isolieren
    _ = profile[0][3].find('^')
    spec_short = (profile[0][3][:_]).strip()
    
    if bench_id == hpl_id:
        bin_path = shell(spack_binary+' find --paths '+spec_short)
        #Die Benchmarks sollten vom home-Verzeichnis aus erreichbar sein... <-- TODO: klären ob das den Anforderungen entspricht
        _ = bin_path.find('/home')
        if _ == -1:
            error_log('Das Benchmark-Package {} ist (zumindest lokal) nicht aufzufinden! Profil: '.format(spec_short)+profile[0][0])
        else:
            bin_path = ((bin_path[_:]).strip()+'/bin/')
    return bin_path



"""
Skriptbau-Funktionen
"""

#Default Argument <=> wir wollen alle Profile laufen lassen
def bench_run(bench_id, farg = 'all', extra_args = ''):

    #Vorschlag: Überarbeitung der Menü-Ausgabe, vll über eine globale String-Variable, das würde simultane Menü und Flag-Nutzung erlauben
    #z.B. global menutxt und in der menu-Fkt das printen immer über diese globale Variable
    #Falls das überhaupt nötig ist...
    menutxt, tag, pth = '', tag_id_switcher(bench_id), get_cfg_path(tag)
    
    #Aufarbeitung des Argumentstrings
    if farg == 'all':
        names = get_cfg_names(pth, tag)
    else:
        names = farg_to_list(farg, tag)
    
    #Die Liste der Namen der verfügbaren Profile
    avail_names = get_cfg_names(pth, tag)
    #Die Liste der Namen der nicht verfügbaren Profile
    unavail_names = []
    
    #Die Liste der geladenen Profile aus dem Config-Ordner
    selected_profiles = cfg_profiles[bench_id]
    #Namen von verfügbaren aber nicht ausgewählten Profilnamen
    unselected_names = []
    
    for profile in selected_profiles:
        #profile[0][0] <=> Wir schauen in den Metadaten nach dem Profilnamen
        if profile[0][0] not in names:
            #Aussortieren, falls der Name nicht unter den übergebenen Namen ist
            del selected_profiles[selected_profiles.index(profile)]
            unselected_names.append(profile[0][0])
    for name in names:
        if name not in avail_names:
            error_log('Profil: '+name+' war nicht verfügbar!')
            menutxt+='Profil: '+name+' war nicht verfügbar!'+'\n'
            unavail_names.append(name)
    for profile in selected_profiles:
        menutxt+='Ausgewählt: '+profile[0][0]+'\n'
    
    #Prüfe ob alle verfügbar sind, breche sonst ab TODO
    
    #Skriptbau
    if extra_args!='':
        menutxt+='...an srun würde übergeben werden: '+build_batch(selected_profiles, bench_id, extra_args)
    else:
        menutxt+='...an srun würde übergeben werden: '+build_batch(selected_profiles, bench_id)
    
    return menutxt

#Hiermit soll das Skript gebaut werden
#Welche Parameter wären sinnvoll? <---- TODO 
def build_batch(selected_profiles, bench_id, extra_args = ''):
    
    tag = tag_id_switcher(bench_id)
    
    batchtxt='#!/bin/bash\n'
    #Noch mehr Einstellungen
    
    tstamp = time.ctime()
    
    #Namen der Auftragsordner
    run_dir = 'projects/'+tag+'_'+'['+tstamp+']'+'_'+'[run]/'
    res_dir = 'projects/'+tag+'_'+'['+tstamp+']'+'_'+'[results]/'
    
    #Erst mal statisch & Minimalallokation
    #An dieser Stelle sollten später aus den allgemeinen Metadaten die Allokationsparameter ausgelesen werden <-- TODO
    batchtxt+='#SBATCH --partition=vl-parcio\n'
    batchtxt+='#SBATCH --begin=now+120\n'
    batchtxt+='#SBATCH --nodes=1\n'
    batchtxt+='#SBATCH --job-name='+tag+'_run'+'['+tstamp+']'+'\n'
    batchtxt+='#SBATCH --output='+run_dir+tag+'_run'+'['+tstamp+']'+'.out'+'\n'
    batchtxt+='#SBATCH --error='+run_dir+tag+'_run'+'['+tstamp+']'+'.err'+'\n'
    
    if os.path.isdir('projects/'+run_dir[:-1])==False:     
        shell('mkdir -p '+'projects/'+run_dir[:-1])
    if os.path.isdir('projects/'+res_dir[:-1])==False:     
        shell('mkdir -p '+'projects/'+res_dir[:-1])
    
    #Einzelne Jobskripte je Profil
    for profile in selected_profiles:
        if bench_id == hpl_id:
            #Anpassung z.B. für den Fall: versch. Profile benutzen gleiches hpl package mit untersch. HPL.dat Parametern
            #hpl_handler_pth muss noch per Funktion definiert werden! <-- TODO
            batchtxt+='python3 '+hpl_handler_xpth+' '+profile[0][1]+' '+profile[0][2]+'\n'
        if extra_args!='':
            batchtxt+='srun '+build_job(profile, bench_id, run_dir, res_dir, extra_args)
        elif len(extra_args)==0:
            batchtxt+='srun '+build_job(profile, bench_id, run_dir, res_dir)
    
    #Niederschreiben des Skripts & Rückgabe des entspr. Pfads hin
    file_w(run_dir+'{}.sh'.format(tag+'_run'+'['+tstamp+']'),batchtxt,'a')
    return run_dir+'{}.sh'.format(tag+'_run'+'['+tstamp+']')

def build_job(profile, bench_id, run_dir, res_dir, extra_args = ''):

    #Manche Dinge werden direkt ermittelt...
    proc_count = eval_proc_count(profile)
    bin_path = find_binary(profile, bench_id)

    #Shebang
    jobtxt='#!/bin/bash\n'
    #Partition per Funktion (ggf. Usereingabe)
    jobtxt+='#SBATCH --partition={}\n'.format(eval_partition(profile)) 
    #Nodezahl wird per Funktion bestimmt aus tasks per node und der Prozessanzahl
    jobtxt+='#SBATCH --nodes={}\n'.format(eval_node_count(profile))
    """
    #Anzahl der Prozesse
    jobtxt+='#SBATCH --ntasks={}\n'.format(proc_count)
    """
    #Anzahl der Prozesse pro Node
    if profile[3][3]!='':
        jobtxt+='#SBATCH --ntasks-per-node={}\n'.format(profile[3][3])
    #Anzahl der CPUs pro Task/Prozess(default lt. SLURM-Doku: 1 Kern per Task)
    if profile[3][4]!='':
        jobtxt+='#SBATCH --cpus-per-task={}\n'.format(profile[3][4])
    #Anzahl an allokiertem Speicher pro CPU
    if profile[3][5]!='':
        jobtxt+='#SBATCH --mem-per-cpu={}\n'.format(profile[3][5])
    #Startzeitpunkt
    if profile[3][6]!='':
        jobtxt+='#SBATCH --begin={}\n'.format(profile[3][6])
    #Zeitlimit
    if profile[3][7]!='':
        jobtxt+='#SBATCH --time={}\n'.format(profile[3][7])
    #Ziel-User für Emailbenachrichtigungen
    if profile[3][8]!='':
        jobtxt+='#SBATCH --mail-user={}\n'.format(profile[3][8])
    #Valide Trigger für Benachrichtigungen
    if profile[3][9]!='':
        jobtxt+='#SBATCH --mail-type={}\n'.format(profile[3][9])
    #Jobname (<=> Profilname)
    jobtxt+='#SBATCH --job-name={}\n'.format(profile[0][0][:-4])
    #Ziel für Output (sollte in (...)[results] landen)
    jobtxt+='#SBATCH --output={}\n'.format(res_dir+'/'+profile[0][0][:-4]+'.out')
    #Ziel für Fehler (sollte in (...)[results] landen)
    jobtxt+='#SBATCH --error={}\n'.format(res_dir+'/'+profile[0][0][:-4]+'.err')
    #<--- Überschreibmöglichkeit für individuelle Skripte? (vll mit offenem Block)    
    
    jobtxt+='\n'
    
    #Sourcen von spack <--- TODO: verallgemeinern für bel. Pfade
    jobtxt+='source ~/spack/share/spack/setup-env.sh'
    
    #Laden der passenden Module
    #Funktioniert nur für hpl! (Metadaten haben andere Struktur...) <--- TODO: verallgemeinern für bel. benchmarks
    module = profile[0][3].replace('^',' ').split()
    for _ in module:
        jobtxt+= 'spack load {}\n'.format(module[_])
    
    jobtxt+='\n'
    
    #Skriptzeile in der eine Binary ausgeführt wird
    jobtxt+=execute_line(bench_id, bin_path, proc_count, extra_args)
    
    #TODO: Entladen von Modulen, nötig? Das ist ja ein abgeschlossenes Jobscript...
    #
    
    #Niederschreiben des Skripts & Rückgabe des entspr. Pfads hin
    if os.path.isdir('projects/'+run_dir[:-1])==True:
        file_w(run_dir+'{}.sh'.format(profile[0][0][:-4]),jobtxt,'a')
    return run_dir+'{}.sh'.format(profile[0][0][:-4])



"""
Installation
"""

def view_install_specs(name=0):
    try:
        if name==0:
           return shell('spack find --show-full-compiler')
        else:
            return shell('spack find --show-full-compiler '+name)  
    
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))

#Prüft Installationsausdruck auf grobe Syntaxfehler
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

#Überprüft ob ein einzelner spec (Name + Version) existiert
def check_spec(name,version=-1):
    try:        
        out = shell('spack info '+str(name))
        #Falls keine Version vorhanden
        if version == -1:
            if out.find('Error')== -1:
                return True 
        elif out.find(version) != -1:
            return True         
        return False
    
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))

#Prüft ob Installationsausdruck gültig ist (alle Specs)
def check_expr(expr):
    if check_expr_syn(expr):
        arr = expr.split('^')        
        for spec in arr:
            s=spec.split('%')            
            
            #Untersuchung von einzelnem Package und Version
            for _ in s:            
                if _[0][:0]=='@':
                    #print('Name fehlt!')
                    #Package Name fehlt
                    return False               
                
                _=_.split('@')                
                if len(_) > 1:
                    if not check_spec(_[0],_[1]):                   
                        error_log(_[0]+'@'+_[1]+' existiert nicht')
                        #Version existiert nicht
                        return False
                else:
                    if not check_spec(_[0]):
                        #Package existiert nicht
                        error_log(_[0]+' existiert nicht')
                        return False
       
        return True
    #Syntaxfehler im Ausdruck
    return False

#Entfernt bereits installierte specs aus Installationsausdruck
def remove_installed_spec(expr):
    arr=expr.split('^')    
    all_specs=view_install_specs()
    out=''
    for _ in arr:        
        if all_specs.find(_)==-1 and out.find(_)==-1:
            out=out+'^'+_
    if out!='':        
        return out[1:]
    else:
        return out

#Entfernt redundante Specs, erhält eine Liste aus [spec^spec^...^spec][...] Ausdrücken
def remove_redudant_specs(expr):
    spec_list=[]    
    for list in expr:
        for _ in list.split('^'):
            insert=True
            for spec_ in spec_list:
                if _ in spec_:
                    insert=False
            if insert:
                spec_list.append('^'+_)
            
    for _ in spec_list:
        spec_list[spec_list.index(_)]=_[1:]    
    return spec_list
        
        
        
#Schreibt Script zum installieren der specs 
#TODO: Auslagern der Slurmparameter                    
def install_spec(expr):
    #Entfernt unnötig redundate Specs
    expr=remove_redudant_specs(expr)
    partition=cfg_profiles[0][0][2][0]
    node=cfg_profiles[0][0][2][1]
    task=cfg_profiles[0][0][2][2]
    cpus=cfg_profiles[0][0][2][3]
    #Check ob angegebene Partition existiert
    if shell('sinfo -h -p '+partition).find(partition)==-1:
        print('Partition: '+partition+' existiert nicht')
        return error_log('Partition: '+partition+' existiert nicht')  
    
    slurm=''
    specs=''
    #Holt sich max. CPU Anzahl der Partition
    #cpus=shell('sinfo -h -p '+partition+' -o "%c"').split('+')[0]
    #Falls install.sh nicht existiert wird es erstellt und Ausführbar gemacht
    if (os.path.isfile('install.sh'))==False: 
            shell('touch install.sh')
            shell('chmod +x install.sh')
            file_w('install.sh','','a')
    else:
        #Clear install.sh
        shell('echo a > install.sh')    
    
    #Slurmparameter für die Installation
    slurm='#!/bin/bash\n' \
    +'#SBATCH --nodes='+node+'\n' \
    +'#SBATCH --ntasks=1'+task+'\n' \
    +'#SBATCH --cpus-per-task='+cpus+'\n' \
    +'#SBATCH --partition='+partition+'\n' \
    +'#SBATCH --output=install.out\n' \
    +'#SBATCH --error=install.err\n\n'   
    file_w('install.sh',slurm,0)    
    
    for e in expr:
        if check_expr(e):
            e=remove_installed_spec(e)            
            if e != '':                    
                specs=specs+'srun spack install '+e+'\n'                 
            else:                
                error_log(e+': Bereits installiert')
                
        else:
            print('Installation abgebrochen: '+e+' existiert nicht!')
            return error_log('Installation abgebrochen: '+e+' existiert nicht!')
            
    if specs is not '':
        file_w('install.sh',str(specs),'a')
        user=shell('echo $USER')
        info = shell('squeue -u '+user)
        error_log(info)
        #shell('sbatch install.sh')
        time.sleep(0.5)
        print('Installation läuft:\n'+info)
                
    else:
        return print('Bereits alles installiert!')
         


"""
Menüfunktionen
"""
def printmenu(txt = ''):
    clear()
    print('---Menü---')
    print('(0) Exit')
    print('(1) Optionen')
    #evtl. anzeigen lassen, dass die Profile lauffähig sind?
    print('(2) HPL')
    print('(3) OSU')
    print('(4) Fehleranzeige {}'.format(check_err_stack()))
    print(' ')
    print(str(txt))


#Hauptmenü
def menu():
    
    global errorstack
 
    #Damit man die Optionen sehen kann
    printmenu(initm)
    
    #Interaktivität mit Nutzereingabe
    while True:
        opt = input_format()

        if opt == '0' or opt == 'q':
            clear()
            #SystemExit(0)
            break
        elif opt == '1' or opt == 'options':       
            printmenu('Info: Noch nicht implementiert...')           
        elif opt == '2' or opt == 'hpl':
            printmenu('Info: Noch nicht implementiert...')      
        elif opt == '3'or opt == 'osu':
            osu_menu()
        elif opt == '4':
            elist = ''
            while len(errorstack)!=0:
                elist = elist + '\n' + errorstack.pop()
            printmenu('Zuletzt aufgetretene Fehler... {}'.format(elist))
        elif opt[0:5] == 'code:':
            r = code_eval(opt[5:])
            printmenu('Rückgabe: '+str(r)+' [print] --- '+str(type(r))+' [typ]')
        elif opt[0:6] == 'shell:':
            r = str(shell(opt[6:]))
            printmenu('Ausgabe: \n'+r)   
        else:
            printmenu('Eingabe ungültig: Bitte eine Ganzzahl, z.B. 1')   

#OSU-Menu
def osu_menu():    
    opt = -1
    while True:
        clear()
        print('---OSU---')
        print('(0) Back')
        print('(1) Run')
        print('(2) View install specs')
        print('(3) Install')
        print(' ')        
        
        if opt == -1:
             opt = str(input_format())
        if opt == '0' or opt == 'q':            
            printmenu()
            return True
        elif opt == '1' or opt == 'run':            
            print('Info: Noch nicht implementiert...')
        elif opt == '2' or opt == 'specs':                        
            print(view_install_specs('osu-micro-benchmarks'))
        elif opt == '3' or opt == 'install':            
            print("Bitte spec^spec^...^spec eingeben\n") 
            print(' ')  
            print(install_spec(str(input_format())))        
        else:            
            print('Eingabe ungültig: Bitte eine Ganzzahl, z.B. 1')
            clear()            
        opt = str(input_format())
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
            #-> Vorsicht: Index-Fehler bzgl. leerer Zeilen!
            
            #print('Schreibtest (vor-1): '+stringlist[int(pos-1)])
            #print('Schreibtest (vor): '+stringlist[int(pos)])
            #print('Schreibtest (vor+1): '+stringlist[int(pos+1)])
            stringlist[int(pos)]=txt
            #print('Schreibtest (nach-1): '+stringlist[int(pos-1)])
            #print('Schreibtest (nach): '+stringlist[int(pos)])
            #print('Schreibtest (nach+1): '+stringlist[int(pos+1)])
            #...und schreiben sie wieder zurück
            
            with open(name, 'w') as f:      
                f.writelines(stringlist)
        else:
            with open(name, "a") as f:     
                f.write('\n'+txt)
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__)+'\nfile_w wurde aufgerufen aus: '+str(inspect.stack()[1][3])+'\nZieldatei: '+name+'\nPosition: '+str(pos))



"""
Funktionen die HPL zuzuordnen sind
"""

"""
#Default Argument <=> wir wollen alle Profile laufen lassen
def hpl_run(farg = 'all'):

    #Vorschlag: Überarbeitung der Menü-Ausgabe, vll über eine globale String-Variable, das würde simultane Menü und Flag-Nutzung erlauben
    #z.B. global menutxt und in der menu-Fkt das printen immer über diese globale Variable
    #Falls das überhaupt nötig ist...
    menutxt=''

    #Aufarbeitung des Argumentstrings
    if farg == 'all':
        names = get_cfg_names(hpl_cfg_pth, 'hpl')
    else:
        names = farg_to_list(farg, 'hpl')
    
    #Die Liste der Namen der verfügbaren Profile
    avail_names = get_cfg_names(hpl_cfg_pth, 'hpl')
    #Die Liste der Namen der nicht verfügbaren Profile
    unavail_names = []
    
    #Die Liste der geladenen Profile aus dem Config-Ordner
    selected_profiles = cfg_profiles[hpl_id]
    #Namen von verfügbaren aber nicht ausgewählten Profilnamen
    unselected_names = []
    
    for profile in selected_profiles:
        #profile[0][0] <=> Wir schauen in den Metadaten nach dem Profilnamen
        if profile[0][0] not in names:
            #Aussortieren, falls der Name nicht unter den übergebenen Namen ist
            del selected_profiles[selected_profiles.index(profile)]
            unselected_names.append(profile[0][0])
    for name in names:
        if name not in avail_names:
            error_log('Profil: '+name+' war nicht verfügbar!')
            menutxt+='Profil: '+name+' war nicht verfügbar!'+'\n'
            unavail_names.append(name)
    for profile in selected_profiles:
        menutxt+='Ausgewählt: '+profile[0][0]+'\n'
    
    #Prüfe ob alle verfügbar sind, breche sonst ab TODO
    
    #Skriptbau
    menutxt+='...an srun würde übergeben werden: '+build_batch(selected_profiles, hpl_id)
    
    return menutxt
"""

def execute_line(bench_id, bin_path, proc_count, extra_args):
    txt = ''
    if bench_id==hpl_id:
        txt = 'mpirun -np {pcount} {bpath}xhpl'.format(pcount = proc_count, bpath = bin_path)
    elif bench_id==osu_id:
        txt = 'unklar...'
    return txt

#Startpunkt
clear()
cl_arg()
