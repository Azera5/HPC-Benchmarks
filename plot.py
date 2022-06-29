import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import NullFormatter, FixedLocator
import os
import glob
import sys
import math

#Der Timestemp muss ohne [] angegeben werden!
timestemp=str(sys.argv[1])
bench=str(sys.argv[2])

#Pfad zum Speichern des Plots
path=glob.glob('projects/*'+timestemp+'*results*/*.out')[0]
end=path.rfind(']')
path=path[:end+1]

def read_values(timestemp,bench):
    values = [[],[]]
    
    #Alle Results eines Timestemps abarbeiten
    for name in glob.glob('projects/*'+timestemp+'*results*/*.out'):
        if os.stat(name).st_size == 0:
            continue
        values[1].append([[],[],[]])
        with open(name,'r') as f:
            stringlist = f.readlines()
        
        #Technische Grundlagen Auslesen (ACHTUNG OSU optimiert!)
        with open('configs/'+bench+'/'+os.path.basename(name).replace('.out', '.txt'),'r') as f:
            tech= f.readlines()[4].split()[0]           
            #Achtung Profinname muss Format *cfg_x.txt haben -> TODO ANPASSEN!
            values[1][len(values[1])-1][2]=tech+' ('+os.path.basename(name)[-9:-4]+')'
        
        #Auslesen der OSU Results
        if bench == 'osu':
            for line in stringlist:
                if stringlist.index(line) == 0:
                    continue
                elif stringlist.index(line) == 1:
                    values[0]= line[2:].replace(' ',',',1).replace(' ','').replace('\n','').split(',')
                    values[0].append(bench+' '+values[0][1])
                elif line[0].isdigit():                    
                    val = line.replace(' ',',',1).replace(' ','').split(',')
                    values[1][len(values[1])-1][0].append(float(val[0]))
                    values[1][len(values[1])-1][1].append(float(val[1].replace('\n','')))            
         
        #TODO
        if bench == 'hpl':
            continue
        
    return values

def forward(x):
    #print(x)    
    return x
    

def inverse(x):
    return x

def ax_lim(val,old, op):
    if op == 'min':
        if float(val) < float(old):
            return val
        else:
            return old
    if op == 'max':
        if float(val) > float(old):
            return val
        else:
            return old
    

def run_plot(timestemp,bench):
    values = read_values(timestemp,bench)    
    fig, ax = plt.subplots()
    xmin = float('inf')
    ymin = float('inf')
    xmax = -1
    ymax = -1 
    for v in values[1]:        
        xmin=ax_lim(v[0][0],xmin,'min')
        xmax=ax_lim(v[0][len(values[1][0][0])-1],xmax,'max')
        ymin=ax_lim(v[1][0],ymin,'min')
        ymax=ax_lim(v[1][len(values[1][0][1])-1],ymax,'max')       
        plt.plot(v[0],v[1],label=v[2])
        plt.legend()
        
    plt.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)    
    plt.title(values[0][2])
    plt.xlabel(values[0][0])
    plt.ylabel(values[0][1])
    #plt.autoscale(enable=False,axis='both',tight=None)
    #plt.axis([xmin,xmax,ymin,ymax])
    #plt.xscale('linear')
    #plt.yscale('log')
    plt.savefig(path+'/'+bench+'_plot.png')

#Debugfunktion zum printen jedes Tripels (x,y,label)
def plot_list():
    values = read_values(timestemp,bench)
    for val in values[1]:
        print(val)
   
#plot_list()
run_plot(timestemp,bench)