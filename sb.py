import os
import os.path
import subprocess
import datetime
import math
import inspect
import time

hpl_cfg_path = "config/hpl/"

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

def menu(txt):
    print('---Menü---')
    print('(0) Exit')
    print('(1) Optionen')
    print('(2) HPL')
    print('(3) OSU')
    print('(4) Lesetest')
    print('(5) Schreibtest')
    print(' ')
    
    #Nachrichten an den Nutzer aus vorh. Vorgängen: Exceptions, stdout von Subshell-Aufrufen...
    print(str(txt))
    
    #Nutzereingabe
    opt = str(input_format())
    if opt == '0':
        clear()
        SystemExit(0)
    elif opt == '1':
        clear()
        menu('Info: Noch nicht implementiert...')
    elif opt == '2':
        clear()
        menu('Info: Noch nicht implementiert...')
    elif opt == '3':
        clear()
        menu('Info: Noch nicht implementiert...')
    #Testoption, später löschen
    elif opt == '4':
        clear()
        print('Dateiname?')
        n1 = input_format()
        print('Zeile?')
        l1 = input_format()
        menu('Leseversuch: '+file_r(n1, l1))
    #Testoption, später löschen
    elif opt == '5':
        clear()
        print('Dateiname?')
        n2 = input_format()
        print('Was schreiben?')
        t2 = input_format()
        print('Zeile?')
        l2 = input_format()
        file_w(n2, t2, l2)
        time.sleep(0.5)
        menu('Schreibversuch wurde unternommen...')
    elif opt[0:6] == 'shell:':
        clear()
        menu('Ausgabe: \n'+str(shell(opt[6:])))
    else:
        clear()
        menu('Eingabe ungültig: Bitte eine Ganzzahl, z.B. 1')
     
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
