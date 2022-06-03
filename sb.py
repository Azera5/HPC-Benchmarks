import os
import os.path
import subprocess
import datetime
import inspect
import time
import fnmatch
import re
import argparse
from argparse import RawTextHelpFormatter



"""
Potentielle Usereingaben
"""
hpl_cfg_pth = ''
osu_cfg_pth = ''
spack_binary = ''



"""
Hilfsvariablen
"""
#Anzahl unterstützter Benchmarks (HPL, OSU, ...)
benchcount = 2
hpl_id = 1
osu_id = 2
#Sammelt kürzliche Fehlermeldungen

errorstack = []
#Trägt Informationen des Config-Ordners; Ersteintrag für Metadaten
#Index: [Benchmark-id][Profil-Nr.][Abschnitt][Zeile im Abschnitt]
cfg_profiles = [[]]*(benchcount+1)
#Initialnachricht
initm = ''


"""
Command-Line-Parameter
"""
def cl_arg():
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument('-i','--install',type=str,help=''+
    'all: Installiert alle specs aus Install-config\n' +
    'spec -> Installiert bestimmte spec\n\n')
    
    parser.add_argument('-r','--run',nargs='+',type=str,help=''+   
    'hpl [<cfg>,<cfg>,...,<cfg>]\n'+     
    '     Nummer -> Ausführung bestimmter hpl_cfg\n\n' +
    '     all -> Ausführung aller hpl_cfg\n' +
    'osu [<Test>] [<cfg>,<cfg>,...,<cfg>]\n'+
    '     Tests:\n'+
    '     latency\n' +
    '     bw\n' +
    '     bcast\n' +
    '     barrier\n' +
    '     allreduce\n'+    
    '     Nummer -> Ausführung bestimmter hpl_cfg\n\n'+
    '     all -> Ausführung aller osu_cfg\n') 
    args= parser.parse_args()
    if args.install:
        if args.install=='all':
            expr=''            
            print('#TODO: Install all')
            install_spec(expr)
        else:
            print(install_spec(args.install))
            
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
            
    if not args.install and not args.run:
        menu()
            

#Abschnittsgrenzen der hpl Configs:
hpl_cfg_abschnitt_1 = 11    # <=> Grundlagentechnologie
hpl_cfg_abschnitt_2 = 41    # <=> HPL.dat
hpl_cfg_abschnitt_3 = 50    # <=> SLURM


#Abschnittsgrenzen der osu Configs:
osu_cfg_abschnitt_1 = 7     # <=> Grundlagentechnologie
osu_cfg_abschnitt_2 = 16    # <=> 
osu_cfg_abschnitt_3 = 25    # <=> SLURM

#Wieviele Benchmarktypen kennen wir?
bench_count = 2

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
        error_log(' {} [Exception]'.format(type(exc).__name__))

#Wertet einen Python-Ausdruck aus
def code_eval(expr):
    """
    try:
        return eval(expr)
    except Exception as exc:
        error_log(' {} [Exception]'.format(type(exc).__name__))
    """
    return eval(expr)

#Ermittelt Pfade relevanter Verzeichnisse und Binaries, wenn nichts spezifiziert wurde
def find_paths():
    global hpl_cfg_pth, osu_cfg_pth, spack_binary   
    #An der Stelle, an der das Programm ausgeführt wird, sollten auch die configs sein
    if hpl_cfg_pth=='':
        hpl_cfg_pth = str(shell('pwd')+'/config/hpl/').replace('\n','').strip()
    if osu_cfg_pth=='':
        osu_cfg_pth = str(shell('pwd')+'/config/osu/').replace('\n','').strip()
    if spack_binary=='':
        r_list = str(shell('find ~ -executable -name spack -path \'*/spack/bin/*\'')).replace('\n',' ').split()
        #Wir nehmen die erstbeste spack Binary, wenn nichts per Hand spezifiziert wurde
        spack_binary = r_list[0].strip()

def check_data():
    global cfg_profiles
    #Für jeden Bench eine Liste, in jeder dieser Listen eine Liste pro Profil
    """
    _ = ['hpl:empty'*len(get_cfg_names(hpl_cfg_pth,'hpl'))]
    cfg_profiles.append(_)
    _ = ['osu:empty'*len(get_cfg_names(osu_cfg_pth,'osu'))]
    cfg_profiles.append(_)
    """
    #Hinweis: ['test']*n <=> ['test, 'test', ...] vgl. ['test'*n] = ['testtesttest...']
    for _ in range(0, len(get_cfg_names(hpl_cfg_pth,'hpl'))):
        #Ein Subliste pro Metadatenblock und drei Abschnitten je Profil
        cfg_profiles[1].append([[]]*4)
    for _ in range(0, len(get_cfg_names(osu_cfg_pth,'osu'))):
        cfg_profiles[2].append([[]]*3)
    

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
    return fnmatch.filter(get_names(pth), type+'_cfg_*.txt')

def config_out(bench_id):
    s=''
    for p in cfg_profiles[bench_id]:
        #Metadaten
        s += 'Profil: '+p[0][0]+'\n'
        if (p[0][1]!='')and(p[0][2]!=''):
            s += 'Configpfad: '+p[0][1]+'\n'
            s += 'Zielpfad: '+p[0][2]+'\n'
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

def get_osu_cfg():
    global cfg_profiles
    names = get_cfg_names(osu_cfg_pth, 'osu')
    sublist = []
    #i-te Configzeile (int), p für Profil (string)
    
    for p in names:
        #+1 damit auch die letzte Zeile ausgewertet wird
        for i in range(1,osu_cfg_abschnitt_1+1):
            sublist.append(config_cut(file_r(osu_cfg_pth+p,i)))
        cfg_profiles[osu_id][names.index(p)][1] = sublist
        sublist = []
        #+4 zum Überspringen der Trennzeilen; +1 damit auch die letzte Zeile ausgewertet wird
        for i in range(osu_cfg_abschnitt_1+4, osu_cfg_abschnitt_2+1):
            sublist.append(config_cut(file_r(osu_cfg_pth+p,i)))
        cfg_profiles[osu_id][names.index(p)][2] = sublist
        sublist = []
        #+2 zum Überspringen der Trennzeilen; +1 damit auch die letzte Zeile ausgewertet wird
        for i in range(osu_cfg_abschnitt_2+2, osu_cfg_abschnitt_3+1):
            sublist.append(config_cut(file_r(osu_cfg_pth+p,i)))
        sublist = []
        cfg_profiles[osu_id][names.index(p)][3] = sublist
        #Ersteintrag ist nur Platzhalter für Metadaten: Name, Configpfad, Zielpfad zu Binary&HPL.dat
        cfg_profiles[osu_id][names.index(p)][0] = p
        print('...')



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
            if s[0][:0]=='@':
                #print('Name fehlt!')
                #Package Name fehlt
                return False
               
            s=spec.split('@')
            if len(s) > 1:                    
                if not check_spec(s[0],s[1]):                   
                    #print(s[0]+'@'+s[1]+' existiert nicht')
                    #Version existiert nicht
                    return False
            else:
                if not check_spec(s[0]):
                    #Package existiert nicht
                    #print(s[0]+' existiert nicht')
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
        if all_specs.find(_)==-1:
            out=out+'^'+_
    if out!='':        
        return out[1:]
    else:
        return out
    
#Schreibt Script zum installieren der specs 
#TODO: Auslagern der Slurmparameter                    
def install_spec(expr):
        if check_expr(expr):
            expr=remove_installed_spec(expr)            
            if expr != '':
                if (os.path.isfile('install.sh'))==False: 
                    shell('touch install.sh')
                else:
                    #Clear install.sh
                    file_w('install.sh','',0)
                s='#!/bin/bash\n' \
                    + '#SBATCH --nodes=1\n' \
                    +'#SBATCH --ntasks=1\n' \
                    +'#SBATCH --partition=vl-parcio\n' \
                    +'#SBATCH --output=install.out\n' \
                    +'#SBATCH --error=install.err\n' \
                    +'echo spack install ' \
                    + expr
                #Achtung write: besser vorher install.sh leeren
                file_w('install.sh',' ','a')
                file_w('install.sh',str(s),0)
                print(shell('cat install.sh'))               
                return 'Installation läuft'
            else: 
                return 'Bereits alles installiert!'
                
        else:
            return 'Kann nicht installiert werden!'



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
        error_log(' {} [Exception]'.format(type(exc).__name__))

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
        error_log(' {} [Exception]'.format(type(exc).__name__))



"""
Funktionen die HPL zuzuordnen sind
"""

#Bekommt eine Liste bzgl. der Packages aus einer Config, liefert die package spec
def get_hpl_spec(cfg_list): 
    #Syntax bilden
    symb = ['@', '%', '@', '^', '@', '%', '@', '^', '@', '%', '@']
    spec = 'hpl'
    for _ in range(0,11):
        symb[_] = symb[_]+cfg_list[_] #config_cut(cfg_list[_])
        #Nur anhängen, wenn auch was in der Config stand
        #Vorsicht: Es müsste noch geprüft werden ob vor einem @blabla überhaupt etwas steht!
        if len(symb[_])>2:
            spec = spec+symb[_]
    #print('DBG --- get_hpl_spec(pth) ermittelt:'+spec)
    return spec

def get_hpl_target_path(spec):
    if(spec.find('^')==-1):
        pth = shell(spack_binary+' find --paths '+spec)
    else:
        pth = shell(spack_binary+' find --paths '+spec[:spec.find('^')])
    _ = pth.find('/home')
    return ((pth[_:]).strip()+'/bin')

#Braucht einen Pfad zum 
def get_hpl_cfg():
    global cfg_profiles
    names = get_cfg_names(hpl_cfg_pth, 'hpl')
    sublist = []
    #i-te Configzeile (int), p für Profil (string)
    for p in names:
        #+1 damit auch die letzte Zeile ausgewertet wird
        for i in range(1,hpl_cfg_abschnitt_1+1):
            sublist.append(config_cut(file_r(hpl_cfg_pth+p,i)))
        cfg_profiles[hpl_id][names.index(p)][1] = sublist
        sublist = []
        #+2 zum Überspringen der Trennzeilen; +1 damit auch die letzte Zeile ausgewertet wird
        for i in range(hpl_cfg_abschnitt_1+2, hpl_cfg_abschnitt_2+1):
            sublist.append(config_cut(file_r(hpl_cfg_pth+p,i)))
        cfg_profiles[hpl_id][names.index(p)][2] = sublist
        sublist = []
        #+2 zum Überspringen der Trennzeilen; +1 damit auch die letzte Zeile ausgewertet wird
        for i in range(hpl_cfg_abschnitt_2+2, hpl_cfg_abschnitt_3+1):
            sublist.append(config_cut(file_r(hpl_cfg_pth+p,i)))
        sublist = []
        cfg_profiles[hpl_id][names.index(p)][3] = sublist
        #Ersteintrag ist nur Platzhalter für Metadaten: Name, Configpfad, Zielpfad zu Binary&HPL.dat
        spec = get_hpl_spec(cfg_profiles[hpl_id][names.index(p)][1])
        cfg_profiles[hpl_id][names.index(p)][0] = [p, hpl_cfg_pth+p, get_hpl_target_path(spec), spec]
        print('...')

#Funktion schreibt HPL-Abschnitt aus dem Config-Profil in eine HPL.dat (beide Pfade notwendig)
def set_data_hpl(cfg, pth):
    print('DBG: set_data_hpl hat die File gefunden -> '+str(os.path.isfile(pth+'HPL.dat')))
    #Überschreiben mit Offeset (erst ab Index 13 geht der HPL Abschnitt in der Config los)
    #Auskommentiert bis Schreibfunktion gefixt ist <--- TODO
    """
    if (os.path.isfile(pth+'HPL.dat'))==True:
        for _ in range(2,30):
            file_w(pth+'HPL.dat',file_r(cfg,_+11),_)
    """

#Hiermit soll das Skript gebaut werden
#Welche Parameter wären sinnvoll? <---- TODO 
def build_hpl(id, bin, spec):
    if (os.path.isfile('sc.sh'))==False:
        shell('touch sc.sh') 
    file_w('sc.sh','#!/bin/bash','a')
    #file_w('sc.sh','#SBATCH --partition={}'.format(par),'a')
    file_w('sc.sh','#SBATCH --partition=vl-parcio','a')
    file_w('sc.sh','#SBATCH -N 2','a')
    file_w('sc.sh','#SBATCH --mem=4000M','a')
    file_w('sc.sh','#SBATCH --cpus-per-task=4','a')
    #Sinnvoller Jobname <--- TODO: evtl. Zeit, id? etc.
    #file_w('sc.sh','#SBATCH -J HPL-Benchmark[{}][{}]'.format(str(id), str(datetime.datetime.now())),'a')
    file_w('sc.sh','#SBATCH --job-name=hpl-test','a')
    #Info %j sollte zur ID (Zuw. des Jobs von SLURM, *nicht* config) und x% zum Namen ausgewertet werden! 
    file_w('sc.sh','#SBATCH -o %x.out','a')
    file_w('sc.sh','#SBATCH -e %x.err','a')
    file_w('sc.sh','\n','a')
    file_w('sc.sh','source ~/spack/share/spack/setup-env.sh','a')
    
    #Welche Packages müssen geladen werden?
    module = (spec.replace('^',' ')).split()
    for _ in range(0,len(module)):
        file_w('sc.sh', 'spack load {}'.format(module[_]),'a')
    
    #Ist das wirklich notwendig für den Zugriff auf HPL.dat? <---- TODO
    #Tipp: Flag prüfen für HPL.dat Verzeichnis
    file_w('sc.sh','cd {}'.format(bin),'a')
    
    file_w('sc.sh','mpirun -np 8 {}/xhpl'.format(bin),'a')

"""
#Hiermit soll das Skript ausgeführt werden
def hpl_run(id):

    #Welches Profil wird benutzt?
    cfg = hpl_cfg_pth+'hpl_cfg_{}.txt'.format(str(id))
    
    #Was ist das spec?
    spec = get_hpl_spec(cfg)
    _ = spec.find('^')
    spec_short = (spec[:_]).strip()
    
    #Was ist der Pfad zur Binary & HPL.dat?
    pth = shell(spack_binary+' find --paths '+spec_short)
    _ = pth.find('/home')
    pth = ((pth[_:]).strip()+'/bin')
    
    #Sind die entsprechenden Module überhaupt verfügbar? (Grafik Schritt 1)
    #<--- TODO: Funktion die das prüft, wenn nein, dann melden!
    #UPDATE: evtl. das Prüfen auslagern...
    
    #Die passende HPL.dat muss angepasst werden! (Grafik Schritt 2)
    set_data_hpl(cfg, pth)
    
    #Jetzt soll das Skript gebaut werden (Grafik Schritt 3)
    print('\n\nbuild_hpl({},{},{}\n\n)'.format(cfg, pth, spec))
    build_hpl(id, pth, spec)

#TODO Möglichkeit ein bzw. alle Profile laufen lassen
"""

"""
#Handling der übergebenen Argumente
#Aus dem zweiten Argument der -r Flag wird eine Liste aufbereitet
def hpl_preparation(farg):
    if farg == 'all':
        hpl_run(get_cfg_names(hpl_cfg_pth, 'hpl'))
    else:
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
            names[names.index(e)] = 'hpl_cfg_'+str(e)+'.txt'
        hpl_run(names)
"""

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
        print('farg-to-list:'+str(names[names.index(e)]))
        names[names.index(e)] = bench+'_cfg_'+str(e)+'.txt'
    return names
    
#Default Argument <=> wir wollen alle Benchmarks laufen lassen
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
    
    return menutxt
    
    #Prüfe ob alle verfügbar sind, breche sonst ab TODO
    
    #Lasse eine Funktion daraus ein Skript bauen
    
    #Lass das Skript laufen
    
    #return 'noch nicht implementiert...'

"""
Funktionen die OSU zuzuordnen sind
"""  




#Startpunkt
clear()
print('laden ...')
find_paths()
check_data()
check_dirs()
get_hpl_cfg()
get_osu_cfg()
cl_arg()
