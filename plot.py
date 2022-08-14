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
#  [profile_result] = [[x1,...,xn],[y1,...,yn],...,label] #
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
    global label_token
    
    for name in profiles:    
        if BENCH=='osu':
            #values[1].append([[[],[],[]],[]])  
            read_osu(name,profiles.index(name))

        elif BENCH=='hpl':            
            #Meta-labels
            if label_token==True:
                values[0]=['HPL Benchmark','Gflops','']  
                
            read_hpl(name,profiles.index(name))
            
        
        elif BENCH=='hpcg':
            #Meta-labels
            if label_token==True:
                values[0]=['HPCG Benchmark','Gflops','']        
            
            #values[1].append([[[],[],[]],[]])
            read_hpcg(name,profiles.index(name))    

        #reads function to aggregate the data
        aggregate_func=read_aggregate_func(name[1:-1])
           
        #aggregate data across all iterations
        aggregated=aggregate_results(values[1][len(values[1])-1][1],aggregate_func)
                
        if append_count>0:
            values[1][len(values[1])-1][0][0]=aggregated[0]
            values[1][len(values[1])-1][0][1]=aggregated[1]
            values[1][len(values[1])-1][0][2]='({}) [{}#{}]\n{}'.format(name[name.rfind(TIMESTEMP+'/')+len(TIMESTEMP)+1:-1],aggregate_func,len(values[1][len(values[1])-1][1]),values[1][len(values[1])-1][0][2])
            append_count=0    
        
        label_token=True    
  
    return values

def read_osu(profile,index):
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
            with open('{}/configs/'.format(LOC)+BENCH+name_[name_.rfind('/'):]+'.txt','r') as f:
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

def read_hpl(profile,index):
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
        if label_token==True:
            values[1][len(values[1])-1][0][2]='N {}\nP{}; Q{} ({})'.format(stringlist[18].split()[2],stringlist[21].split()[2],stringlist[22].split()[2],name[name.rfind('#')+1:-4])                        
            label_token=False
        
        #Results
        val=float(stringlist[46].split()[6].replace('.',''))
        values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][0].append(float(index))
        values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][1].append(val)
       
    return values 

def read_hpcg(profile,index):
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
                            
        #Profilmerkmale number of processes, threads per processe, problem size; Slurm: nodes, cpus_per_task      
        if label_token==True:            
            problem_size='?'
            
            slurm_param = read_slurm_param(name)
            #readas problem size from profil_cfg
            name_=profile[1:-1]
            with open('{}/configs/'.format(LOC)+BENCH+name_[name_.rfind('/'):]+'.txt','r') as f:
                _=f.readlines()[12].split()
                problem_size='{} {} {}'.format(_[0],_[1],_[2])
            
            values[1][len(values[1])-1][0][2]='size {}; processes {}; threads per proc. {};\nSlurm: nodes {}; cpus per task: {}'.format(problem_size,stringlist[4].split('=')[1][:-1],stringlist[5].split('=')[1][:-1],slurm_param[0],slurm_param[1])                        
            label_token=False
        
        #Results
        val=float(stringlist[118].split('=')[1])        
        values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][0].append(float(index))
        values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][1].append(val)
    
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

def read_slurm_param(name):
    nodes='?'
    cpus_per_task='?'
    #reads number of nodes and cpus-per-task from slurm script            
    with open(name[:name.find(TIMESTEMP+'/')+len(TIMESTEMP)].replace('res','run')+name[name.rfind('/'):].replace('.out','.sh')) as f:
        for line_index, line in enumerate(f):
            if '--nodes=' in line:
                nodes=line.split('=')[1][:-1]                    
                
            elif '-N ' in line:
                nodes=line.split()[1][:-1]
                
            elif '--cpus-per-task=' in line:
                cpus_per_task=line.split('=')[1][:-1]
                
            elif '-c ' in line:
                cpus_per_task=line.split()[1][:-1]
    return [nodes,cpus_per_task]

#plots the results
def run_plot(TIMESTEMP,BENCH):
    values = read_values(TIMESTEMP,BENCH)
    fig, ax = plt.subplots()    
    labels=['']
    fig_typ=''
    
    #reorder of results for bar charts   
    if len(values[1][0][0][0])==1:
        values[1]=sorted(values[1].copy(), key=lambda row: (row[0][1]))
        fig_typ='barh'
    
    
    for v in values[1]:
        #function graphs        
        if len(v[0][0])>1:            
            plt.plot(v[0][0],v[0][1],label=v[0][2])
            
        #horizontal bar chart
        else:
            plt.barh(v[0][2],v[0][1],label=v[0][2])
            
            
            
    #formats the figure layout (size, legend, position etc.)       
    fig_layout(fig,ax,fig_typ)
    ax_scale()
    
    plt.savefig('{}plot.png'.format(path))


def ax_scale():
    if BENCH == 'osu':
        plt.xscale('log', base=2)
        plt.yscale('log')
    
    elif BENCH == 'hpl':
        plt.xscale('log',base=10)
        
    elif BENCH == 'hpcg':
        plt.xscale('log',base=10)

#Formats the figure layout
def fig_layout(fig, ax, fig_typ):
    if fig_typ=='barh':
        fig.set_figwidth(13)
        fig.set_figheight(5+0.2*len(values[1]))   
        fig.subplots_adjust(left=0.1,right=0.65)

        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1],loc='upper left', bbox_to_anchor=(1, 1), fancybox=True, shadow=True, ncol=1)
               
        plt.yticks(ticks=range(0,len(values[1])),labels=[_[0][2][1:_[0][2].find(')')] for _ in values[1]])        
    
    
    plt.legend()
    plt.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
    
    plt.title(values[0][0])
    plt.xlabel(values[0][1])
    plt.ylabel(values[0][2]) 
    
#Debugfunction will be print each triple (x,y,label)
def plot_list():
    for val in values[1]:
        print(val[0])

def main():   
    #plot_list()
    run_plot(TIMESTEMP,BENCH)
    
if __name__ == "__main__":
    main()