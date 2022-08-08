import sys
import os
import subprocess
import re

from sb import shell, check_expr_syn, error_log, LOC, FCOL, FEND, menutxt


meta=sys.argv[1].split('#')
expr=[_.split('$') for _ in sys.argv[2].split('#')]
menutxt=''

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
def check_expr(expr,name):
    global menutxt    
    check_syn=check_expr_syn(expr,name)
    if check_syn=='True':
        arr = expr.split('^')       
        
        for spec in arr:
            s=spec.split('%')
            
            #Untersuchung von einzelnem Package und Version
            for _ in s:            
                """ Wird in check_expr_syn rausgefiltert
                if _[0][:0]=='@' or _[0]=='':                    
                    menutxt+='\n'+FCOL[6]+'<warning> '+FEND+'profile: '+FCOL[6]+name+FEND+' was deselected! <spec error>: packagename is missing\n'+expr+FCOL[8]+'\n'+'^'.rjust(shift+2)+'^'.rjust(expr.find('^',shift+2,len(expr))-1)+FEND+'\n'
                    error_log('<spec error> at {}: packagename is missing\n'.format(name)+expr+'\n'+'^'.rjust(shift+2)+'^'.rjust(expr.find('^',shift+2,len(expr))-1)+'^'.rjust(expr.find('^',shift+2,len(expr))-1)+'\n',locals())
                    return False               
                """
                _=_.split('@')                
                if len(_) > 1:
                    if not check_spec(_[0],_[1]):
                        #Version existiert nicht
                        menutxt+='\n'+FCOL[6]+'<warning> '+FEND+'profile: '+FCOL[6]+name+FEND+' was deselected! <spec error>: {} does not exist\n'.format(_[0]+'@'+_[1])+expr+FCOL[8]+'\n'+'^'.rjust(expr.find(_[0]+'@'+_[1])+1)+FEND+'\n'
                        error_log('<spec error> at {}: version {} does not exist\n'.format(name,_[0]+'@'+_[1])+expr+'\n'+'^'.rjust(expr.find(_[0]+'@'+_[1])+1)+'\n',locals())                        
                        return False
                else:
                    if not check_spec(_[0]):
                        #Package existiert nicht
                        menutxt+='\n'+FCOL[6]+'<warning> '+FEND+'profile: '+FCOL[6]+name+FEND+' was deselected! <spec error>: {} does not exist\n'.format(_[0])+expr+FCOL[8]+'\n'+'^'.rjust(expr.find(_[0])+1)+FEND+'\n'
                        error_log('<spec error> at {}: package {} does not exist\n'.format(name,_[0])+expr+'\n'+'^'.rjust(expr.find(_[0])+1)+'\n',locals())
                        return False
       
        return True
    #Syntaxfehler im Ausdruck  
    menutxt+=check_syn
    return False

              
#Schreibt Script zum installieren der specs 
def install_spec(expr):
    global menutxt
    partition=meta[0]
    node=meta[1]
    task=meta[2]
    cpus=meta[3]
    #Check ob angegebene Partition existiert
    if shell('sinfo -h -p '+partition).find(partition)==-1:        
        error_log('Partition: {} existiert nicht'.format(str(partition)),locals())
        #os.system('echo Partition: {} existiert nicht >> {}/install.err'.format(str(partition),LOC),locals())
        return 
        
    slurm=''
    specs=''  
    
    #Slurmparameter für die Installation
    slurm='#!/bin/bash\n' \
    +'#SBATCH --nodes='+node+'\n' \
    +'#SBATCH --ntasks='+task+'\n' \
    +'#SBATCH --cpus-per-task='+cpus+'\n' \
    +'#SBATCH --partition='+partition+'\n' \
    +'#SBATCH --output={}/install.out\n'.format(LOC) \
    +'#SBATCH --error={}/install.err\n\n'.format(LOC) \
    +'source {}/share/spack/setup-env.sh\n'.format(meta[4])
    
    for e in expr:
        #Prüft ob identische spec installiert werden soll
        if specs.find(e[0])==-1:            
            #Prüft ob jeweils die einzelnen Komponenten der spec existieren
            if check_expr(e[0],e[1])==True:                   
                specs=specs+'srun spack install '+e[0]+'\n'                
    
    if len(specs)==0:        
        error_log('There is nothing to install',locals())
        return ''             
              
    return str(slurm+specs)

def main():
    #Write install.sh
    global menutxt        
    script_txt=install_spec(expr)
    if script_txt!='':
        with open('{}/install.sh'.format(LOC),'w') as f:
            f.write(script_txt)   
    
    sys.exit(menutxt)
    
if __name__ == "__main__":
    main()



    
    