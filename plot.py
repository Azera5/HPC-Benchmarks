import numpy as np
import os
import glob
import sys
import re
import math
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    from sb import file_w, error_log
except ImportError:
        pass

#############  hints regarding data structure  ##############
#                                                           #
#  values =[[metadata][results]]                            #  
#  [metadata] = [[titel][x-label][y-label]]                 #
#  [results]  = [[profile_1],[profile_2],...,[profile_n]]   #
#  [profile_x] = [[aggregated values],[iterations]]         #
#  [profile_result] = [[x1,...,xn],[y1,...,yn],...,label]   #
#                                                           #
#############################################################


#plot.py Path
LOC=str(os.path.dirname(os.path.abspath(__file__)))

values = [[],[]]
label_token = True
append_count = 0

#reads results
def read_values(TIMESTEMP,BENCH):
    clean_values()
    profiles = glob.glob('{}/projects/*'.format(LOC)+'*res@'+TIMESTEMP+'/*/')
    global values
    global append_count
    global label_token
    
    for name in profiles:    
        if BENCH=='osu':             
            read_osu(name,profiles.index(name),BENCH)

        elif BENCH=='hpl':            
            #meta-labels
            if label_token==True:
                values[0]=['HPL Benchmark','Gflops','']  
                
            read_hpl(name,profiles.index(name),BENCH,TIMESTEMP)
            
        
        elif BENCH=='hpcg':
            #meta-labels
            if label_token==True:
                values[0]=['HPCG Benchmark','Gflops','']            
            read_hpcg(name,profiles.index(name),BENCH,TIMESTEMP)    

        #reads aggregation-type
        aggregate_func=read_aggregate_func(name[1:-1],BENCH)           
        
                
        if append_count>0:
            #aggregates data across all iterations
            aggregated=aggregate_results(values[1][len(values[1])-1][1],aggregate_func)
            var=calc_variance(values[1][len(values[1])-1][1])
            
            values[1][len(values[1])-1][0][0]=aggregated[0]
            values[1][len(values[1])-1][0][1]=aggregated[1]
            values[1][len(values[1])-1][0][2]=var[1]          
            values[1][len(values[1])-1][0][3]='({}) [{}#{}]\n{}'.format(name[name.rfind(TIMESTEMP+'/')+len(TIMESTEMP)+1:-1],aggregate_func,len(values[1][len(values[1])-1][1]),values[1][len(values[1])-1][0][3])
            
            append_count=0    
        
        label_token=True    
  
    return values

def read_osu(profile,index,BENCH):
    global values
    global label_token
    global append_count
    iter_res = glob.glob(profile+'*.out')    
    
    for name in iter_res:        
        if os.stat(name).st_size == 0:
            continue

        if append_count==0:
            values[1].append([[[],[],[],[]],[]])
            append_count+=1
                
        values[1][len(values[1])-1][1].append([[],[]])
        with open(name,'r') as f:
            stringlist = f.readlines()         
            
        #reads results
        for line in stringlist:            
            #Abfangen leerer Zeile        
            if len(line) < 2:
                continue            
            
            #reads mpi-implementation         
            name_=profile[1:-1]
            with open('{}/configs/'.format(LOC)+BENCH+name_[name_.rfind('/'):]+'.txt','r') as f:
                values[1][len(values[1])-1][0][3]='{}'.format(f.readlines()[7].split()[0])
            
            #reads title
            if line.find('# OSU MPI ')!=-1 and label_token==True:
                values[0]=[line[line.find('# OSU MPI ')+10:-5]]                
                
            #reads axis-labels                
            elif line.find('#') != -1 and label_token==True:                    
                values[0].extend([x.lstrip() for x in line[2:-1].split(' ',1)])                
                if len(values[0])>2:
                    for _ in values[0][3:]:
                        values[0][2]+=' '+_
                    values[0]=values[0][:3]
                label_token=False 
         
            #reads results           
            elif line[0].isdigit() or line.split()[-1:][0].replace('.','').isdigit():   
            
                val = line.replace(' ',',',1).replace(' ','').split(',')               
                values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][1].append(float(val[1].replace('\n','')))
                
                if val[0]!='':
                    values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][0].append(float(val[0]))
                else:
                    values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][0].append(iter_res.index(name))
  
    #reorganizes axis labels for bar charts
    if len(values[1][0][0][0])==1:
        for _ in values[0][2:]:
            values[0][1]+=' '+_
        values[0][2]=''
        
    return values

def read_hpl(profile,index,BENCH,TIMESTEMP):
    global values
    global label_token
    global append_count
    iter_res = glob.glob(profile+'*.out')
    
    for name in iter_res:
        if os.stat(name).st_size == 0:
            continue
    
        if append_count==0:
            values[1].append([[[],[],[],[]],[]])
            append_count+=1
    
        values[1][len(values[1])-1][1].append([[],[]])        
        
        with open(name,'r') as f:
            stringlist = f.readlines() 
        
        #profile features: (N,P,Q)
        if label_token==True:
            slurm_param=read_slurm_param(name,TIMESTEMP)
            
            values[1][len(values[1])-1][0][3]='Ps {}; Qs {}; threshold {}Sizes (Ns) {}; Blocksizes (NBs) {}\nSlurm: nodes {}; cpus per task: {}\n'.format(
                stringlist[21].split()[2],
                stringlist[22].split()[2], 
                stringlist[41].split('than')[1].lstrip(),
                re.sub(' +', ' ',stringlist[18].split(':')[1].lstrip()[:-2]),
                re.sub(' +', ' ',stringlist[19].split(':')[1].lstrip()[:-2]),                
                slurm_param[0],
                slurm_param[1])                        
            
            label_token=False
        
        #results
        val=float(stringlist[46].split()[6])
        values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][0].append(float(index))
        values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][1].append(val)
       
    return values 

def read_hpcg(profile,index,BENCH,TIMESTEMP):
    global values
    global label_token
    global append_count
    iter_res = glob.glob(profile+'*.out')   
    
    for name in iter_res:       
        if os.stat(name).st_size == 0:
            continue
        
        if append_count==0:
            values[1].append([[[],[],[],[]],[]])            
            append_count+=1     
        
        values[1][len(values[1])-1][1].append([[],[]])
        
        with open(name,'r') as f:
            stringlist = f.readlines() 
                            
        #profile features: number of processes, threads per processe, problem-size; Slurm: nodes, cpus_per_task      
        if label_token==True:            
            problem_size='nA'
            
            slurm_param = read_slurm_param(name,TIMESTEMP)
            #reads problem-size from profil_cfg
            name_=profile[1:-1]
            with open('{}/configs/'.format(LOC)+BENCH+name_[name_.rfind('/'):]+'.txt','r') as f:
                _=f.readlines()[12].split()
                problem_size='{} {} {}'.format(_[0],_[1],_[2])
            
            values[1][len(values[1])-1][0][3]='size {}; processes {}; threads per proc. {}\nSlurm: nodes {}; cpus per task: {}\n'.format(problem_size,stringlist[4].split('=')[1][:-1],stringlist[5].split('=')[1][:-1],slurm_param[0],slurm_param[1])                        
            label_token=False
        
        #results
        val=float(stringlist[118].split('=')[1])        
        values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][0].append(float(index))
        values[1][len(values[1])-1][1][len(values[1][len(values[1])-1][1])-1][1].append(val)
    
    return values

def read_aggregate_func(profile,BENCH):
    name=profile[profile.rfind('/')+1:]
    #read function
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

def calc_variance(list):
    return np.var(list,axis=0).tolist()

#Min-Max-Normalisierung
def normalize_values(list):   
    min_=0
    max_=0
    max_=max(list)
    min_=min(list)    
    return [(i-min_)/(max_-min_) for i in list]

def read_slurm_param(name,TIMESTEMP):
    nodes='nA'
    cpus_per_task='nA'
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
    #labels=[]
    fig_typ=''
    
    if len(values[1])==0:
        error_log('plotting impossible, no results found')
        sys.exit('plotting impossible: no results found')
    
    #reorder of results for bar charts   
    if len(values[1][0][0][0])==1:
        values[1]=sorted(values[1].copy(), key=lambda row: (row[0][1]))
        fig_typ='barh'
            
    
    for v in values[1]:
        #function graphs        
        if len(v[0][0])>1:           
            p=plt.plot(v[0][0],v[0][1],label=v[0][3])  
            c=p[0].get_color()
            #Plots variance graph
            plt.plot(v[0][0],v[0][2],alpha=0.8,color=c,linestyle='dotted',linewidth=0.7)
            
               
        #horizontal bar chart
        else:
            plt.barh(v[0][3],v[0][1],label=v[0][3],xerr=v[0][2][0],capsize=4)
            
            
            
    #format figure layout (size, legend, position etc.)       
    fig_layout(fig,ax,fig_typ)
    ax_scale(BENCH,fig_typ)
    
    plt.savefig('{}plot.png'.format('{}/projects/{}_res@{}/'.format(LOC,BENCH,TIMESTEMP)))


def ax_scale(BENCH,fig_typ):
    if BENCH == 'osu':
        if fig_typ!='barh':
            plt.xscale('log', base=2)
            plt.yscale('log')
        else:
            plt.xscale('log',base=10)
    
    elif BENCH == 'hpl':
        plt.xscale('log',base=10)
        
    elif BENCH == 'hpcg':
        plt.xscale('log',base=10)

#format figure layout
def fig_layout(fig, ax, fig_typ):
    if fig_typ=='barh':
        fig.set_figwidth(14)
        fig.set_figheight(5+0.2*len(values[1]))   
        fig.subplots_adjust(left=0.1,right=0.6)

        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1],loc='upper left', bbox_to_anchor=(1, 1), fancybox=True, shadow=True, ncol=1)               
        plt.yticks(ticks=range(0,len(values[1])),labels=[_[0][3][1:_[0][3].find(')')] for _ in values[1]])        
    
    else:
        fig.set_figwidth(10)
        fig.subplots_adjust(right=0.7)
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1), fancybox=True, shadow=True)
        #plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fancybox=True, shadow=True)
        plt.grid(color='b', alpha=0.3, linestyle='dashed', linewidth=0.4)
    
    plt.title(values[0][0])
    plt.xlabel(values[0][1])
    plt.ylabel(values[0][2]) 

def clean_values():
    global values
    values = [[],[]]
#debugging-function will print each triple (x,y,label)
def plot_list():
    for val in values[1]:
        print(val[0])

def main():   
    TIMESTEMP=str(sys.argv[1])
    BENCH=str(sys.argv[2])
    run_plot(TIMESTEMP,BENCH)
    time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_w('{}/projects/{}_res@{}/plot.out'.format(LOC,BENCH,TIMESTEMP),'{} finished'.format(time),0)
    
if __name__ == "__main__":
    main()
    

