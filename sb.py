import os
import os.path
import subprocess
import datetime
import math
import inspect
import time

hpl_cfg_path = 'config/hpl/'


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
    if (os.path.isdir(hpl_cfg_path))==False:     
        shell('mkdir -p '+hpl_cfg_path)
        str = str+'Config-Verzeichnis für HPL erstellt ...\n'
        #Hier sollte noch eine Funktion sinnvolle Werte reinschreiben! <---TODO
    if (os.path.isfile(hpl_cfg_path+'hpl_cfg_d.txt'))==False:     
        shell('touch '+hpl_cfg_path+'hpl_cfg_d.txt')
        str = str+'default Config für HPL: \'hpl_cfg_d.txt\' erstellt ...\n'
    menu(str)

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
        aktuell_menu = 'main'
        print('---Menü---')
        print('(0) Exit')
        print('(1) Optionen')
        print('(2) HPL')
        print('(3) OSU')
        print(' ')
    
    #Nachrichten an den Nutzer aus vorh. Vorgängen: Exceptions, stdout von Subshell-Aufrufen...
    if txt != 0:
        print(str(txt))
    
    #Nutzereingabe
    if back == 0:
        opt = str(input_format())
    if opt == '0' or opt == 'exit':
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
        try:
            clear()
            r = eval(opt[5:])
            menu('Rückgabe: '+str(r)+' [print] --- '+str(type(r))+' [typ]')
        except Exception as exc:
            error_log(' {} [Exception]'.format(type(exc).__name__))
            menu('Exception: {}'.format(type(exc).__name__))


    
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
    aktuell_menu ='mvapich2'
    print('Betritt aktuell_menu: '+aktuell_menu)
    print('---OSU---')
    print('(0) Back')
    print('(1) Run')
    print('(2) View install specs')
    print('(3) Install')
    print(' ')        
        
    if back != 0:
        print(str(txt))  

    opt = str(input_format())    
        
    if opt == '0' or opt == 'back':
        clear()
        back = 0
        menu()
    elif opt == '1' or opt == 'run':
        clear()
        menu('Info: Noch nicht implementiert...','3')
    elif opt == '2' or opt == 'specs':
        clear()            
        menu(shell('spack find --show-full-compiler mvapich2'),'3')
    elif opt == '3' or opt == 'install':
        print('Install aktuell_menu: '+aktuell_menu)
        print("Name@Version %compiler@Version\n(Name und Version optional)\n")                        
        info = install_spec(str(input_format()))
        print(info)
        menu('Installation läuft: '+info,'3')

         
         
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

#Schreibfunktion: In welche Datei? Welchen Text? An welche Position? bzw. 'a' für anhängen/append    
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


#Überprüft ob die angegebene Version existiert
def check_version(name,version):
    try: 
        out = shell('spack info '+str(name))
        if out.find(version) != -1:
            return True
        else: 
            return False
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))
        menu('Exception: {}'.format(type(exc).__name__))
        

#Liefert empfohlene (aktuellste) Version     
def find_last_version(name):
    try:
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
                        
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))
        return 'Exception: {}'.format(type(exc).__name__)
        
 
#Format des input: name@version %compiler@version 
#Name und Versionen sind optional!
def extract(str):
    try:
        #print('Extract aktuell_menu: '+aktuell_menu)
        out = ['','','','']
        arr = str.split()
        
        #Behandlung des Sondefalls dass nur der Compilername angegeben wurde
        if len(arr)==1:
            arr=['',arr[0]]        
       
        #Extrahiere Package Spezifikationen
        if arr[0].find('@') == -1:
            #print(aktuell_menu)
            if aktuell_menu != 'main':
                #print('1. PackageName: '+aktuell_menu)
                out[0] = aktuell_menu                
                out[1] = find_last_version(aktuell_menu)
                #print('PackageVersion: '+out[1])
            else:
                #print('2. PackageName: '+arr[0])
                out[0] = arr[0]                
                out[1] = find_last_version(arr[0]) 
                #print('PackageVersion: '+out[1])
        else:
            temp = arr[0].split('@')
            out[1] = temp[1]
            if aktuell_menu != 'main':
                out[0] = aktuell_menu
            else:                    
                out[0] = temp[0]

        #Extrahiere Compiler Spezifikationen        
        arr = arr[1].split('%')        
        if arr[1].find('@') == -1: 
            #print('Compilername: '+arr[0])
            out[2] = arr[1]            
            out[3] = find_last_version(arr[0])
            #print('Compilerversion: '+out[3])
        else:            
            arr = arr[1].split('@')                
            out[3] = arr[1]
            out[2] = arr[0]
            
        return out
        
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))
        menu('Exception: {}'.format(type(exc).__name__))
                
                
def install_spec(str):
    try:
        #print('InstallFunk aktuell_menu: '+aktuell_menu)
        #Par = [PackageName, PackageVersion, Compiler, Compilerversion]
        para = extract(str)
        print(str+' -> '+para)
        #if check_version(para[0],para[1]) and check_version(para[2],para[3]):
        return 'Pid: ?'+str(para[0])+'@'+str(para[1])+' %'+str(para[2])+'@'+str(para[3])
    
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
