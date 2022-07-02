import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import sys


#Der Timestemp muss ohne [] angegeben werden!
timestemp=str(sys.argv[1])
bench=str(sys.argv[2])

#Pfad zum Speichern des Plots
path=glob.glob('projects/*'+timestemp+'*results*/*.out')[0]
end=path.rfind(']')
path=path[:end+1]

#Auslesen der Results
def read_values(timestemp,bench):
    values = [[],[]]
    profiles = glob.glob('projects/*'+timestemp+'*results*/*.out')
    #Alle Results eines Timestemps abarbeiten
    for name in profiles:
        if os.stat(name).st_size == 0:
            continue
        values[1].append([[],[],[]])
        with open(name,'r') as f:
            stringlist = f.readlines()             

        #Auslesen OSU (Results und Labels)
        if bench == 'osu':
            #Auslesen MPI-Implementierung
            with open('configs/'+bench+'/'+os.path.basename(name).replace('.out', '.txt'),'r') as f:                
                values[1][len(values[1])-1][2]='{} ({})'.format(f.readlines()[4].split()[0],name[name.rfind('\\')+5:-4])
            
            for line in stringlist:
                if stringlist.index(line) == 0:
                    continue
                
                #Achsen-Label Auslesen
                elif stringlist.index(line) == 1:
                    values[0]= line[2:].replace(' ',',',1).replace(' ','').replace('\n','').split(',')
                    values[0].append(bench+' '+values[0][1])
                
                #Results Auslesen
                elif line[0].isdigit():                    
                    val = line.replace(' ',',',1).replace(' ','').split(',')
                    values[1][len(values[1])-1][0].append(float(val[0]))
                    values[1][len(values[1])-1][1].append(float(val[1].replace('\n','')))
        
        #Auslesen HPL (Results und Labels)        
        if bench == 'hpl':
            #Profilmerkmale (N,P,Q)
            values[1][len(values[1])-1][2]='N {}\nP{}; Q{} ({})'.format(stringlist[18].split()[2],stringlist[21].split()[2],stringlist[22].split()[2],name[name.rfind('\\')+5:-4])                        
            
            #Results
            val=float(stringlist[46].split()[6].replace('.',''))
            values[1][len(values[1])-1][0].append(float(profiles.index(name)))
            values[1][len(values[1])-1][1].append(val)
            
            #Achsen-Label
            values[0]=['Gflops','','HPL Benchmark']
    
    return values

#Plotten der Results
def run_plot(timestemp,bench):
    values = read_values(timestemp,bench)    
    fig, ax = plt.subplots()    
    labels=['']
    
    #Neu sortieren der Results für Balkendiagramme
    if len(values[1][0][0])==1:
        values[1]=sorted(values[1].copy(), key=lambda row: (row[1]))   
    

    for v in values[1]:
        #Graphen
        if len(v[0])>1:
            plt.plot(v[0],v[1],label=v[2])
            plt.legend()
            plt.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
        
        #Balkendiagramme
        else:                       
            plt.barh(v[2],v[1],label=v[2])
            fig.set_figwidth(10)     
 
    plt.title(values[0][2])
    plt.xlabel(values[0][0])
    plt.ylabel(values[0][1])        

    ax_scale()
    
    plt.savefig(path+'/'+bench+'_plot.png')

#Skalieren der Achsen   
def ax_scale():
    if bench == 'osu':
        plt.xscale('log', base=2)
        plt.yscale('log')
    
    elif bench == 'hpl':
        plt.xscale('log',base=10)

    
#Debugfunktion zum printen jedes Tripels (x,y,label)
def plot_list():
    values = read_values(timestemp,bench)
    for val in values[1]:
        print(val)
   
#plot_list()
run_plot(timestemp,bench)