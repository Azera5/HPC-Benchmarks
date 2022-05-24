import os
import os.path
import subprocess
import datetime
import math
import inspect
import time

hpl_cfg_pth = 'config/hpl/'
spack_binary = '~/spack/bin/spack'

#In welcher Funktion ist wann, welche Exception o.a. Unregelmäßigkeit aufgetreten?
def error_log(txt):
    txt = str(inspect.stack()[1][3])+' [Funktion] '+str(datetime.datetime.now())+' [Zeitpunkt] '+txt+'\n'
    file_w('log.txt', txt, 'a')

#Existieren überhaupt log.txt, config/hpl/, config/hpl/hpl_cfg_[d, 1, ..., n] etc.
def check():
    str = ''
    if (os.path.isfile('log.txt'))==False:     
        shell('touch log.txt')
        str = str+'errorlog erstellt ...\n'
    if (os.path.isdir(hpl_cfg_pth))==False:     
        shell('mkdir -p '+hpl_cfg_pth)
        str = str+'Config-Verzeichnis für HPL erstellt ...\n'
        #Hier sollte noch eine Funktion sinnvolle Werte reinschreiben! <---TODO
    if (os.path.isfile(hpl_cfg_pth+'hpl_cfg_d.txt'))==False:     
        shell('touch '+hpl_cfg_pth+'hpl_cfg_d.txt')
        str = str+'default Config für HPL: \'hpl_cfg_d.txt\' erstellt ...\n'
    menu(str)
    #Wäre gut wenn man sehen könnte ob lokale spack Installation da ist oder nicht, vll auch mit Pfadangabe...

def config_cut(line):
    line = line[:line.find("[")]
    return line.strip()

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
def build_hpl(cfg, pth, spec):
    print('DBG --- build_hpl würde hier bauen')
    


#lieber mit spack load
"""
srun -p vl - parcio -- pty bash
source spack/share/spack/setup-env.sh
module avail
module load hpl-2.3-gcc-8.5.0-m4rmdjk
module load openmpi-4.1.3-gcc-8.5.0-dm5ykbl
module load openblas-0.3.20-gcc-8.5.0-lnllhmy
module list
cd spack/opt/spack/linux-centos8-x86_64_v3/gcc-8.5.0/hpl-2.3-m4rmdjkqu7zmzc2b5kmjq6xhtdx7mdvr/bin
mpirun -np 2 xhpl
"""

#def create_script(par,hw_alloc,time,limit,out,spec): <--- TODO:Parameter?
#Die impl. Variante ist noch sehr statisch...
def create_script(bin,spec):
    if (os.path.isfile('sc.sh'))==False:
        shell('touch sc.sh') 
    file_w('sc.sh','#!/bin/bash','a')
    #file_w('sc.sh','#SBATCH --partition={}'.format(par),'a')
    file_w('sc.sh','#SBATCH --partition=vl - parcio','a')
    file_w('sc.sh','#SBATCH -N 2','a')
    file_w('sc.sh','#SBATCH --mem=4000M','a')
    file_w('sc.sh','#SBATCH --ntasks-per-node=2','a')
    file_w('sc.sh','#SBATCH -J Benchmark','a')
    file_w('sc.sh','#SBATCH -o b_results.%J.out','a')
    file_w('sc.sh','#SBATCH -e b_errors.%J.err','a')
    file_w('sc.sh','#SBATCH -e b_errors.%J.err','a')
    file_w('sc.sh','\n','a')
    file_w('sc.sh','source ~/spack/share/spack/setup-env.sh','a')
    
    module = (spec.replace('^',' ')).split()
    for _ in range(0,len(module)):
        file_w('spack load {}',module[_],'a')
    file_w('sc.sh','mpirun -np 2 {}'.format(bin),'a')
    
    

#Hiermit soll das Skript ausgeführt werden
#Übergabe eines Skripts an SLURM <--- Vorschlag: vielleicht erst mal mit einem statischen Skript?
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
    
    #Sind die entsprechenden Module überhaupt verfügbar?
    #<--- TODO: Funktion die das prüft, wenn nein, dann installieren!
    
    #Die passende HPL.dat muss angepasst werden!
    set_data_hpl(cfg, pth)
    
    #Jetzt soll das Skript gebaut werden
    print('\n\nbuild_hpl({},{},{}\n\n)'.format(cfg, pth, spec))
    build_hpl(cfg, pth, spec)
    
    

#Ein Art Prompt für den Nutzer
def input_format():
    print(' ')
    print('Eingabe: ', end='')
    return input()

def menu(txt=0, back=0):
    #Umleitung in aktuelles Menu
    if back !=0:
        clear()
        opt = back
        
    else:
        print('---Menü---')
        print('(0) Exit')
        print('(1) Optionen')
        print('(2) HPL')
        print('(3) OSU')
        print(' ')
    
    #Nachrichten an den Nutzer aus vorh. Vorgängen: Exceptions, stdout von Subshell-Aufrufen...
    if txt != 0 and back==0:
        print(str(txt))
    
    #Nutzereingabe
    if back == 0:
        opt = str(input_format())
    if opt == '0' or opt == 'q':
        clear()
        SystemExit(0)
    elif opt == '1' or opt == 'options':
        clear()       
        menu('Info: Noch nicht implementiert...')
    elif opt == '2' or opt == 'hpl':
        clear()
        menu('Info: Noch nicht implementiert...')
    
    elif opt == '3'or opt == 'osu':
        clear()
        osu_menu(back,txt)           

    elif opt[0:5] == 'code:':
        clear()
        eval(opt[5:])
        #Zum Testen erst mal noch so lassen
        """
        try:
            clear()
            r = eval(opt[5:])
            menu('Rückgabe: '+str(r)+' [print] --- '+str(type(r))+' [typ]')
        except Exception as exc:
            error_log(' {} [Exception]'.format(type(exc).__name__))
            menu('Exception: {}'.format(type(exc).__name__))
        """

    
    elif opt[0:6] == 'shell:':
        try:
            clear()
            menu('Ausgabe: \n'+str(shell(opt[6:])))
        except Exception as exc:
            error_log(' {} [Exception]'.format(type(exc).__name__))
            menu('Exception: {}'.format(type(exc).__name__))
   
  
    else:
        clear()
        menu('Eingabe ungültig: Bitte eine Ganzzahl, z.B. 1')    

def osu_menu(back,txt):    
    print('---OSU---')
    print('(0) Back')
    print('(1) Run')
    print('(2) View install specs')
    print('(3) Install')
    print(' ')        
        
    if back != 0:
        print(str(txt))  

    opt = str(input_format())    
        
    if opt == '0' or opt == 'q':
        clear()
        back = 0
        menu()
    elif opt == '1' or opt == 'run':
        clear()
        menu('Info: Noch nicht implementiert...','3')
    elif opt == '2' or opt == 'specs':
        clear()            
        menu(view_install_specs('mvapich2'),'3')
    elif opt == '3' or opt == 'install':
        clear()
        print("Name und Version optional\npackage@version%compiler@version\n") 
        print(' ')  
        menu(install_spec(str(input_format()),'mvapich2'),'3')        
    else:
        clear()
        menu('Eingabe ungültig: Bitte eine Ganzzahl, z.B. 1','3')

         
         
def clear():
    os.system('clear')
    #print('\n\n\n---Debugprint---\n\n\n')

#Lesefunktion: In welche Datei? An welche Position?  
def file_r(name, pos):  
    try:     
        with open(name, 'r') as f:      
            stringlist = f.readlines()
            return stringlist[int(pos)]
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))
        menu('Exception: {}'.format(type(exc).__name__))


#Diese Variante ist verbuggt (Lines werden nicht überschrieben, sondern Einträge werden davorgeschrieben)
"""
def file_w(name, txt, pos):
    try:
        if(pos!='a'):
            #Wir holen uns eine Stringliste...
            with open(name, 'r') as f:      
                stringlist = f.readlines()
            #...ändern den passenden Index ab...
            #-> Vorsicht: Index-Fehler bzgl. leerer Zeilen!
            stringlist[int(pos)]=txt
            #...und schreiben sie wieder zurück
            with open(name, 'w') as f:      
                f.writelines(stringlist)
        else:
            with open(name, "a") as f:     
                f.write('\n'+txt)
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))
        menu('Exception: {}'.format(type(exc).__name__))
"""

#Schreibfunktion: In welche Datei? Welchen Text? An welche Position? bzw. 'a' für anhängen/append
def file_w(name, txt, pos):
    try:
        if(pos!='a'):
            #Wir holen uns eine Stringliste...
            with open(name, 'r') as f:      
                stringlist = f.readlines()
            #...ändern den passenden Index ab...
            #-> Vorsicht: Index-Fehler bzgl. leerer Zeilen!
            print('Schreibtest (vor-1): '+stringlist[int(pos-1)])
            print('Schreibtest (vor): '+stringlist[int(pos)])
            print('Schreibtest (vor+1): '+stringlist[int(pos+1)])
            stringlist[int(pos)]=txt
            print('Schreibtest (nach-1): '+stringlist[int(pos-1)])
            print('Schreibtest (nach): '+stringlist[int(pos)])
            print('Schreibtest (nach+1): '+stringlist[int(pos+1)])
            #...und schreiben sie wieder zurück
            with open(name, 'w') as f:      
                f.writelines(stringlist)
        else:
            with open(name, "a") as f:     
                f.write('\n'+txt)
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))
        menu('Exception: {}'.format(type(exc).__name__))


def view_install_specs(name=0):
    try:
        if name==0:
           return shell('spack find --show-full-compiler')
        else:
            return shell('spack find --show-full-compiler '+name)  
    
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))
        menu('Exception: {}'.format(type(exc).__name__))

#Überprüft ob die angegebene Version existiert
def check_version(name,version):
    try:
        if name == 'error':
            return 'error'    
        out = shell('spack info '+str(name))
        if out.find(version) != -1:
            return name
        else: 
            return 'error'
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))
        menu('Exception: {}'.format(type(exc).__name__))
        

#Liefert empfohlene (aktuellste) Version     
def find_last_version(name):
    try:
        if name == 'error':
            return 'error'
        version = ''       
        out = shell('spack info '+str(name))         
        lines=out.split('\n')        
        for _ in lines:           
            if "Preferred version:" in str(_):
                index = lines.index(str(_))                
                for i in lines[index+1]:
                    if i.isdigit() or i is '.':
                        version=version+i
                    if i is 'h':
                        return version
        if version == '':
            return'error'
        
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))
        return 'Exception: {}'.format(type(exc).__name__)
        
 
#Format des input: name@version%compiler@version 
#Name und Versionen sind optional!
def extract(input,menu):
    try:
        #Vorbreitung des Eingabe
        out = ['','','','']
        input.replace(' ','')
        if input.find('%')==-1:
            return 'error'
        elif input[0]=='%':
            arr=[input]
        else:
            arr = input.split('%')
            arr[1] = '%'+arr[1]
        
        #Sondefall: Nur Compilername gegeben
        if arr[0][:1]=='@' or arr[0][:1]=='%':            
            if(menu=='main'):                
                print('Kein Packagename\nNeue Eingabe oder Abbruch(q)\n')
                out[0]=str(input_format())            
            else:
                out[0]=menu            
            
            if arr[0][:1]!='@':
                out[1]=find_last_version(out[0])
                arr=['',arr[0]]
            else:                
                out[1]=check_version(out[0],arr[0][1:arr.find('%')-1])           
            
        #Extrahiere Package Spezifikationen          
        elif arr[0].find('%') == -1:
            if arr[0].find('@') == -1:
                out[0] = arr[0]
                out[1]=find_last_version(arr[0])
            else:
                temp=arr[0].split('@')
                out[0] = temp[0]            
                out[1] = check_version(out[0],temp[1]) 

        #Extrahiere Compiler Spezifikationen 
        if arr[1].find('@') == -1:             
            out[2] = arr[1][1:]            
            out[3] = find_last_version(arr[1][1:])            
        else:            
            arr = arr[1].split('@')          
            out[2] = arr[1][1:]
            out[3] = check_version(out[2],arr[1])
            
        return out
        
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))
        menu('Exception: {}'.format(type(exc).__name__))
                
                
def install_spec(input,menu):
    try:
        #Par = [PackageName, PackageVersion, Compiler, Compilerversion]
        para = extract(input,menu)        
        
        #Abfangen nicht existierender Packages, Compiler oder Versionen
        if str(para).find('error')!=-1:
            return 'Abbruch: Falsche Eingabe!'
        else:
            #install command
            spec=str(para[0])+'@'+str(para[1])+' %'+str(para[2])+'@'+str(para[3])
            #Check ob spec bereits installiert ist
            if view_install_specs().find(spec) != -1:
                return 'Job ID: [comming soon] ' + spec
            #TODO Slurmscript schreiben, evtl in eigene Funktion auslagern?
            else:
                return spec +' ist bereits installiert'
            
    
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))
        return 'Exception: {}'.format(type(exc).__name__)
    

#Diese Funktion klappt, kann aber nicht alles! z.B. 'echo $$' printet nicht die Shell-PID!
"""
def shell(command): 
    try:
        #Ausgabe soll nicht direkt auf's Terminal (würde durch erneuten menu()-Aufruf überschrieben werden)
        #.split <=> Strings in Listen verwandeln; Nicht nötig falls shell=True
        p = subprocess.run(str(command).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if(p.returncode!=0):
            error_log('returncode is non-zero')
        #.stdout liefert einen Binärstring desw. die Dekodierung
        return p.stdout.decode('UTF-8')
    except Exception as exc:
        error_log(' {} [Exception]'.format(type(exc).__name__))
        menu('Exception: {}'.format(type(exc).__name__))
"""

def shell(command): 
    try:
        #Ausgabe soll nicht direkt auf's Terminal (würde sonst durch erneuten menu()-Aufruf überschrieben werden)
        p = subprocess.run(str(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        if(p.returncode!=0):
            error_log('returncode ist nicht null!')
        #.stdout liefert einen Binärstring desw. die Dekodierung
        return p.stdout.decode('UTF-8')
    except Exception as exc:
        error_log(' {} [Exception]'.format(type(exc).__name__))
        menu('Exception: {}'.format(type(exc).__name__))

#Startpunkt
clear()
check()

"""
sb.py wurde vollkommen überarbeitet
-> weniger Funktionalität (erst mal: noch kein Installieren/Ausführen)
-> ich war aber bemüht Konventionen einzuhalten: Kontext-Manager statt open/close; Behandlung von Ausnahmen via try/except Blöcken inkl. Errorlogging usw.
"""
