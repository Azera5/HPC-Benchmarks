import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import sys


############# Hinweis zur Datenstruktur values ##############
#                                                           #
#  values =[[metadata][results]]                            #  
#  [metadata] = [[titel][x-label][y-label]]                 #
#  [results]  = [[profile_1],[profile_2],...,[profile_n]]   #
#  [profile_x] = [[aggregated values],[iterations]]         #
#  [profile_result] = [[x1,...,xn],[y1,...,yn],...,[label]] #
#                                                           #
#############################################################


#Der Timestemp muss ohne [] angegeben werden!
TIMESTEMP=str(sys.argv[1])
BENCH=str(sys.argv[2])

#plot.py Path
LOC=str(os.path.dirname(os.path.abspath(__file__)))

#Pfad zum Speichern des Plots
#path=glob.glob('{}/projects/*'.format(LOC)+TIMESTEMP+'*results*/*.out')[0]
#end=path.rfind(']')
path='{}/projects/*'.format(LOC)+TIMESTEMP+'*results*/'
values = [[],[]]
label_token = True

#Auslesen der Results
def read_values(TIMESTEMP,BENCH):
    profiles = glob.glob('{}/projects/*'.format(LOC)+'*res@'+TIMESTEMP+'/*/')
    global values
    
    if BENCH=='osu':
        values[1].append([[[],[],[]],[]])        
        for name in profiles:
            read_osu(name)                       
            name_=name[1:-1]
            #Read function
            with open('{}/projects/{}_run@{}/1#'.format(LOC,BENCH,TIMESTEMP)+name_[name_.rfind('/')+1:]+'.sh','r') as f:
                aggregate_func=f.readlines()[2].split()[0]
            
            aggregated=aggregate_results(values[1][len(values[1])-1][1],aggregate_func)
            values[1][len(values[1])-1][0][0]=aggregated[0]
            values[1][len(values[1])-1][0][1]=aggregated[1]
            
    elif BENCH=='hpl':
        for name in profiles:
            read_hpl(name)
        
        
    elif BENCH=='hpcg':
        for name in profiles:
            read_hpcg(name)    
   
    print(values)
    return values

def read_osu(profile):
    global values
    global label_token
    iter_res = glob.glob(profile+'*.out')    
    
    for name in iter_res:        
        if os.stat(name).st_size == 0:
            continue
                
        values[1][len(values[1])-1][1].append([[],[]])
        with open(name,'r') as f:
            stringlist = f.readlines()         
            
        #Auslesen der Results
        for line in stringlist:
            #Abfangen leerer Zeile
            if len(line) == 0:
                continue            
            
            #Auslesen MPI-Implementierung
            if label_token ==True:
                name_=profile[1:-1]
                with open('{}/configs/'.format(LOC)+'osu'+name_[name_.rfind('/'):]+'.txt','r') as f:
                    values[1][len(values[1])-1][0][2]='{} ({})'.format(f.readlines()[7].split()[0],name_[name_.rfind('/')+1:])
            
            #Titel Auslesen
            if line.find('# OSU MPI ')!=-1 and label_token==True:
                values[0]=[line[line.find('# OSU MPI ')+10:-5]]                
                
            #Achsen-Label Auslesen                
            elif line.find('#') != -1 and label_token==True:                    
                values[0].extend([x.lstrip() for x in line[2:-1].split(' ',1)])
                label_token=False                
                
            #Ergebnisse Auslesen
            elif line[0].isdigit():                    
                val = line.replace(' ',',',1).replace(' ','').split(',')                
                values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][0].append(float(val[0]))
                values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][1].append(float(val[1].replace('\n','')))

    return values

def read_hpl(profiles):
    values = [[],[]]
    for name in profiles:
        if os.stat(name).st_size == 0:
            continue
        values[1].append([[],[],[]])
        
        with open(name,'r') as f:
            stringlist = f.readlines() 
        
        #Profilmerkmale (N,P,Q)
        values[1][len(values[1])-1][2]='N {}\nP{}; Q{} ({})'.format(stringlist[18].split()[2],stringlist[21].split()[2],stringlist[22].split()[2],name[name.rfind('/')+5:-4])                        
           
        #Results
        val=float(stringlist[46].split()[6].replace('.',''))
        values[1][len(values[1])-1][0].append(float(profiles.index(name)))
        values[1][len(values[1])-1][1].append(val)
            
        #Achsen-Label
        values[0]=['HPL Benchmark','Gflops','']
            
    return values 

def read_hpcg(profiles):
    values = [[],[]]
    nodes='?'
    cpus_per_task='?'
    for name in profiles:
        if os.stat(name).st_size == 0:
            continue
        values[1].append([[],[],[]])
        
        with open(name,'r') as f:
            stringlist = f.readlines() 
        
        #reads number of nodes and cpus-per-task from slurm script
        with open(name.replace('results','run').replace('.out','.sh')) as f:
            for line_index, line in enumerate(f):
                if '--nodes=' in line:
                    nodes=line.split('=')[1][:-1]                    
                
                elif '-N ' in line:
                    nodes=line.split()[1][:-1]
                
                elif '--cpus-per-task=' in line:
                    cpus_per_task=line.split('=')[1][:-1]
                
                elif '-c ' in line:
                    cpus_per_task=line.split()[1][:-1]
                    
        #Profilmerkmale Number of processes, threads and nodes, cpus_per_task      
        values[1][len(values[1])-1][2]='proc {}; thread {}\nnodes: {}, cpus: {}\n ({})'.format(stringlist[4].split('=')[1][:-1],stringlist[5].split('=')[1][:-1],nodes,cpus_per_task,name[name.rfind('/')+6:-4])                        
           
        #Results
        val=float(stringlist[118].split('=')[1])
        values[1][len(values[1])-1][0].append(float(profiles.index(name)))
        values[1][len(values[1])-1][1].append(val)
            
        #Achsen-Label
        values[0]=['HPCG Benchmark','Gflops','']
        
    return values

#Plotten der Results
def run_plot(TIMESTEMP,BENCH):
    values = read_values(TIMESTEMP,BENCH)
    fig, ax = plt.subplots()    
    labels=['']
    
    #Neu sortieren der Results für Balkendiagramme
    if len(values[1][0][0][0])==1:
        values[1]=sorted(values[1].copy(), key=lambda row: (row[1]))
    

    for v in values[1]:
        #Graphen
        if len(v[0][0][0])>1:
            plt.plot(v[0][0],v[0][1],label=v[0][2])
            plt.legend()
            plt.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
        
        #Balkendiagramme
        else:                       
            plt.barh(v[0][2],v[0][1],label=v[0][2])
            fig.set_figwidth(10)     
 
    plt.title(values[0][0])
    plt.xlabel(values[0][1])
    plt.ylabel(values[0][2])        

    ax_scale()
    
    plt.savefig(path+'/'+'plot.png')



#Skalieren der Achsen   
def ax_scale():
    if BENCH == 'osu':
        plt.xscale('log', base=2)
        plt.yscale('log')
    
    elif BENCH == 'hpl':
        plt.xscale('log',base=10)
        
    elif BENCH == 'hpcg':
        plt.xscale('log',base=10)

def aggregate_results(list, function):
    return list[0]
    
#Debugfunktion zum printen jedes Tripels (x,y,label)
def plot_list():
    values = read_values(TIMESTEMP,BENCH)
    for val in values[1]:
        print(val)
   
#plot_list()
run_plot(TIMESTEMP,BENCH)