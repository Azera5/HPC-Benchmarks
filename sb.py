import os
import os.path
import subprocess
import datetime
import math
import inspect
import time
import fnmatch
import re
import argparse
from argparse import RawTextHelpFormatter

hpl_cfg_pth = 'config/hpl/'
osu_cfg_pth = 'config/osu/'
spack_binary = '~/spack/bin/spack'
errorstack = []

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
            error_log('returncode ist nicht null!')
        #.stdout liefert einen Binärstring desw. die Dekodierung
        return p.stdout.decode('UTF-8')
    except Exception as exc:
        error_log(' {} [Exception]'.format(type(exc).__name__))

#Wertet einen Python-Ausdruck aus
def code_eval(expr):
    try:
        return eval(expr)
    except Exception as exc:
        error_log(' {} [Exception]'.format(type(exc).__name__))

#Existieren überhaupt log.txt, config/hpl/, config/hpl/hpl_cfg_[d, 1, ..., n] etc.
def check():
    str = ''
    if os.path.isfile('log.txt')==False:     
        shell('touch log.txt')
        str = str+'errorlog erstellt ...\n'
    if os.path.isdir(hpl_cfg_pth)==False:     
        shell('mkdir -p '+hpl_cfg_pth)
        str = str+'Config-Verzeichnis für HPL erstellt ...\n'
        #Hier sollte noch eine Funktion sinnvolle Werte reinschreiben! <---TODO
    if os.path.isfile(hpl_cfg_pth+'hpl_cfg_d.txt')==False:     
        shell('touch '+hpl_cfg_pth+'hpl_cfg_d.txt')
        str = str+'default Config für HPL: \'hpl_cfg_d.txt\' erstellt ...\n'
    #Wäre gut wenn man sehen könnte ob lokale spack Installation da ist oder nicht, vll auch mit Pfadangabe...

#Liefert für eine Configzeile "123.4.5   [Parameter x]" nur die Zahl
def config_cut(line):
    line = line[:line.find("[")]
    return line.strip()

#Ein Art Prompt für den Nutzer
def input_format():
    print(' ')
    print('Eingabe: ', end='')
    return input()

def clear():
    os.system('clear')
    #print('\n\n\n---Debugprint---\n\n\n')

#Liefert Files, keine Verzeichnisse
def get_names(pth):
    r = os.listdir(pth)
    for _ in r:
        if os.path.isdir(_)==True:
            r.remove(_)
    return r

#Liefert Textfiles eines bestimmten Typs (z.B. hpl_cfg_(...).txt)
def get_cfg_names(pth, type):
    return fnmatch.filter(get_names(pth), type+'_cfg_*.txt')

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
    printmenu()
    
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

#Zu entfernen sobald die fortgeschritteneren Funktionen fertig sind
"""
#Passende Index-Grenzen für die Config setzen <--- TODO
def get_hpl_spec(pth):
    symb = ['@', '%', '@', '^', '@', '%', '@', '^', '@', '%', '@']
    spec = 'hpl'
    #Cofig-Zeile ab 1 aber Symbol-Liste ab 0, desw. der Index-Offeset
    for _ in range(0,11):
        symb[_] = symb[_]+config_cut(file_r(pth,(_+1)))
        #Nur anhängen, wenn auch was in der Config stand
        #Vorsicht: Es müsste noch geprüft werden ob vor einem @blabla überhaupt etwas steht!
        if len(symb[_])>2:
            spec = spec+symb[_]
    print('DBG --- get_hpl_spec(pth) ermittelt:'+spec)
    return spec
"""

#Bekommt eine Liste bzgl. der Packages aus einer Config, liefert die package spec
def get_hpl_spec(cfg_list):
    symb = ['@', '%', '@', '^', '@', '%', '@', '^', '@', '%', '@']
    spec = 'hpl'
    #Cofig-Zeile ab 1 aber Symbol-Liste ab 0, desw. der Index-Offeset
    for _ in range(0,11):
        symb[_] = symb[_]+config_cut(cfg_l[1][_+1])
        #Nur anhängen, wenn auch was in der Config stand
        #Vorsicht: Es müsste noch geprüft werden ob vor einem @blabla überhaupt etwas steht!
        if len(symb[_])>2:
            spec = spec+symb[_]
    print('DBG --- get_hpl_spec(pth) ermittelt:'+spec)
    return spec

def get_cfg(pth):
    return 'noch nicht implementiert...'
    #TODO: get_cfg_names sollte getestet sein...
    #return cfg_list

#Hier soll HPL.dat dem Profil entsprechend justiert werden
def set_data_hpl(cfg, pth):
    print('DBG: set_data_hpl hat die File gefunden -> '+str(os.path.isfile(pth+'/HPL.dat')))
    #Überschreiben mit Offeset (erst ab Index 13 geht der HPL Abschnitt in der Config los)
    #Auskommentiert bis Schreibfunktion gefixt ist <--- TODO
    """
    if (os.path.isfile(pth+'/HPL.dat'))==True:
        for _ in range(2,30):
            file_w(pth+'/HPL.dat',file_r(cfg,_+11),_)
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

def hpl_run(id):
    
    #Hol alle cfg_lists in eine Übergeordnete Liste
    profile_list = []
    #TODO: get_cfg() sollte fertig sein
    
    #Prüfe ob alle verfügbar sind, breche sonst ab TODO
    
    #Lasse eine Funktion daraus ein Skript bauen
    
    #Lass das Skript laufen
    
    return 'noch nicht implementiert...'

"""
Funktionen die OSU zuzuordnen sind
"""  




#Startpunkt
clear()
check()
cl_arg()
