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


#path=glob.glob('{}/projects/*'.format(LOC)+TIMESTEMP+'*results*/*.out')[0]
#end=path.rfind(']')
#plot save path
path='{}/projects/{}_res@{}/'.format(LOC,BENCH,TIMESTEMP)
values = [[],[]]
label_token = True
append_count= 0

#Auslesen der Results
def read_values(TIMESTEMP,BENCH):
    profiles = glob.glob('{}/projects/*'.format(LOC)+'*res@'+TIMESTEMP+'/*/')
    global values
    global append_count
    
    for name in profiles:    
        if BENCH=='osu':
            values[1].append([[[],[],[]],[]])  
            read_osu(name)

        elif BENCH=='hpl':            
            #Meta-labels
            if label_token==True:
                values[0]=['HPL Benchmark','Gflops','']  
                
            read_hpl(name)
            
        
        elif BENCH=='hpcg':
            #Meta-labels
            if label_token==True:
                values[0]=['HPCG Benchmark','Gflops','']        
            
            values[1].append([[[],[],[]],[]])
            read_hpcg(name)    

        #reads function to aggregate the data
        aggregate_func=read_aggregate_func(name[1:-1])
           
        #aggregate data across all iterations
        aggregated=aggregate_results(values[1][len(values[1])-1][1],aggregate_func)
                
        if append_count>0:
            values[1][len(values[1])-1][0][0]=aggregated[0]
            values[1][len(values[1])-1][0][1]=aggregated[1]
            values[1][len(values[1])-1][0][2]+=' [{}#{}]'.format(aggregate_func,len(values[1][len(values[1])-1][1]))
            append_count=0     
    
    
    return values

def read_osu(profile):
    global values
    global label_token
    global append_count
    iter_res = glob.glob(profile+'*.out')    
    
    for name in iter_res:        
        if os.stat(name).st_size == 0:
            continue

        if append_count==0:
            values[1].append([[[],[],[]],[]])
            append_count+=1
                
        values[1][len(values[1])-1][1].append([[],[]])
        with open(name,'r') as f:
            stringlist = f.readlines()         
            
        #Auslesen der Results
        for line in stringlist:
            #Abfangen leerer Zeile
            if len(line) == 0:
                continue            
            
            #Auslesen MPI-Implementierung            
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

def read_hpl(profile):
    global values# = [[],[]]
    global label_token
    global append_count
    iter_res = glob.glob(profile+'*.out')
    
    for name in iter_res:
        if os.stat(name).st_size == 0:
            continue
    
        if append_count==0:
            values[1].append([[[],[],[]],[]])
            append_count+=1
    
        values[1][len(values[1])-1][1].append([[],[]])        
        
        with open(name,'r') as f:
            stringlist = f.readlines() 
        
        #Profilmerkmale (N,P,Q)        
        values[1][len(values[1])-1][0][2]='N {}\nP{}; Q{} ({})'.format(stringlist[18].split()[2],stringlist[21].split()[2],stringlist[22].split()[2],name[name.rfind('/')+5:-4])                        
        label_token=False
        
        #Results
        val=float(stringlist[46].split()[6].replace('.',''))
        values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][0].append(float(iter_res.index(name)))
        values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][1].append(val)
       
    return values 

def read_hpcg(profile):
    global values
    global label_token
    iter_res = glob.glob(profile+'*.out')
    nodes='?'
    cpus_per_task='?'
    for name in iter_res:       
        if os.stat(name).st_size == 0:
            continue
        
        if append_count==True:
            values[1].append([[[],[],[]],[]])
            append_count=False     
        
        values[1].append([[],[]])
        
        with open(name,'r') as f:
            stringlist = f.readlines() 
        
        #reads number of nodes and cpus-per-task from slurm script
        with open(name.replace('res','run').replace('.out','.sh')) as f:
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
        if label_token==True:   
            values[1][len(values[1])-1][0][2]='proc {}; thread {}\nnodes: {}, cpus: {}\n ({})'.format(stringlist[4].split('=')[1][:-1],stringlist[5].split('=')[1][:-1],nodes,cpus_per_task,name[name.rfind('/')+6:-4])                        
            label_token=False
        
        #Results
        val=float(stringlist[118].split('=')[1])
        values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][0].append(float(profile.index(name)))
        values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][1].append(val) 
    
    append_count=True
    return values

def read_aggregate_func(profile):
    name=profile[profile.rfind('/')+1:]
    #Read function
    with open('{}/configs/{}/{}.txt'.format(LOC,BENCH,name),'r') as f:
        aggregate_func=f.readlines()[2].split()[0]
    
    return aggregate_func

def aggregate_results(list, func):
    _=[]
    if func=='avg':        
        _=np.average(list,axis=0)
        
    elif func=='max':
        _=np.amax(list,axis=0)
    
    elif func=='min':
        _= np.amin(list,axis=0)
        
    return _.tolist()

#Plotten der Results
def run_plot(TIMESTEMP,BENCH):
    values = read_values(TIMESTEMP,BENCH)
    fig, ax = plt.subplots()    
    labels=['']
    
    #Neu sortieren der Results für Balkendiagramme
    """
    if len(values[1][0][0][0])==1:
        values[1]=sorted(values[1].copy(), key=lambda row: (row[1]))
    """

    for v in values[1]:
        #Graphen        
        if len(v[0][0])>1:            
            plt.plot(v[0][0],v[0][1],label=v[0][2])
            plt.legend()
            plt.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
        
        #Balkendiagramme
        else:
            plt.barh(v[0][2],v[0][1],label=v[0][2])
            plt.legend()
            fig.set_figwidth(10)     
 
    plt.title(values[0][0])
    plt.xlabel(values[0][1])
    plt.ylabel(values[0][2])        

    ax_scale()
    
    plt.savefig('{}plot.png'.format(path))



#Skalieren der Achsen   
def ax_scale():
    if BENCH == 'osu':
        plt.xscale('log', base=2)
        plt.yscale('log')
    
    elif BENCH == 'hpl':
        plt.xscale('log',base=10)
        
    elif BENCH == 'hpcg':
        plt.xscale('log',base=10)


    
#Debugfunktion zum printen jedes Tripels (x,y,label)
def plot_list():
    for val in values[1]:
        print(val[0])
   
#plot_list()
run_plot(TIMESTEMP,BENCH)