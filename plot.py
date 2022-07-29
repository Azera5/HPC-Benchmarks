import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import sys


#Der Timestemp muss ohne [] angegeben werden!
timestemp=str(sys.argv[1])
bench=str(sys.argv[2])

#plot.py Path
loc=str(os.path.dirname(os.path.abspath(__file__)))

#Pfad zum Speichern des Plots
path=glob.glob('{}/projects/*'.format(loc)+timestemp+'*results*/*.out')[0]
end=path.rfind(']')
path=path[:end+1]

#Auslesen der Results
def read_values(timestemp,bench):
    values = [[],[]]
    profiles = glob.glob('{}/projects/*'.format(loc)+timestemp+'*results*/*.out')
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
            with open('{}/configs/'.format(loc)+bench+'/'+os.path.basename(name).replace('.out', '.txt'),'r') as f:
                values[1][len(values[1])-1][2]='{} ({})'.format(f.readlines()[4].split()[0],name[name.rfind('/')+5:-4])
            
            #Auslesen der Results
            for line in stringlist:
                #Abfangen leerer Zeile
                if len(line) == 0:
                    continue
                
                #Titel Auslesen
                elif line.find('# OSU MPI ')!=-1:
                    values[0]=[line[line.find('# OSU MPI ')+10:-5]]
                
                #Achsen-Label Auslesen                
                elif line.find('#') != -1:                    
                    values[0].extend([x.lstrip() for x in line[2:-1].split(' ',1)])                                     
                
                #Ergebnisse Auslesen
                elif line[0].isdigit():                    
                    val = line.replace(' ',',',1).replace(' ','').split(',')
                    values[1][len(values[1])-1][0].append(float(val[0]))
                    values[1][len(values[1])-1][1].append(float(val[1].replace('\n','')))
        
        #Auslesen HPL (Results und Labels)        
        if bench == 'hpl':
            #Profilmerkmale (N,P,Q)
            values[1][len(values[1])-1][2]='N {}\nP{}; Q{} ({})'.format(stringlist[18].split()[2],stringlist[21].split()[2],stringlist[22].split()[2],name[name.rfind('/')+5:-4])                        
           
            #Results
            val=float(stringlist[46].split()[6].replace('.',''))
            values[1][len(values[1])-1][0].append(float(profiles.index(name)))
            values[1][len(values[1])-1][1].append(val)
            
            #Achsen-Label
            values[0]=['HPL Benchmark','Gflops','']    
    
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
 
    plt.title(values[0][0])
    plt.xlabel(values[0][1])
    plt.ylabel(values[0][2])        

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