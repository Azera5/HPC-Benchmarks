import sys
import os
import os.path
import datetime
import inspect
import fnmatch
import traceback


#sys.argv[1] <=> source
source = sys.argv[1]
 
#sys.argv[2] <=> target
target = sys.argv[2]

#sys.argv[3] <=> start line
sline = int(sys.argv[3])

#how many lines in the target should be skipped
offset = int(sys.argv[4]) 

#Funktion schreibt HPL-Abschnitt aus dem Config-Profil in eine HPL.dat (beide Pfade notwendig)
def dat_transfer():
    try:
        stringlist = []
        e = sline
        while True:
            if file_r(source, e).find('---')==-1:
                stringlist.append(prep_source_line(file_r(source, e)))
                e+=1
            else:
                break
        #we have to consider two offsets for both target >>+offset<< *and* source file >>-sline<<
        for n in range(e-sline):
            file_w(target, stringlist[n].rstrip(), n+offset)
    except Exception as exc:
        print(traceback.format_exc())
        
#Lesefunktion: In welche Datei? An welche Position?  
def file_r(name, pos):      
    with open(name, 'r') as f:      
        stringlist = f.readlines()
        return stringlist[int(pos)]

def file_w(name, txt, pos):
    try:
        if(pos!='a'):
            with open(name, 'r') as f:      
                stringlist = f.readlines()
            while len(stringlist)<=pos:
                stringlist.append('\n')           
            stringlist[int(pos)]=txt+'\n'
            with open(name, 'w') as f:
                f.writelines(stringlist)
        else:
            with open(name, "a") as f:     
                f.write(txt+'\n')
    except Exception as exc:
        print(traceback.format_exc())
        


def prep_source_line(line):
    return line.replace('[','').replace(']','')

dat_transfer()