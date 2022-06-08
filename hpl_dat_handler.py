import sys
import os
import os.path
import datetime
import inspect
import fnmatch



"""
Kernfunktion
"""

#Funktion schreibt HPL-Abschnitt aus dem Config-Profil in eine HPL.dat (beide Pfade notwendig)
def config_to_dat_transfer():
    try:
        stringlist = []
        for _ in range(0,31):
            if _ in range(2,31):
                #Wir holen die Zeile und schneiden bis auf den Int alles weg
                val1 = config_cut(file_r(sys.argv[1],_+11))
                #Wir schauen was wir überschreiben wollen und lassen den Int weg
                val2 = file_r(sys.argv[2]+'HPL.dat',_)
                #Wir fügen diese zwei Stücke zusammen, damit sich nur die Zahlen in der Ziel-HPL.dat ändern
                stringlist.append(val1+val2[val2.find(' '):])
            #Zeilen die man nicht transferieren muss
            else:
                stringlist.append(file_r(sys.argv[2]+'HPL.dat',_))
        os.remove(sys.argv[2]+'HPL.dat')       
        with open(sys.argv[2]+'HPL.dat', 'w') as f:
            f.writelines(stringlist)
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__)+'\nfile_w wurde aufgerufen aus: '+str(inspect.stack()[1][3])
    

#Lesefunktion: In welche Datei? An welche Position?  
def file_r(name, pos):  
    try:     
        with open(name, 'r') as f:      
            stringlist = f.readlines()
            return stringlist[int(pos)]
    except Exception as exc:     
        error_log(' {} [Exception]'.format(type(exc).__name__))

#In welcher Funktion ist wann, welche Exception o.a. Unregelmäßigkeit aufgetreten?
def error_log(txt):
    txt = str(inspect.stack()[1][3])+' [Funktion@hpl_dat_handler] '+str(datetime.datetime.now())+' [Zeitpunkt] '+txt+'\n'
    file_w('log.txt', txt, 'a')
    
#Liefert für eine Configzeile "123.4.5   [Parameter x]" nur die Zahl
def config_cut(line):
    c = line.find("[")
    if(c!=-1):
        line = line[:c]
    return line.strip()

"""
Ausführung
"""

config_to_dat_transfer()