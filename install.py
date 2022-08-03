import sys
import os
import subprocess
import re

from sb import shell, check_expr_syn, error_log


meta=sys.argv[1].split('#')
expr=sys.argv[2].split('#')
err=''

#plot.py Path
loc=str(os.path.dirname(os.path.abspath(__file__)))

#Shellfunktion aus sb.py (Hauptprogramm)
"""
def shell(cmd):
    #Ausgabe soll nicht direkt auf's Terminal
    p = subprocess.run(str(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)   
    #.stdout liefert einen Binärstring desw. die Dekodierung
    return p.stdout.decode('UTF-8')



#Prüft Installationsausdruck auf grobe Syntaxfehler
def check_expr_syn(expr):
    expr_list=['@%','%@','^%','%^','^@','@^']
   
   
    Hinweis bzgl. regulärem Ausdruck:
    {min,max} min/max vorkommen der vorrangegangenen Zeichenkette 
    \w Symbolmenge: [a-z, A-Z, 0-9, _]            
    * Vorangegangene Zeichenkette kommt beliebig oft vor (inkl. 0 mal)
    (...) Gruppe -> praktisch eine Zeichenkette
    \. Punktsymbol, da einfach nur . für einzelnes Zeichen steht            
  
    if re.search(r'@{1,1}(\w*\.*[%]{0,0}\w*)*@{1,}',expr):
        return False
    for _ in expr_list:
        r=expr.find(_)        
        if r != -1:
            sb.error_log('echo Syntaxfehler an Position: {} >> {}/install.err'.format(str(r),loc),locals())
            sb.err
            return False
    return True
"""

#Überprüft ob ein einzelner spec (Name + Version) existiert
def check_spec(name,version=-1):       
    out = shell('spack info '+str(name))
    #Falls keine Version vorhanden
    if version == -1:
        if out.find('Error')== -1:
            return True 
    elif out.find(version) != -1:
        return True         
    return False


#Prüft ob Installationsausdruck gültig ist (alle Specs)
def check_expr(expr):
    if check_expr_syn(expr)==True:
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
                        error_log(_[0]+'@'+_[1]+' existiert nicht',locals())
                        #Version existiert nicht
                        return False
                else:
                    if not check_spec(_[0]):
                        #Package existiert nicht
                        error_log(_[0]+' existiert nicht',locals())
                        return False
       
        return True
    #Syntaxfehler im Ausdruck
    return False

              
#Schreibt Script zum installieren der specs 
def install_spec(expr):
    partition=meta[0]
    node=meta[1]
    task=meta[2]
    cpus=meta[3]
    #Check ob angegebene Partition existiert
    if shell('sinfo -h -p '+partition).find(partition)==-1:        
        error_log('Partition: {} existiert nicht'.format(str(partition)),locals())
        #os.system('echo Partition: {} existiert nicht >> {}/install.err'.format(str(partition),loc),locals())
        return 
        
    slurm=''
    specs=''  
    
    #Slurmparameter für die Installation
    slurm='#!/bin/bash\n' \
    +'#SBATCH --nodes='+node+'\n' \
    +'#SBATCH --ntasks='+task+'\n' \
    +'#SBATCH --cpus-per-task='+cpus+'\n' \
    +'#SBATCH --partition='+partition+'\n' \
    +'#SBATCH --output={}/install.out\n'.format(loc) \
    +'#SBATCH --error={}/install.err\n\n'.format(loc) \
    +'source {}/share/spack/setup-env.sh\n'.format(meta[4])
    
    for e in expr:
        #Prüft ob breits identische spec installiert werden soll
        if specs.find(e)==-1:            
            #Prüft ob jeweils die einzelnen Komponenten der spec existieren
            if check_expr(e)==True:                   
                specs=specs+'srun spack install '+e+'\n'        
        
        #Dokumentieren des Fehlers
        else:
            #os.system('echo {} existiert nicht >> {}/install.err'.format(str(e),loc))
            error_log('{} does not exist'.format(str(e),loc),locals())
    
    if len(specs)==0:
        error_log('everything already installed',locals())
        #return os.system('echo bereits alles installiert >> {}/install.err'.format(str(e),loc))                
    else:        
        return str(slurm+specs)

#Write install.sh
with open('{}/install.sh'.format(loc),'w') as f:
    f.write(install_spec(expr))