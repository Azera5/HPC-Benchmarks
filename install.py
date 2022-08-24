import sys
import os
import subprocess
import re

from sb import shell, check_expr_syn, error_log, LOC, FCOL, FEND, info_feed

#debugging
import traceback

slurm='#!/'+sys.argv[1].replace('$','\n').replace('_',' ')
expr=[_.split('$') for _ in sys.argv[2].split('#')]
menutxt=''
no_hint = True

def give_hint():
    global menutxt, no_hint
    if no_hint and info_feed:
        menutxt+=FCOL[7]+'<info>    '+FEND+'new error entries for install.py in log.txt'
        no_hint = False

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
    try:
        global menutxt   
        check_syn=check_expr_syn(expr,name)
        print(expr)
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
                            menutxt+='\n'+FCOL[6]+'<warning> '+FEND+'profile: '+FCOL[6]+name+FEND+' was deselected!\n          reason: {} doesn\'t exist!\n'.format(_[0]+'@'+_[1])+expr+FCOL[8]+'\n'+'^'.rjust(expr.find(_[0]+'@'+_[1])+1)+FEND+'\n'
                            error_log('can\'t install {}: package {} doesn\'t not exist!\n'.format(name,_[0]+'@'+_[1])+expr+'\n'+'^'.rjust(expr.find(_[0]+'@'+_[1])+1)+'\n')                        
                            give_hint()
                            return False
                    else:
                        if not check_spec(_[0]):
                            #Package existiert nicht
                            menutxt+='\n'+FCOL[6]+'<warning> '+FEND+'profile: '+FCOL[6]+name+FEND+' was deselected!\n          reason: {} doesn\'t exist!\n'.format(_[0])+expr+FCOL[8]+'\n'+'^'.rjust(expr.find(_[0])+1)+FEND+'\n'
                            error_log('can\'t install {}: package {} doesn\'t exist!\n'.format(name,_[0])+expr+'\n'+'^'.rjust(expr.find(_[0])+1)+'\n')
                            give_hint()
                            return False
            return True
        #Syntaxfehler im Ausdruck  
        menutxt+=check_syn
        give_hint()
        return False
    except Exception as exc:     
        error_log('', locals(), traceback.format_exc())
        give_hint()
        sys.exit(menutxt)
              
#Schreibt Script zum installieren der specs 
def install_spec(expr):
    try:
        global menutxt
        global slurm
        specs=''
        """
        partition=meta[0]
        node=meta[1]
        task=meta[2]
        cpus=meta[3]
        
        #Check ob angegebene Partition existiert
        if shell('sinfo -h -p '+partition).find(partition)==-1:        
            error_log('partition doesn\'t {} exist!'.format(str(partition)))
            #os.system('echo Partition: {} existiert nicht >> {}/install.err'.format(str(partition),LOC),locals())
            return 
            
        #slurm=meta
          
        
        #Slurmparameter für die Installation
        slurm='#!/bin/bash\n' \
        +'#SBATCH --nodes='+node+'\n' \
        +'#SBATCH --ntasks='+task+'\n' \
        +'#SBATCH --cpus-per-task='+cpus+'\n' \
        +'#SBATCH --partition='+partition+'\n' \
        +'#SBATCH --output={}/install.out\n'.format(LOC) \
        +'#SBATCH --error={}/install.err\n\n'.format(LOC) \
        +'source {}/share/spack/setup-env.sh\n'.format(meta[4])
        """
        for e in expr:
            #Prüft ob identische spec installiert werden soll
            if specs.find(e[0])==-1:            
                #Prüft ob jeweils die einzelnen Komponenten der spec existieren
                if check_expr(e[0],e[1])==True:                   
                    specs=specs+'srun spack install '+e[0]+'\n'                
        
        if len(specs)==0:        
            error_log('there is nothing to install')
            return ''             
                  
        return str(slurm+specs)
    except Exception as exc:     
        error_log('', locals(), traceback.format_exc()) 
        give_hint()
        sys.exit(menutxt)    

def main():
    try:
        #Write install.sh
        global menutxt       
        script_txt=install_spec(expr)
        if script_txt!='':
            with open('{}/install.sh'.format(LOC),'w') as f:
                f.write(script_txt)   
        sys.exit(menutxt)
        
    except Exception as exc:     
        error_log('', locals(), traceback.format_exc())
        give_hint()
        sys.exit(menutxt)
    
if __name__ == "__main__":
    main()



    
    