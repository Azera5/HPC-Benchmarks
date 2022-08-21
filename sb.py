import os
import os.path
import subprocess
import datetime
import inspect
import shutil
import time
import math
import fnmatch
import re
import argparse
import glob
from os.path import exists 
from argparse import RawTextHelpFormatter
from plot import read_values, clean_values, values

#debugging
import sys
from io import StringIO
import traceback

#these are just simple name-reservations/declarations (*not* initializations), otherwise some function definitions would have to be changed
LOC, SPACK_XPTH, error_stack, cfg_profiles, form_factor_menu, t_width, ml, mr, menutxt, dbg, menu_ctrl, full_bin_paths, auto_space_normalization, SPACK_SEARCH_ROOT, termination_logging, path_logging, info_feed, test_only, check_python_setting = (0,)*19

"""
Initialization of Colorcodes 
"""

#############################
### formatting text color ###
#############################
"""
0 = grau '\33[90m'
1 = schwarz '\33[30m'
2 = weiß '\33[37m'
3 = weiß2 '\33[97m'
4 = grün '\33[32m'
5 = grün2 '\33[92m'
6 = gelb '\33[33m'
7 = gelb2 '\33[93m'
8 = rot '\33[31m'
9 = rot2 '\33[91m'
10 = blau '\33[34m'
11 = blau2 '\33[94m'
12 = violett '\33[35m'
13 = violett2 '\33[95m'
14 = beige/türkis '\33[36m'
15 = beige/türkis2 '\33[96m'
"""
#idea: disabled color support <=> every entry in FCOL is an empty string; if we plan to re-enable the color support wie simply make FCOL equal to FCOL_M again
FCOL = [ '\33[90m', '\33[30m', '\33[37m', '\33[97m', '\33[32m', '\33[92m', '\33[33m', '\33[93m', '\33[31m', '\33[91m', '\33[34m', '\33[94m', '\33[35m', '\33[95m', '\33[36m', '\33[96m' ]
FCOL_M = [ '\33[90m', '\33[30m', '\33[37m', '\33[97m', '\33[32m', '\33[92m', '\33[33m', '\33[93m', '\33[31m', '\33[91m', '\33[34m', '\33[94m', '\33[35m', '\33[95m', '\33[36m', '\33[96m' ]

#############################
#formatting background color#
#############################
"""
0 = grau '\33[100m'
1 = schwarz '\33[40m'
2 = weiß '\33[47m'
3 = weiß2 '\33[107m'
4 = grün '\33[42m'
5 = grün2 '\33[102m'
6 = gelb '\33[43m'
7 = gelb2 '\33[103m'
8 = rot '\33[41m'
9 = rot2 '\33[101m'
10 = blau '\33[44m'
11 = blau2 '\33[104m'
12 = violett '\33[45m'
13 = violett2 '\33[105m'
14 = beige/türkis '\33[46m'
15 = beige/türkis2 '\33[106m'
"""
#idea: analogous to FCOL
FBGR = [ '\33[100m', '\33[40m', '\33[47m', '\33[107m', '\33[42m', '\33[102m', '\33[43m', '\33[103m', '\33[41m', '\33[101m', '\33[44m', '\33[104m', '\33[45m', '\33[105m', '\33[46m', '\33[106m' ]
FBGR_M = [ '\33[100m', '\33[40m', '\33[47m', '\33[107m', '\33[42m', '\33[102m', '\33[43m', '\33[103m', '\33[41m', '\33[101m', '\33[44m', '\33[104m', '\33[45m', '\33[105m', '\33[46m', '\33[106m' ]

#############################
#####  formatting font  #####
#############################
"""
0 = dick (bold) '\33[1m'
1 = kursiv (italic) '\33[3m'
2 = unterstr. (url) '\33[4m'
3 = markiert '\33[7m'
4 = blinkend '\33[5m'
5 = blinkend2 '\33[6m'
ggf. nicht alle unterstützt! (z.B. blinkend & kursiv)
"""
#idea: analogous to FCOL
FORM = [ '\33[1m', '\33[3m', '\33[4m', '\33[7m', '\33[5m', '\33[6m' ]
FORM_M = [ '\33[1m', '\33[3m', '\33[4m', '\33[7m', '\33[5m', '\33[6m' ]

#stop formatting
FEND = '\33[0m'


"""
Command-Line-Parameter
"""
def cl_arg():
    global cfg_profiles, menu_ctrl, test_only
    
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
    parser.add_argument('-i','--install',nargs='+',type=str,help=''+
    FCOL[15]+'<Benchmark> <cfg>,<cfg>,...,<cfg>\n'+FEND+ 
    FCOL[2]+'     e.g.: -i hpl 1,3-4,example\n\n'+FEND+    
    FCOL[15]+'all: Install all benchmarks or profiles\n'+FEND+    
    FCOL[2]+'     e.g.: -i all\n'+
    '           -i osu all\n\n'+FEND)
    
    parser.add_argument('-r','--run',nargs='+',type=str,help=''+
    FCOL[15]+'hpl <cfg>,<cfg>,...,<cfg>\n'+FEND+
    FCOL[2]+'     e.g.: -r hpl 1,3-4,Test1\n'+
    '           -r hpl all <=> -r hpl\n\n'+
    FCOL[15]+'osu_<test>_<flags> <cfg>,<cfg>,...,<cfg> \n'+FEND+
    FCOL[7]+'     tests: {latency, bw, bcast, barrier, allreduce}\n'+FEND+
    FCOL[2]+'     e.g.: -r osu_latency 1,3-4,example\n'+
    FCOL[2]+'           -r osu_latency_i500:1000_x200 1,3-4,example\n'+
    '           -r osu_latency all <=> -r osu_latency\n\n'+
    FCOL[15]+'hpcg <cfg>,<cfg>,...,<cfg>\n'+FEND+
    FCOL[2]+'     e.g.: -r hpcg 1,3-4,Test1\n'+
    '           -r hpcg all <=> -r hpcg\n\n'+FEND)
    
    parser.add_argument('-w','--write',nargs='+',type=str,help=''+
    FCOL[15]+'works very similar to -r/--run\n'+FEND+
    FCOL[7]+'key difference: '+FEND+'there\'s no final script submission!\n'+
    FCOL[2]+'     e.g.: -w hpl 1,3-4,Test1\n'+
    '           etc.\n\n'+FEND)
    
    parser.add_argument('-t','--test',nargs='+',type=str,help=''+
    FCOL[15]+'works very similar to -r/--run\n'+FEND+ 
    FCOL[7]+'key difference: '+FEND+'creates *non-persistent* dummy projects and prints the error stack!\n'+
    FCOL[2]+'     e.g.: -t hpl 1,3-4,Test1\n'+
    '           etc.\n\n'+FEND+
    FCOL[15]+'<info>    '+FEND+'clean up is »rm -r ...«-based respective to sub-directories named like »*@*[dummy]«,\n'+
    'please be cautious with naming data in the project directory this way\n\n')
    
    parser.add_argument('-p','--profiles',nargs=1,type=str,help=''+
    FCOL[15]+'shows the availability of profiles for specific benchmarks\n'+FEND+  
    FCOL[2]+'     e.g.: -p hpl\n'+FEND)
    
    parser.add_argument('-l','--load',nargs=1,type=str,help=''+
    FCOL[15]+'shows how a specific profile set is loaded (Debugging)\n'+FEND+  
    FCOL[2]+'     e.g.: -l hpl\n'+FEND)
    
    parser.add_argument('-c','--clean',nargs=1,type=str,help=''+
    FCOL[15]+'helps to handle data clutter\n'+FEND+  
    '  '+FCOL[7]+'projects:'+FEND+' removes projects folder\n'+
    '  '+FCOL[7]+'install:'+FEND+'  removes all install scripts\n'+
    '  '+FCOL[7]+'log:'+FEND+' cleans log.txt (error-log file)\n' +
    '  '+FCOL[7]+'mem:'+FEND+' resets mem.txt (run time variables)\n'+
    '  '+FCOL[7]+'all:'+FEND+' cleans projects folder, install scripts and log.txt,'+FCOL[13]+' not mem.txt!\n'+FEND+     
    '     '+FCOL[2]+'e.g.: -c projects\n'+
    '           -c all\n'+FEND+
    FCOL[15]+'<info>    '+FEND+'please consider saving relevant project results beforehand\n')
    
    
    args= parser.parse_args()
    
    #Clean files
    if args.clean:       
        return print(clean(args.clean[0]))
      
    #Install Benchmarks
    if args.install:
        expr=[]
        #we want to install all profiles of all benchmarks
        if args.install[0]=='all':
            #expr=get_all_specs('hpl')+get_all_specs('osu') <--- Überholt!
            for id in BENCH_ID_LIST:
                if id==MISC_ID:
                    continue
                get_cfg(tag_id_switcher(id))
                expr+=get_all_specs(tag_id_switcher(id))   
        
        #we want to install profiles for specific benchmarks...  
        else:            
            #...but all profiles
            if len(args.install)<2 or args.install[1]== 'all':
                get_cfg(args.install[0])
                expr=get_all_specs(args.install[0]) 
            
            #we want to install specific profiles for specific benchmarks
            else:
                names=farg_to_list(args.install[1],args.install[0])                
                get_cfg(args.install[0],args.install[1])               
                expr=get_all_specs(args.install[0],names)
                   
        script_pth=install_spec(expr)
        
        if menutxt !='':
            print(menutxt)
        
        print(script_pth)
    
    #this mode writes the scripts *and* submitts them directly to SLURM
    if args.run:
        pth=comline_run_helper(args.run)
        #possible warnings etc.
        print(menutxt)
        #we're submitting our scripts
        
        if pth!='-1':        
            print(FCOL[4]+shell(str('sbatch '+pth[pth.find('/'):pth.find('.sh')+3]))+FEND)

    #this mode *only* writes the scripts
    if args.write:
        pth=comline_run_helper(args.write)      
        #possible warnings etc.
        print(menutxt)
    
    #this mode simulates script writing for an error-analysis
    if args.test:
        test_only=True
        pth=comline_run_helper(args.test)
        #possible warnings etc.
        print(show_err_stack())
        clean_dummy_projects()
    
    #this mode *only* loads profiles and prints them afterwards
    if args.load:
        get_cfg(args.load[0])
        print(config_out(tag_id_switcher(args.load[0])))
    
    #this mode shows the availability of profiles for specific benchmarks
    if args.profiles:
        get_cfg(args.profiles[0])
        left_size=t_width-len(ml)
        txt='\n\n'+ml+FCOL[15]+'--- found {} profiles ---'.format(args.profiles[0])+FEND+'\n'+ml
        for name in avail_pkg(tag_id_switcher(args.profiles[0])):
                if left_size<len(name+ml):
                    txt+='\n'+ml
                    left_size=t_width-len(ml)
                txt+=FORM[0]+name+FEND+ml
                left_size-=len(name+ml)
        print(txt+'\n')
        
    #Start via Menu   
    if not args.install and not args.test and not args.load and not args.profiles and not args.write and not args.run and not args.clean:
        menu_ctrl=True
        clear()
        for id in BENCH_ID_LIST:
            if id==MISC_ID:
                continue
            get_cfg(tag_id_switcher(id))
        menu()
    
    


"""
Wichtige Vorlauf-Funktionen
""" 

#Bestimmt die genutzten Pfade
def evaluate_paths():
    global initm, evaluate_paths_t
    timestart = time.time()
    
    #preparation of path- & info-arrays
    for id in BENCH_ID_LIST:
        #we have one config directory per benchmark
        BENCH_PTHS.append('empty')
        pkg_info.append(['empty', 'empty', 'empty', 'empty'])
    
    #path evaluation
    for id in BENCH_ID_LIST:
        if id==MISC_ID:
            pth = LOC+'/configs/'
        else:
            pth = LOC+'/configs/{}/'.format(tag_id_switcher(id))
        BENCH_PTHS[id]=pth
        #loadprogress('')
    
    evaluate_paths_t=time.time()-timestart

#no timestats because of the integration into path evaluation
def extensive_spack_evaluation():
    global SPACK_XPTH
    
    test_list = str(shell('find {} -executable -name spack -path \'*/spack/bin/*\''.format(SPACK_SEARCH_ROOT))).replace('\n',' ').split()
    
    git_loc = shell('whereis git').split('git:')[1]
    if (git_loc.isspace==True or len(git_loc)<2):
        git_warning = FCOL[9]+' unavailable!*'+FEND
    else:
        git_warning = ''
    
    
    for e in test_list:
        e = e.strip()
    alternatives = False
    
    if SPACK_SEARCH_ROOT=='/':
        search_mode=SPACK_SEARCH_ROOT+FCOL[13]+' [global]'+FEND
    elif SPACK_SEARCH_ROOT=='~':
        search_mode=SPACK_SEARCH_ROOT+FCOL[13]+' [local]'+FEND
    else:
        search_mode=SPACK_SEARCH_ROOT+FCOL[13]+' [custom]'+FEND

    if len(test_list)>0:
        alternatives = True

    #there is a path but is that an actual spack-directory? 
    if len(SPACK_XPTH)>0 and SPACK_XPTH.isspace()!=True:          
        
        for e in test_list:
            #is that our spack?
            if e.find(SPACK_XPTH)!=-1 and check_is_dir(SPACK_XPTH)==False:
                #it is and therefore should be used
                check_python()
                return True
               
        print('\n')
        
        #our spack-path seems invalid, so we have to ask how to continue
        print(FCOL[6]+'\n<warning> '+FEND+'specified path doesn\'t correspond to a spack-installation!')
        print('          '+FCOL[6]+SPACK_XPTH+FEND+'\n')
            
        if git_warning!='':
            print(FCOL[6]+'<warning> '+FEND+'»whereis git« returns no path: installation unavailable!'+FCOL[9]+'*'+FEND+'\n')
            
        if alternatives:
            print(FCOL[15]+'<info>    '+FEND+'these possibly valid options were detected:')
            for e in test_list:
                print('          '+FCOL[15]+'[{}.] '.format(test_list.index(e)+1)+FEND+e)
            print('          '+FCOL[7]+'search mode:'+FCOL[2]+' {}'.format(search_mode)+FEND)
        else:
            print(FCOL[7]+'<info>    '+FEND+'no alternatives were detected! ({})'.format(search_mode))                
        
        while True:
            print(FCOL[14]+'\n- - - how to proceed? - - -'+FEND)
            print('(1) ignore and proceed as usual with given path')
            print('(2) install spack to the given location'+git_warning)
            print('(3) terminate')
            if alternatives:
                print('(4) proceed with an alternative '+FORM[0]+'(will be saved to config!)'+FEND)
        
            answer=input_format()        
        
            if answer==str(1):
                check_python()
                return True
            elif answer==str(2):
                install_spack(SPACK_XPTH)
                check_python()
                return True
            elif answer==str(3) or answer=='quit' or answer=='exit':
                sys.exit(-1)
            elif answer==str(4) and alternatives:
                print(FCOL[14]+'\n- - - which one? - - -'+FEND)
                print('1 <=> first one & up to '+str(len(test_list))+' options')
                SPACK_XPTH = test_list[int(input_format())-1]                
                file_w(BENCH_PTHS[MISC_ID]+'config.txt',SPACK_XPTH+'        [Path to the spack-binary]',4)
                check_python()
                return True
            else:
                print('\ninvalid input')
               
    #there is no path specified, so we have to ask how to continue
    else:
        print(FCOL[6]+'\n<warning> '+FEND+'there\'s no specified path for spack!\n')

        if git_warning!='':
            print(FCOL[6]+'<warning> '+FEND+'»whereis git« returns no path: installation unavailable!'+FCOL[9]+'*'+FEND+'\n')

        if alternatives:
            print(FCOL[15]+'<info>    '+FEND+'these possibly valid options were detected:')
            for e in test_list:
                print('          '+FCOL[15]+'[{}.] '.format(test_list.index(e)+1)+FEND+e)
            print('          '+FCOL[7]+'search mode:'+FCOL[2]+' {}'.format(search_mode)+FEND)
        else:
            print(FCOL[7]+'<info>    '+FEND+'no alternatives were detected! ({})'.format(search_mode))

        while True:
            print(FCOL[14]+'\n- - - how to proceed? - - -'+FEND)
            print('(1) install spack to a specific location'+git_warning)
            print('(2) terminate')
            if alternatives:
                print('(3) proceed with an alternative '+FORM[0]+'(will be saved to config!)'+FEND)
        
            answer=input_format()
            
            if answer==str(1):
                print(FCOL[14]+'\n- - - please specify the location - - -'+FEND)
                print('please specify the '+FORM[2]+'full'+FEND+' path down to the binary')
                print('e.g. .../'+FCOL[5]+'<disired location>'+FEND+'/spack/bin/spack')
                print(FCOL[7]+'\nsb.py was executed in:\n'+FEND+FCOL[2]+LOC+FEND)
                print(FCOL[0]+'\ne.g. input for local installation:\n'+LOC+'/spack/bin/spack'+FEND)
                install_spack(input_format().strip())
                check_python()
                return True
            elif answer==str(2) or answer=='quit' or answer=='exit':
                sys.exit(-1)
            elif alternatives and answer==str(3):
                print(FCOL[14]+'\n- - - which one? - - -'+FEND)
                print('1 <=> first one & up to '+str(len(test_list))+' options')
                SPACK_XPTH = test_list[int(input_format())-1]
                file_w(BENCH_PTHS[MISC_ID]+'config.txt',SPACK_XPTH+'        [Path to the spack-binary]',4)
                check_python()
                return True
            else:
                print('\ninvalid input')

def check_python():
    global menutxt
    if check_python_setting==False:
        return
        
    pth_spack=SPACK_XPTH[:SPACK_XPTH.find('spack')+5]
    py=shell('find '+pth_spack+' -name python | grep bin').split('\n')[:-1]
    
    if len(py)==0:        
         while True:
            print(FCOL[6]+'\n\n<warning> '+FEND+'can\'t find a python package in current spack location!\n          it\'s easy to set up '+FORM[0]+'»matplotlib«'+FEND+' for such a package\n          '+FORM[0]+'»matplotlib«'+FEND+' is a '+FORM[2]+'must have'+FEND+' for plotting!')
            print(FCOL[14]+'\n- - - how to proceed? - - -'+FEND)
            print('(1) install python to the current spack')
            print('(2) ignore and proceed'+FCOL[6]+'*'+FEND)
            print('(3) ignore and proceed, don\'t ask again'+FCOL[6]+'*'+FEND)
            print('(4) terminate')
            print('')
            print(FCOL[6]+'might cause trouble for plotting!*'+FEND)
           
            answer=input_format()
            
            if answer==str(1):
                install_py_script=write_slurm_params(cfg_profiles[0][0],2)+'\n'
                install_py_script+='source {}/share/spack/setup-env.sh\n'.format(SPACK_XPTH[:-9])
                install_py_script+='spack install python'
                                
                if os.path.isfile('{}/install_python.sh'.format(LOC))==True:
                    shell('rm {}/install_python.sh'.format(LOC))
                
                shell('touch {}/install_python.sh'.format(LOC))
                file_w('{}/install_python.sh'.format(LOC),install_py_script,'a')
                menutxt+='\n'
                menutxt+=FCOL[15]+'<info>    '+FEND+'Python installation started '
                menutxt+=shell('sbatch {}/install_python.sh'.format(LOC))
                return
            elif answer==str(2):
                return
            elif answer==str(3):
                menutxt+='\n'
                menutxt+=(FCOL[15]+'<info>    '+FEND+'python check disabled! can be changed in settings or mem.txt')
                if int(get_mem_digit(10))==1:
                    mode_switch('check_python_setting', 0)
                    file_w('{}/mem.txt'.format(LOC),'check_python_setting\t\t\t[0]',10)
                return
            elif answer==str(4) or answer=='quit' or answer=='exit':               
                sys.exit(-1)
            else:
                print('\ninvalid input')
        
#Vorbereitung des Arrays mit den Profildaten
def prepare_array():
    global cfg_profiles, prepare_array_t
    timestart = time.time()
    
    #['test']*n <=> ['test, 'test', ...] or ['test'*n] <=> ['testtesttest...']
    #Spezielle Angaben z.B. welche Partition/Nodes usw. gelten für Installationsdienste etc.
    cfg_profiles[MISC_ID].append([[]])  
    #Für jeden Bench eine Liste, in jeder dieser Listen... 
    for id in BENCH_ID_LIST:
        if id==MISC_ID:
            continue
        #...one list per profile       
        #for _ in range(len(glob.glob(BENCH_PTHS[id]))): (alternative?)
        for _ in range(len(get_names(BENCH_PTHS[id]))):       
            #Für jedes Profil existieren verschiedene Blöcke an Informationen (z.B. über SLURM-Einstellungen)
            cfg_profiles[id].append([[]])
            #loadprogress('')
    prepare_array_t=time.time()-timestart

#checks if error log exist and some settings
def check_data():
    global check_data_t, initm, mr, ml, colour_support, refresh_intervall, form_factor_menu ,LOC
    timestart = time.time()
    #loadprogress('')
    if os.path.isfile('{}/log.txt'.format(LOC))==False:     
        shell('touch {}/log.txt'.format(LOC))
        if info_feed:
            initm+=FCOL[7]+'<info>    '+FEND+'new error-log (log.txt) was created'       
    if os.path.isfile('{}/mem.txt'.format(LOC))==False:     
        txt='-------------------program settings-------------------'
        txt+='\n---------------direct input or via menu---------------'
        txt+='\nform_factor_menu\t\t\t[12]'
        txt+='\nrefresh_intervall\t\t\t[0]'
        txt+='\ncolour_support\t\t\t[0]'
        txt+='\ndebug_mode\t\t\t[0]'
        txt+='\ninfo_feed\t\t\t[0]'
        txt+='\ntermination_logging\t\t\t[0]'
        txt+='\npath_logging\t\t\t[0]'
        txt+='\nauto_space_normalization\t\t\t[0]'
        txt+='\ncheck_python_setting\t\t\t[1]'
        txt+='\n------------------last boot up stats------------------'
        txt+='\n----------------no intended user input----------------'
        txt+='\nevaluate_paths\t\t\t[]'
        txt+='\nprepare_array\t\t\t[]'
        txt+='\ncheck_data\t\t\t[]'
        txt+='\ncheck_dirs\t\t\t[]'
        txt+='\nget_cfg\t\t\t[]'
        txt+='\ncreate_mem\t\t\t[]'
        file_w('{}/mem.txt'.format(LOC), txt, 'a')
        initm+='program settings (mem.txt) were created ...\n'
        form_factor_menu = int(get_mem_digit(2))
        refresh_format_params()
        refresh_intervall = int(get_mem_digit(3))
        colour_support = int(get_mem_digit(4))
        color_check()
        mode_switch('dbg', int(get_mem_digit(5)))
        mode_switch('info_feed', int(get_mem_digit(6)))
        mode_switch('termination_logging',int(get_mem_digit(7)))
        mode_switch('path_logging',int(get_mem_digit(8)))
        mode_switch('auto_space_normalization',int(get_mem_digit(9)))
        mode_switch('check_python_setting',int(get_mem_digit(10)))
    check_data_t=time.time()-timestart

#checks config directories
def check_dirs():
    global initm, check_dirs_t
    timestart = time.time()
    spack_errorcheck()
    for pth in BENCH_PTHS:
        #loadprogress('')
        if BENCH_PTHS.index(pth)==0:
            continue
        if os.path.isdir(pth[:-1])==False:
            #notice: '/dir1/dir2/.../'[:-1] <=> '/dir1/dir2/...'
            shell('mkdir -p '+pth[:-1])
            initm+='Ein Config-Verzeichnis (.../configs/{}) für {} wurde erstellt ...\n'.format(tag_id_switcher(BENCH_PTHS.index(pth)))
    check_dirs_t=time.time()-timestart

#reads profiles from local configs
def get_cfg(bench,farg='all'):
    timestart = time.time()
    global cfg_profiles, get_cfg_t
    
    sublist, spec_ = [], []
    id = tag_id_switcher(bench)
    
    if id != MISC_ID:
        print('\nloading {}'.format(bench))
    
    if farg=='all':
        names = get_cfg_names(get_cfg_path(bench), bench)
    else:
        names = farg_to_list(farg,bench)
        
        for n in names:
            if os.path.isfile(get_cfg_path(bench)+n)==False:
                del names[names.index(n)]
                error_log('»'+get_cfg_path(bench)+n+'« doesn\'t exist!')
        cfg_profiles[id]=cfg_profiles[id][:len(names)]    

    
    #for each profile
    for p in names:
        block = 1
        try:
            txtfile = open(get_cfg_path(bench)+p, 'r')
            txtlist = txtfile.readlines()
        except Exception as exc:
                error_log('can\'t load »'+get_cfg_path(bench)+p+'«', locals(), traceback.format_exc())
                progressbar(names.index(p)+1, len(names))
                continue
        test=''
        #inserts each row accordingly
        for ln in txtlist:                
            #last block & reset of variables            
            if txtlist.index(ln)==len(txtlist)-1: 
                sublist.append(config_cut(ln))                              
                cfg_profiles[id][names.index(p)].append(sublist)               
                cfg_profiles[id][names.index(p)].append([])
            #collects regular rows in a sublist
            elif (ln.find('---')==-1) and (ln.find('[Pfad')==-1):                                   
                sublist.append(config_cut(ln))
                if block==2:
                    spec_.append(ln)
            #a parting line implies that we're ready to append the finished block
            elif (len(sublist)>0) and (ln.find('---')>-1):                
                cfg_profiles[id][names.index(p)].append(sublist)                
                block+=1
                sublist=[]
                continue
            #skips further parting lines
            else:            
                continue                   
        #normal profiles need additional metadata
        if id != MISC_ID:
            #normalises whitespaces in the config 
            if auto_space_normalization:                
                normalise_config(get_cfg_path(bench)+p,blocks=block+1)
            spec = get_spec(spec_,bench)
            cfg_profiles[id][names.index(p)][0] = [p, get_cfg_path(bench)+p, get_target_path(spec), spec]
       
        sublist, spec_, spec = [], [], ''       
              
        #small illustration of loadprogress
        if id != MISC_ID:
            progressbar(names.index(p)+1, len(names))        
        txtfile.close()
    print(test)   
    #not »get_cfg_t=time.time()-timestart« because we might have multiple loading operations
    get_cfg_t+=time.time()-timestart    

def save_times():
    global menutxt, stat_table
    c = count_line('{}/mem.txt'.format(LOC))
    file_w('{}/mem.txt'.format(LOC),'initialization    [{}]'.format(str(init_t)),c-7)
    file_w('{}/mem.txt'.format(LOC),'path evaluation   [{}]'.format(str(evaluate_paths_t)),c-6)
    file_w('{}/mem.txt'.format(LOC),'array preparation [{}]'.format(str(prepare_array_t)),c-5)
    file_w('{}/mem.txt'.format(LOC),'data verification [{}]'.format(str(check_data_t)),c-4)
    file_w('{}/mem.txt'.format(LOC),'dir. verification [{}]'.format(str(check_dirs_t)),c-3)
    file_w('{}/mem.txt'.format(LOC),'config loading    [{}]'.format(str(get_cfg_t)),c-2)
    stat_table.append([str('{:08.6f}'.format(init_t))+' [s]','main initialization'])
    stat_table.append([str('{:08.6f}'.format(evaluate_paths_t))+' [s]','path evaluation     ƒ@init.'])
    stat_table.append([str('{:08.6f}'.format(prepare_array_t))+' [s]','array preparation   ƒ@init.'])
    stat_table.append([str('{:08.6f}'.format(check_data_t))+' [s]','data verification   ƒ@init.'])
    stat_table.append([str('{:08.6f}'.format(check_dirs_t))+' [s]','dir. verification   ƒ@init.'])
    stat_table.append([str('{:08.6f}'.format(get_cfg_t))+' [s]','config loading      ƒ@cl_arg();menu()'])

#looking for matplotlib and installs if not found
def find_matplot_python_hash():
    pth_spack=SPACK_XPTH[:SPACK_XPTH.find('spack')+5]
    pth=shell('find {} -name matplotlib'.format(pth_spack))
   
    #Kein matplotlib installiert 
    if pth=='':
        sourcen='source {}/share/spack/setup-env.sh; '.format(SPACK_XPTH[:-9])
        py=shell('find '+pth_spack+' -name python | grep bin').split('\n')
        count=len(py)-1
        #Eine Pythonversion vorhanden
        if count==1:
            print(shell(sourcen+'spack load python; python -m pip install matplotlib'))
            return ''
            
        #Mehrere Pythonversionen vorhanden
        #py in Form von: spack/opt/spack/linux-centos8-zen3/gcc-12.1.0/python-3.9.12-6ewjgugumhth6r56gvjxhdtq6tvowln7/bin/python 
        #Wir brauchen den hash: 6ewjgugumhth6r56gvjxhdtq6tvowln7
        else:
            py=py[0][py[0].find('python-')+7:py[0].find('/bin')]
            py_hash=py[py.find('-')+1:]
            u=shell(sourcen+'spack load python /'+py_hash+'; python -m pip install matplotlib')
            return '/'+py_hash
            
    #Matplotlib ist installiert 
    #Pfad- bzw. Hashsuche
    pth=pth[pth.find('python'):].replace('-','',1)
    pth=pth[pth.find('-')+1:pth.find('/')]
    return '/'+pth

def comline_run_helper(comline_args):
    global menutxt
    #base case: benchmarks without extra arguments
    if tag_id_switcher(comline_args[0]) in BENCHS_WITHOUT_EXTRA_ARGS: 
        #e.g. »python3 sb.py -r hpl« <=> we want to run all profiles for hpl
        if len(comline_args) < 2 or comline_args[1]=='all':
            get_cfg(comline_args[0])
            return bench_run(tag_id_switcher(comline_args[0]),'all')                
        else:
            get_cfg(comline_args[0],comline_args[1])            
            return bench_run(tag_id_switcher(comline_args[0]),comline_args[1])                
   
    #bechmarks with potential extra arguments are handled on individual basis via elifs
    elif comline_args[0].find('osu')!=-1:        
         
        osu_instruction=comline_args[0].split('_')        
        #Catches invalid arguments 
        if len(osu_instruction)<2:
            menutxt+=FCOL[9]+'invalid arguments'+FEND+': {}'.format(' '.join(map(str,comline_args)))
            return '-1'       
        #prepares extra arguments e.g. latency or osu-flags
        elif len(osu_instruction)>2:
            for _ in osu_instruction[2:]:
                _[0].replace('-','')
                osu_instruction[1]+=' -{} {}'.format(_[0:1],_[1:])
        
        
        if len(comline_args) < 2 or comline_args[1]=='all':
            get_cfg(osu_instruction[0])
            return bench_run(tag_id_switcher(osu_instruction[0]),'all',osu_instruction[1])                                       
        
        else:            
            get_cfg(osu_instruction[0],comline_args[1])
            return bench_run(tag_id_switcher(osu_instruction[0]),comline_args[1],osu_instruction[1])

    

  
"""
Debug- & Hilfs-Funktionen
"""

#represents progress in percent:
#how much is already done (<=> curr) in relation to all tasks (<=> full)
def progressper(curr, full, name):
    #time.sleep(0.1)
    if curr!=full:
        print('lade '+name+'... '+str(int(curr/full*100))+'%', end='\r')
    elif curr==full:
        print('lade '+name+'... '+str(int(curr/full*100))+'%')

#represents progress as a filling bar
def progressbar(curr, full):
    #time.sleep(0.1)
    if form_factor_menu!=0:
        width = form_factor_menu
    else:
        width = int(t_width/4)
    perc = str(int(curr/full*100))+'%'
    sym_p = int(width * (curr/full))     
    sym_e = width-sym_p
    if sym_e > len(perc):
        sym_e = width-(sym_p+len(perc))
        print('[{}]'.format('='*sym_p+' '*sym_e+perc), end='\r')
    else:
        print('[{}]'.format('='*sym_p+' '*sym_e), end='\r')

#represents progress as . -> .. -> ... -> . etc.
def loadprogress(txt = ''):
    #time.sleep(0.01)
    if(loadprogress.c<3):
        loadprogress.c+=1
    else:
        loadprogress.c=1
    print(txt+'.'*loadprogress.c, end='\r')
loadprogress.c=0

#logs a hierarchy of function calls, the locals corresponding to the crashing function and traceback-information in case of exceptions
#the same information is aggregated into two distinct strings: info_l (--> log.txt <=> colorless & persistent) and info_s (--> error_stack <=> volatile), the latter can have color support and the first one guarantees that there's always a variant without any color constants because of possible support issues  
def error_log(txt='', local_table={}, exc_info=''):
    global error_stack
    
    try:
        t = time.localtime()

        if exc_info!='':
            errcol = 6
        else:
            errcol = 7
        #hierarchy graph
        call_hierarchy, line_hierarchy = [], []
        #locals
        local_varname, local_varvalue, local_varnumber, local_scale = [], [], [], []
        
        if txt!='':
            txt = 'further information:\n'+txt
        if dbg:
            if len(local_table)>0:
                i = 0
                maxlength = 0
                #local_varname, local_varvalue, local_varnumber, local_scale = [], [], [], []
                for tuple in local_table.items():
                    _ = list(tuple)
                    i+=1
                    local_varname.append(str(_[0]))
                    
                    #very long values are left out, from our perspective printing hunderts of characters just for one variable harms the debugging more than it helps
                    if len(str(_[1]))>100:
                        local_varvalue.append('***var-value left out, too long: '+str(len(str(_[1])))+' characters***')
                    else:
                        local_varvalue.append(str(_[1]))
                    
                    local_varnumber.append('['+str(i)+'.] ')
                    local_scale.append((len(str(_[0]))+len('['+str(i)+'.] '))//8)
                    
                    if len(str(_[0]))+len('['+str(i)+'.] ')>maxlength:
                        maxlength = len(str(_[0]))+len('['+str(i)+'.] ')
                
                for n in range(len(local_scale)):
                    local_scale[n] = (maxlength//8)-local_scale[n]
                    local_varname[n] = local_varname[n]+'\t'*local_scale[n]
             
        #we handle the two inner- (<=> error log at i=0 and the problem-function at i=1) & outermost frames (<=> root) as special cases 
        i=len(inspect.stack())-1
        while (i>2):
            i-=1
            #how is the function called?
            call_hierarchy.append(inspect.stack()[i][3])
            if i+2<len(inspect.stack()):
                #in which line was it called?
                if(inspect.stack()[i+2][3]!='code_eval'):
                    line_hierarchy.append(inspect.stack()[i+1][2])
                else:
                    #so far we failed to determine the calling line if it's done through eval(...)
                    line_hierarchy.append(str(inspect.stack()[i+1][2])+'(invalid!)')
            else:
                line_hierarchy.append(inspect.stack()[i+1][2])
        
        #that might cover the regular situations, but...
        if len(inspect.stack())>2:
            call_hierarchy_errlog = inspect.stack()[len(inspect.stack())-1][1]+': '+inspect.stack()[len(inspect.stack())-1][3]+'-->'+'-->'.join(list_econcat(call_hierarchy,line_hierarchy,'','#'))+'-->'+'***'+inspect.stack()[1][3]+'***'+'#'+str(inspect.stack()[2][2])+'-->'+inspect.stack()[0][3]+'@'+time.strftime("%d-%m-%Y---%H:%M:%S", t)+' [***problem occurance***] '+'\n'
            call_hierarchy_errstk = inspect.stack()[len(inspect.stack())-1][1]+': '+FCOL[13]+inspect.stack()[len(inspect.stack())-1][3]+FEND+'-->'+'-->'.join(list_econcat(call_hierarchy,line_hierarchy,FEND,FCOL[0]+'#',FEND))+'-->'+FCOL[errcol]+inspect.stack()[1][3]+FCOL[0]+'#'+str(inspect.stack()[2][2])+FEND+'-->'+inspect.stack()[0][3]+FCOL[0]+'@'+time.strftime("%d-%m-%Y---%H:%M:%S", t)+FEND+' ['+FCOL[13]+'root'+FCOL[errcol]+' problem occurance'+FEND+']'+'\n'
        #...what if we have very few frames? e.g. in the initialization phase <module> might call *directly* the error function!
        else:
            call_hierarchy_errlog = inspect.stack()[len(inspect.stack())-1][1]+': '+'***'+inspect.stack()[len(inspect.stack())-1][3]+'***'+'-->'+inspect.stack()[0][3]+'@'+time.strftime("%d-%m-%Y---%H:%M:%S", t)+' [***problem occurance***] '+'\n'
            call_hierarchy_errstk = inspect.stack()[len(inspect.stack())-1][1]+': '+FCOL[13]+inspect.stack()[len(inspect.stack())-1][3]+FEND+'-->'+inspect.stack()[0][3]+FCOL[0]+'@'+time.strftime("%d-%m-%Y---%H:%M:%S", t)+FEND+' ['+FCOL[13]+'root'+FEND+' <=>'+FCOL[errcol]+' problem occurance'+FEND+']'+'\n'
        
        call_hierarchy_errlog = call_hierarchy_errlog.replace('-->-->','-->')
        call_hierarchy_errstk = call_hierarchy_errstk.replace('-->-->','-->')
        
        localslist_color = list_econcat(local_varnumber, list_econcat(local_varname, local_varvalue, FCOL[errcol], FEND+FCOL[15]+'\t<==>\t'+FEND+FCOL[errcol], FEND), FCOL[15], FEND)
        localslist = list_econcat(local_varnumber, list_econcat(local_varname, local_varvalue, '', '<==>\t'))
        
        linesize_l = int(50+form_factor_menu*0.2)
        linesize_s = int(t_width*0.2+form_factor_menu*0.2)
        
        #call hierarchy
        info_s=FCOL[15]+'{}\n'.format('---'*linesize_s)+FORM[0]+'{} - call hierarchy - \n'.format('   '*int(linesize_s*0.45))+FEND+call_hierarchy_errstk+txt+'\n'
        info_l='{}\n'.format('---'*linesize_l)+'{} - call hierarchy - \n'.format('   '*int(linesize_l*0.45))+call_hierarchy_errlog+txt+'\n'
        #exception info
        if exc_info!='':
            info_s+=FCOL[15]+'{}\n'.format(' - '*linesize_s)+FORM[0]+'{}    - exception -   \n'.format('   '*int(linesize_s*0.45))+FEND+FCOL[errcol]+exc_info+FEND
            info_l+='{}\n'.format(' - '*linesize_l)+'{}    - exception -   \n'.format('   '*int(linesize_l*0.45))+exc_info   
        #locals info
        if len(local_table)>0 and dbg:    
            info_s+=FCOL[15]+'{}\n'.format(' - '*linesize_s)+FORM[0]+'{}     - locals -     \n'.format('   '*int(linesize_s*0.45))+FEND+FCOL[errcol]+'\n'.join(localslist_color)+FEND+'\n'
            info_l+='{}\n'.format(' - '*linesize_l)+'{}     - locals -     \n'.format('   '*int(linesize_l*0.45))+'\n'.join(localslist)+'\n'
        #end
        info_s+=FCOL[15]+'{}\n'.format('---'*linesize_s)+FEND
        info_l+='{}\n'.format('---'*linesize_l)    
        
        file_w('{}/log.txt'.format(LOC), info_l+'\n', 'a')
        error_stack.append(info_s+'\n')
    except Exception as exc:
        error_log('', locals(), traceback.format_exc())

#checks whether the error_stack is empty
def check_err_stack():
    if len(error_stack)!=0:
        c = 0
        for e in error_stack:
            c+= e.count('- call hierarchy -')
        return '... '+str(c)+' entries available'
    else:
        return ''

def show_err_stack():
    elist = '\n'
    if len(error_stack)==0:
        elist +=FCOL[4]+'no errors detected!'+FEND+'\n'
    else:
        elist =FCOL[9]+'recent errors...'+FEND+'\n'
        while len(error_stack)!=0:
            elist += error_stack.pop()+'\n'
    return elist

def shell(cmd):
    global menutxt
    try:
        #we want to know to know how 
        p = subprocess.run(str(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        if termination_logging and p.returncode!=0:
            if info_feed:
                #that's a dummy
                line_without_cmd = ml+'<info>    '+'non zero termination for »'+'(...)'+'«'
                #here are the real messages
                if len(line_without_cmd)+len(cmd)>t_width:
                    menutxt+=FCOL[7]+'<info>    '+FEND+'non zero termination for »'+cmd[:t_width-len(line_without_cmd)]+FCOL[0]+'(...)'+FEND+'«'+'\n'
                else:
                    menutxt+=FCOL[7]+'<info>    '+FEND+'non zero termination for »'+cmd+'«'+'\n'
            error_log('subshell: non zero termination for »'+cmd+'«')
        return p.stdout.decode('UTF-8')
    except Exception as exc:
        error_log('command: »'+cmd+'«', locals(), traceback.format_exc())
    

#Wertet einen Python-Ausdruck aus
def code_eval(expr):
    try:
        #Vorbereitung; Umleidung der Standardausgabe (print() hat z.B. keinen direkten return...)
        primary_stdout = sys.stdout
        aux_stdout = StringIO()
        sys.stdout = aux_stdout
        inftxt=''
        linesize = int(t_width*0.2+form_factor_menu*0.2)
        
        #execution
        r = eval(expr)    
        sys.stdout = primary_stdout
        
        if dbg and colour_support==1:
            inftxt+='\n'+FCOL[15]+'{}\n'.format('---'*linesize)+FORM[0]+'{} - eval() output - \n'.format('   '*int(linesize*0.45))+FEND+'\n'
            inftxt+='   '*int(linesize*0.30)+FCOL[0]+'purple colored text \t\t<=> type'+FEND+'\n'
            inftxt+='   '*int(linesize*0.30)+FCOL[0]+'teal or beige colored text \t<=> return'+FEND+'\n'
            inftxt+='   '*int(linesize*0.30)+FCOL[0]+'white colored text \t\t<=> stdout'+FEND+'\n'
            inftxt+='\n\n'

        headtxt=FORM[0]+str(type(r))+FEND
        return inftxt+'{}'.format(FCOL[12]+headtxt+'\n'+FCOL[15]+FORM[0]+str(r)+FEND+'\n'+FCOL[3]+FORM[0]+aux_stdout.getvalue()+FEND)+'\n'+'\n'+FCOL[15]+'{}\n'.format('---'*linesize)+FEND

    except Exception as exc:
        sys.stdout = primary_stdout
        error_log('command: »'+expr+'« ', locals(), traceback.format_exc())
        return '\n'+FCOL[15]+'{}\n'.format('---'*linesize)+FORM[0]+'{} - eval() output - \n'.format('   '*int(linesize*0.45))+FEND+'\n'+FCOL[9]+traceback.format_exc()+FEND+FCOL[15]+'{}\n'.format('---'*linesize)+FEND

#Liefert für eine Configzeile "123.4.5   [Parameter x]" nur die Zahl
def config_cut(line):
    c = line.find("[")
    if(c!=-1):
        line = line[:c]   
    return line.strip()

def function_check(name):
    try:
        ref = globals()[name]
        return inspect.isfunction(ref)
    except KeyError:      
        return False

#elementwise concationation for lists: e.g. list_econcat(['1','2'],['a','b'], '/', '#', '/') -> ['/1#a/', '/2#b/'] 
def list_econcat(list_a, list_b, symb_s='', symb_m='', symb_e=''):
    try:     
        rlist=[]
        if len(list_a)!=len(list_b):
            #we might want to use only one list
            if list_a=='' and list_b!='':
                #['test']*n <=> ['test, 'test', ...] or ['test'*n] <=> ['testtesttest...']
                list_a = ['']*len(list_b)
            elif list_a!='' and list_b=='':
                list_b = ['']*len(list_a)
            else:
                error_log('warning: lists have different sizes, elementwise concationation canceled!', locals())    
        else:
            for i in range(len(list_a)):
                rlist.append(symb_s+str(list_a[i])+symb_m+str(list_b[i])+symb_e)
        return rlist
    except Exception as exc:     
        error_log('', locals(), traceback.format_exc())

#Ein Art Prompt für den Nutzer
def input_format():
    print(' ')
    print(FCOL[14]+'<input>'+FEND+' ', end='')
    return input()

def clear():
    os.system('clear')
    #print('\n\n\n---Debugprint---\n\n\n')

#repairs different spaces between parameter and values:
# parameter x   [a]         ->    parameter x   [a]   
# parameter y    [b]        ->    parameter y   [b]
#blocks <=> how many ------- separator lines do we expect? (that's a safeguard for individual scripts at the end of profiles)  
def normalise_config(name, scale=0, blocks=5, tabs=False, tabsize=8):
    param_names = []
    param_values = []
    connection = []
    maxsize = 0
    finished_blocks = 0
    with open(name, 'r') as f:      
        stringlist = f.readlines()
    for l in stringlist:
        if finished_blocks<blocks:
            if l.find('---')!=-1:
                param_names.append('')
                param_values.append(l)
                finished_blocks+=1
            else:
                parts = l.replace('[','<<<split>>>[').split('<<<split>>>')
                param_names.append(str(parts[0]).strip()+' ')
                if len(str(parts[0]).strip())>maxsize:
                    maxsize = len(str(parts[0])+' ')
                param_values.append(str(parts[1]).strip()+'\n')
        else:
            param_names.append('')
            param_values.append(l)
    for l in param_names:
        if l=='':
            connection.append('')
        else:
            if tabs:
                connection.append('\t'*scale*int((maxsize//tabsize)-(len(l)//tabsize)))
            else:
                connection.append(' '*scale+' '*(maxsize-len(l)))
    #multiple elementwise listconcatinations        
    new_lines=list_econcat(list_econcat(param_names, connection), param_values)
    with open(name, 'w') as f:
        f.writelines(new_lines)    
    
def install_spack(pth):
    global SPACK_XPTH, menutxt
    if shell('whereis git').split('git:')[1].isspace==False:
        if len(pth)>15:
            #pth might point to the binary position
            if pth[-15:]=='spack/bin/spack':
                inst_pth=pth[:-16]
            else:
                inst_pth=pth
                pth=pth+'/spack/bin/spack'
        else:
            inst_pth=pth
        if check_is_dir(inst_pth)==False:
            cmd_ = 'mkdir {};'.format(inst_pth)
        else:
            cmd_ = ''
        #set -e is supposed to prevent an installment if we're in the wrong place
        cmd='set -e; {}cd {}; git clone -c feature.manyFiles=true https://github.com/spack/spack.git'.format(cmd_, inst_pth)
        shell(cmd)
        SPACK_XPTH=pth 
        file_w(BENCH_PTHS[MISC_ID]+'config.txt',SPACK_XPTH+'        [Path to the spack-binary]',4)
        menutxt+=FCOL[15]+'\n<info>    '+FEND+'spack was installed to following location:'+'\n          '+FCOL[15]+inst_pth+FEND
    else:
        menutxt+=FCOL[15]+'\n<warning> '+FEND+'spack installation failed! (git clone ...)'+'\n          '+FCOL[15]+'reason: git location unkown!'+FEND

def spack_errorcheck():
    global menutxt, spack_problem
    
    if SPACK_XPTH.isspace() and len(SPACK_XPTH)>0:
        error_log('specified path to the spack binary consists only of whitespaces!')
        menutxt+='\n'+FCOL[6]+'<warning> '+FEND+'specified path to the spack binary consists only of whitespaces!\n'
        spack_problem = 'specified path to the spack binary consists only of whitespaces!'
    
    #shell('if [[ ! -d {} ]] && [[ -f {} ]]; then echo \'true\'; else echo \'false\'; fi'.format(SPACK_XPTH))
    if shell('if [[ ! -x {} ]]; then echo \'true\'; else echo \'false\'; fi'.format(SPACK_XPTH))=='true\n':
        error_log('no execution rights for the specified spack binary!')
        menutxt+='\n'+FCOL[6]+'<warning> '+FEND+'no execution rights for the specified spack binary!\n'+'          '+SPACK_XPTH
        spack_problem = 'no execution rights for the specified spack binary!'
    
    if shell('if [[ -d {} ]]; then echo \'true\'; else echo \'false\'; fi'.format(SPACK_XPTH))=='true\n':
        error_log('specified spack binary is a directory!')
        menutxt+='\n'+FCOL[6]+'<warning> '+FEND+'specified spack binary is a directory!\n'+'          '+SPACK_XPTH
        spack_problem = 'specified spack binary is a directory!'

    if shell('if [[ ! -e {} ]]; then echo \'true\'; else echo \'false\'; fi'.format(SPACK_XPTH))=='true\n':
        error_log('specified spack binary doesn\'t exist!\n'+SPACK_XPTH)
        menutxt+='\n'+FCOL[6]+'<warning> '+FEND+'specified spack binary doesn\'t exist!\n'+'          '+SPACK_XPTH
        spack_problem = 'specified spack binary doesn\'t exist!' 

#Bug: Liefert z.T. auch Verzeichnisse! <--- TODO
#Liefert Files, keine Verz.; Erwartet Pfade in der Form /dir1/dir2/.../
def get_names(pth):
    global menutxt
    r = os.listdir(pth)
    for _ in r:
        if check_is_dir(pth+str(_)):
            r.remove(_)
            menutxt+='remove: '+str(_)+'\n'
    return r

#Bug: Liefert z.T. Verzeichnisse auch nicht! <--- TODO
#Liefert alle Verzeichnis; Erwartet Pfade in der Form /dir1/dir2/.../
def get_dirs(pth):
    global menutxt
    t = os.listdir(pth)
    r = []
    for _ in t:
        if check_is_dir(pth+str(_)):
            r.append(_)
            menutxt+='remove: '+str(_)+'\n'
    return r

#Liefert Textfiles eines bestimmten Typs (z.B. hpl_cfg_(...).txt)
def get_cfg_names(pth, typ):
    if typ == 'misc':
        return ['config.txt']
    else:
        return fnmatch.filter(get_names(pth), str(typ)+'_cfg_*.txt')

#Bekommt eine Liste bzgl. der Packages aus einer Config, liefert die package spec
def get_spec(cfg_list,bench):
    block=False
    if bench == 'osu':
        bench='osu-micro-benchmarks'
    spec = bench    
    for _ in cfg_list:      
        _ = _.split('[')
        further_package_specification = _[1].find('Version')!=-1 or _[1].find('Compiler')!=-1      
        if _[0].isspace()==False:
            if further_package_specification and block:
                #we don't want to append these, since we don't even know the package name
                continue
            else:
                block = False
                _[0]=_[0].rstrip()            
                if _[1].find('Version')!=-1:
                    spec = spec+'@'
                elif _[1].find('Compiler')!=-1:
                    spec = spec+'%'
                else:
                    spec=spec+'^'
            spec=spec+_[0]
        else:
            #we want to block further specification from the profile, if we don't even know the package name
            if further_package_specification == False:
                block=True
    return spec

#Liefert alle Specs einer Config-Liste bzw. eines Benchmarktyps
#Erhält Benchmarkname und (optional) Liste mit Config-Namen
def get_all_specs(bench,cfgs='all'):
    expr=[]  
    for s in cfg_profiles[tag_id_switcher(bench)]:        
        if cfgs=='all' or s[0][0] in cfgs:
            expr.append([s[0][3],s[0][0]])    
    return expr

def config_out(bench_id):
    s=''
    for p in cfg_profiles[bench_id]:
        #Metadaten
        s +='\n'+ml+FCOL[15]+'- '*(int(t_width*0.2))+FEND+'\n'
        s +=ml+FBGR[15]+FCOL[1]+'{}'.format(p[0][0])+FEND+'\n'
        #Abschnitte der Profile
        for b in range(0,len(p)):
            s +=ml+FCOL[15]+'- - -{}. block- - -'.format(str(b))+FEND+'\n'
            #individuelle Lines des Blocks (=Strings) sind konkatenierbar
            for l in p[b]:
                if l=='':
                    s +=ml+ml+FCOL[0]+'leer'+FEND+'\n'
                else:
                    if l.strip()=='no path found!':
                        s +=ml+ml+FCOL[9]+l+FEND+'\n'
                    else:
                        s +=ml+ml+l+'\n'
    s +='\n'+ml+FCOL[15]+'- '*(int(t_width*0.2))+FEND+'\n\n'
    return s

def tag_id_switcher(bench):
    try:
        switcher={
        MISC_ID: 'misc',
        HPL_ID: 'hpl',
        OSU_ID: 'osu',
        HPCG_ID: 'hpcg',
      
        'misc': MISC_ID,
        'hpl': HPL_ID,
        'osu': OSU_ID,
        'hpcg': HPCG_ID,
        }
        return switcher.get(bench) 
    
    except KeyError:
        menutxt+=FCOL[9]+FORM[0]+'---unkown bench type---'+FEND+'\n'
        error_log('an unkown bench-reference was used: '+str(bench), locals(), traceback.format_exc())
        return '-1'

#Configpfad
def get_cfg_path(bench):
    if type(bench) == int:
        return BENCH_PTHS[bench]
    elif type(bench) == str:
        return BENCH_PTHS[tag_id_switcher(bench)]
    else:
        error_log('invalid type! »'+str(type(bench))+'« ', locals())
        return '-1'
    

#Zielpfad zu Binary&HPL.dat
def get_target_path(spec):
    global menutxt
    pth = shell(SPACK_XPTH+' find --paths '+spec)
    _ = pth.find('/home')
    r = (pth[_:]).strip()
    if r!='':
        return r+'/bin'
    else:
        if path_logging:
            if info_feed:
                menutxt+=FCOL[7]+'<info>    '+FEND+'a path for »'+spec[:spec.find('^')]+'« couldn\'t be found!'+'\n'
            error_log('a path for »'+spec[:spec.find('^')]+'« couldn\'t be found!', locals())
        return 'no path found!'

#Erwartet: Argumentliste zu -r/-i und der Benchname (String)
def farg_to_list(farg, bench):
    names = farg.split(',')
    
    for e in names:
        _ = str(e).find('-')
        #Umwandeln von Bindestrichnotation zu konkreten Zahlen: 3-5 -> 3 4 5
        if _!=-1:
            #Hinweis zum Slicen: string[a:b] <=> mit Index a aber ohne Index b
            #Hinweis zu range(x,y): Inkl. Index x aber kleiner Index y
            for i in range(int(e[:_]),int(e[_+1:])+1):
                names.append(i)
            #Eintrag abgearbeitet
            del names[names.index(e)]
    for e in names:
        #print('farg-to-list:'+str(names[names.index(e)]))
        names[names.index(e)] = bench+'_cfg_'+str(e)+'.txt'
    
    
    return names

def write_slurm_params(profile, block):
    global menutxt

    #Shebang
    txt='#!/bin/bash\n'
    #Partition
    if profile[block][0]!='':
        txt+='#SBATCH --partition={}\n'.format(profile[block][0])
    #Nodezahl
    if profile[block][1]!='':
        txt+='#SBATCH --nodes={}\n'.format(profile[block][1])
    #Anzahl der Prozesse
    if profile[block][2]!='':
        txt+='#SBATCH --ntasks={}\n'.format(profile[block][2])
    #Anzahl der Prozesse pro Node
    if profile[block][3]!='':       
        txt+='#SBATCH --ntasks-per-node={}\n'.format(profile[block][3])
    #Anzahl der CPUs pro Task/Prozess(default lt. SLURM-Doku: 1 Kern per Task)
    if profile[block][4]!='':
        txt+='#SBATCH --cpus-per-task={}\n'.format(profile[block][4])
    #Anzahl an allokiertem Speicher pro CPU
    if profile[block][5]!='':
        txt+='#SBATCH --mem-per-cpu={}\n'.format(profile[block][5])
    #Startzeitpunkt (z.B. now+180 <=> in drei Minuten starten)
    if profile[block][6]!='':
        txt+='#SBATCH --begin={}\n'.format(profile[block][6])
    #Zeitlimit 
    if profile[block][7]!='':
        txt+='#SBATCH --time={}\n'.format(profile[block][7])
    #Ziel-User für Emailbenachrichtigungen
    if profile[block][8]!='':
        txt+='#SBATCH --mail-user={}\n'.format(profile[block][8])
    #Valide Trigger für Benachrichtigungen
    if profile[block][9]!='':
        txt+='#SBATCH --mail-type={}\n'.format(profile[block][9])
    
    return txt

def find_binary(profile, bench_id):  
    if check_expr_syn(profile[0][3],profile[0][0]) == 'True':
        bin_path = shell(SPACK_XPTH+' find --paths '+profile[0][3])
        #Die Benchmarks sollten vom home-Verzeichnis aus erreichbar sein... <-- TODO: klären ob das den Anforderungen entspricht
        _ = bin_path.find('/home')
        if _ == -1:
            error_log('package {} seems to be unavailable! profile: '.format(profile[0][3])+profile[0][0], locals())
        else:
            bin_path = ((bin_path[_:]).strip()+'/bin/')
        return bin_path
    else:
        error_log('invalid syntax detected in '+profile[0][0]+', resulting spec: {} '.format(profile[0][3]), locals())
        return bin_path

def delete_dir(pth):
    shutil.rmtree(pth)

def clean(inpt = 'all'):
    global check_data_t, initm, mr, ml, colour_support, refresh_intervall, form_factor_menu ,LOC
    pth = LOC
    rtxt = ''
    if inpt=='log' or inpt=='all':
        if os.path.isfile('{}/log.txt'.format(LOC))==False:
            rtxt+=FCOL[6]+'there was no log-file to be found:\na new one was created!\n'+FEND
            shell('touch {}/log.txt'.format(LOC))
        else:
            shell('rm {}/log.txt'.format(LOC))
            shell('touch {}/log.txt'.format(LOC))
    if inpt=='mem':
        if os.path.isfile('{}/mem.txt'.format(LOC))==False:
            rtxt+=FCOL[6]+'there was no log-file to be found:\na new one was created!\n'+FEND
        else:
            shell('rm {}/mem.txt'.format(LOC))
        txt='-------------------program settings-------------------'
        txt+='\n---------------direct input or via menu---------------'
        txt+='\nform_factor_menu\t\t\t[12]'
        txt+='\nrefresh_intervall\t\t\t[0]'
        txt+='\ncolour_support\t\t\t[0]'
        txt+='\ndebug_mode\t\t\t[0]'
        txt+='\ninfo_feed\t\t\t[0]'
        txt+='\ntermination_logging\t\t\t[0]'
        txt+='\npath_logging\t\t\t[0]'
        txt+='\nauto_space_normalization\t\t\t[0]'
        txt+='\ncheck_python_setting\t\t\t[1]'
        txt+='\n------------------last boot up stats------------------'
        txt+='\n----------------no intended user input----------------'
        txt+='\nevaluate_paths\t\t\t[]'
        txt+='\nprepare_array\t\t\t[]'
        txt+='\ncheck_data\t\t\t[]'
        txt+='\ncheck_dirs\t\t\t[]'
        txt+='\nget_cfg\t\t\t[]'
        txt+='\ncreate_mem\t\t\t[]'
        file_w('{}/mem.txt'.format(LOC), txt, 'a')
        initm+='program settings (mem.txt) were created ...\n'
        form_factor_menu = int(get_mem_digit(2))
        refresh_format_params()
        refresh_intervall = int(get_mem_digit(3))
        colour_support = int(get_mem_digit(4))
        color_check()
        mode_switch('dbg', int(get_mem_digit(5)))
        mode_switch('info_feed', int(get_mem_digit(6)))
        mode_switch('termination_logging',int(get_mem_digit(7)))
        mode_switch('path_logging',int(get_mem_digit(8)))
        mode_switch('auto_space_normalization',int(get_mem_digit(9)))
        mode_switch('check_python_setting',int(get_mem_digit(10)))
    if inpt=='projects' or inpt=='all':    
        if os.path.isdir(pth+'/projects')==False:
            rtxt+=FCOL[6]+'there was no /projects directory to be found!\n'+FEND
        else:
            delete_dir(pth+'/projects')
    
    if inpt=='install' or inpt=='all':
        if os.path.isfile(pth+'/install.sh')==False:
            rtxt+=FCOL[6]+'there was no install.sh to be found\n'+FEND
        else:
             shell('rm {}/install.sh'.format(LOC))
        
        if os.path.isfile(pth+'/install.err')==False:
            rtxt+=FCOL[6]+'there was no install.err to be found\n'+FEND
        else:
             shell('rm {}/install.err'.format(LOC))
        
        if os.path.isfile(pth+'/install.out')==False:
            rtxt+=FCOL[6]+'there was no install.out to be found\n'+FEND
        else:
             shell('rm {}/install.out'.format(LOC)) 
             
    return rtxt+FCOL[4]+'done!'+FEND    

def clean_dummy_projects():
    dummy_list = []
    cmd='find {}/projects -name \'*@*[dummy]*\' -path \'{}/projects*\''.format(LOC, LOC)
    dummy_list = shell(cmd).split('\n')
    for d in dummy_list:
        if d.find('[dummy]')!=-1:
            shell('rm -r {}'.format(d))

def color_check():
    global FCOL, FBGR, FORM
    if colour_support==1:
        for i in range(len(FCOL)):
            FCOL[i] = FCOL_M[i]
        for i in range(len(FBGR)):
            FBGR[i] = FBGR_M[i]
        for i in range(len(FORM)):
            FORM[i] = FORM_M[i]
    else:
        for i in range(len(FCOL)):
            FCOL[i] = ''
        for i in range(len(FBGR)):
            FBGR[i] = ''
        for i in range(len(FORM)):
            FORM[i] = ''

def mode_switch(param, val):
    if val==0:
        globals()[param]=False
    else:
        globals()[param]=True

def refresh_format_params():
    global ml, mr
    if form_factor_menu!=0:
        ml = ' '*(int(form_factor_menu/5))
        mr = ' '+' '*(int(form_factor_menu/12))
    else:
        ml = ' '*(int((t_width/2)-(t_width/20)))
        mr = ' '*(int(t_width/20))

def calc_terminal_size():
    global t_width
    size=str(os.get_terminal_size())
    cut_left=size.find('columns=')
    cut_right=size.find(', ')
    t_width = int(size[cut_left+8:cut_right])

def draw_table(array, size = t_width, offset = 0, factor = 0.8, title='Highlights', COLH = '\33[105m', COL1 = '\33[47m', COL2 = '\33[107m'):
    
    global menutxt
    
    #Größen zum Interieren
    crange = range(len(array[0]))
    lrange = range(len(array))
    
    linesize = int(size*factor)

    #Verkleinerung bis zu einer glatt teilbaren Tabellengröße
    while True:
        if linesize%len(array[0])==0:
            break
        else:
            if linesize>30:
                linesize-=1
            else:
                break
    
    #Tabelle (roh)
    tbl = ''
    
    if linesize<30:
        menutxt+=FCOL[6]+'<warning> '+FEND+'very small window size detected, drawn tables might be distorted!'+'\n'
    
    #Breite der Einträge (d.h. Elemente einer Zeile)
    entry_width = int(linesize/len(crange))
    
    #Was bleibt übrig? (sollte stets 0 sein wg. Schrumpfung von t_width auf glatt teilbares linesize!)
    if linesize-(entry_width*len(crange))>0:
        rest = linesize-(entry_width*len(crange))
    else:
        rest = 0
    
    """
    #debug information
    if dbg:
        dbg_txt=''
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'--Debug-Hints--'+FEND+'\n'
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'t_width: '+'\t\t\t'+str(t_width)+FCOL[0]+'\t<=> real terminal size\n'+FEND
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'array: '+'\t\t\t'+str(len(lrange))+'x'+str(len(crange))+FCOL[0]+'\t<=> array structure\n'+FEND
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'linesize: '+'\t\t\t'+str(linesize)+FCOL[0]+'\t<=> used table size\n'+FEND
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'entry_width: '+'\t\t'+str(entry_width)+FCOL[0]+'\t<=> size per table entry\n'+FEND
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'scaling fac.: '+'\t\t'+str(factor)+FCOL[0]+'\t<=> scales targeted size\n'+FEND
        dbg_txt+=ml+'\t'*offset+FCOL[15]+'tab. offset: '+'\t\t'+str(offset)+FCOL[0]+'\n'+FEND
        
        print(dbg_txt)
    """
    
    #Tabellenbau
    for i in lrange:       
        if i==0:
            #Kopfzeile mit Überschrift
            tbl+='\t'*offset+COLH+FORM[0]+'{:^{pos}}'.format('---'+title[-linesize+3:linesize-3]+'---', pos=linesize)+FEND+'\n'
        newl = ''
        #Abarbeitung der Elemente in einer Zeile
        for j in crange:
            #Differenzierung in gerade/ungerade für wechselnde Farben zwischen Spalten
            if j%2==0:
                newl+='{:<{pos}}'.format(COL2+FCOL[1]+(array[i][j]+' '*(entry_width-len(array[i][j])))[:entry_width], pos=entry_width)
            else:
                newl+='{:<{pos}}'.format(COL1+FCOL[1]+(array[i][j]+' '*(entry_width-len(array[i][j])))[:entry_width], pos=entry_width)
        newl+=' '*rest+FEND
        tbl+='\t'*offset+'{txt:<{pos}}'.format(txt=newl, pos=linesize)+'\n'      
        
    return tbl

#dual use! <=> returns a color-coded list of available/unavailable profiles (e.g. for installation purposes) while also updating pkg_info   
def avail_pkg(id):
    global pkg_info
    rlist = []
    avl = len(cfg_profiles[id])
    full = avl
    miss = 0
    err = 0
    print_menu.updatetime=time.time()
    pkg_info[id][3] = print_menu.updatetime
    for p in cfg_profiles[id]:
        #loadprogress('')
        res = shell('{} find '.format(SPACK_XPTH)+p[0][3])
        if res.find('Kommando nicht gefunden')>-1 or res.find('command not found')>-1 or spack_problem!='':
            rlist.append(FCOL[0]+p[0][0]+FEND)
        else:
            if str(res[0:14])=='==> No package':
                avl-=1
                miss+=1
                rlist.append(FCOL[7]+p[0][0]+FEND)
            elif str(res[0:9])=='==> Error':
                avl-=1
                err+=1
                rlist.append(FCOL[9]+p[0][0]+FEND)
            else:
                rlist.append(FCOL[4]+p[0][0]+FEND)
    if spack_problem=='':
        #for not implemented menu-functions we dont return any list
        if (function_check(tag_id_switcher(id)+'_menu') and function_check('print_'+tag_id_switcher(id)+'_menu'))!=True:
            pkg_info[id][0] = '' #FCOL[9]+' --- no menu implementation --- '+FEND
            pkg_info[id][1] = ''
            pkg_info[id][2] = ''
            return rlist
        if avl==full:
            pkg_info[id][0] = FCOL[5]+str(avl)+FEND+'/'+str(full)+FORM[1]+' avl. '+FEND
        elif avl!=0:
            pkg_info[id][0] = FCOL[7]+str(avl)+FEND+'/'+str(full)+FORM[1]+' avl. '+FEND
        else:
            pkg_info[id][0] = FCOL[9]+str(avl)+FEND+'/'+str(full)+FORM[1]+' avl. '+FEND
        if miss>0:
            pkg_info[id][1] = '('+FCOL[7]+str(miss)+FEND+FORM[1]+' mis., '+FEND
        else:
            pkg_info[id][1] = '('+str(miss)+FORM[1]+' mis., '+FEND
        if err>0:
            pkg_info[id][2] = FCOL[9]+str(err)+FEND+FORM[1]+' err.'+FEND+')'
        else:
            pkg_info[id][2] = str(err)+FORM[1]+' err.'+FEND+')'
    else:
        pkg_info[id][0] = FCOL[9]+'?/?'+FEND+' avl.'
        pkg_info[id][1] = FCOL[9]+' ?'+FEND+' mis.'
        pkg_info[id][2] = FCOL[9]+' ?'+FEND+' err.'
        error_log('information regarding package-availability is unavailable!\n used spack-binary: {}'.format(SPACK_XPTH))
    return rlist



def check_is_dir(pth):
    if shell('if [[ -d {} ]]; then echo \'true\'; else echo \'false\'; fi'.format(pth))=='true\n':
        return True
    return False
   

#Skriptbau-Funktionen
#Default Argument <=> wir wollen alle Profile laufen lassen
def bench_run(bench_id, farg = 'all', extra_args = ''):   

    """ 
    >>>>>   script building pipeline (1/5)           <<<<
    >>>>>   1.1 relevancy check (only menu-based)    <<<<
    >>>>>   1.2 availability check                   <<<<
    """

    global menutxt
    tag = tag_id_switcher(bench_id)    
    pth = get_cfg_path(tag)
    
    selected_profiles = cfg_profiles[bench_id].copy()
    
    
    #Die Liste der Namen der verfügbaren Profile
    avail_names = get_cfg_names(pth, tag)
    #Die Liste der Namen der nicht verfügbaren Profile
    unavail_names = []
    
    #execution via flag in priciple uses only relevant profiles => first check is only relevant for menu-based control
    if menu_ctrl==True:
        #Namen von verfügbaren aber nicht ausgewählten Profilnamen
        unselected_names = []
        
        #argument interpretation
        if farg == 'all':
            names = get_cfg_names(pth, tag)
        else:
            names = farg_to_list(farg, tag)
        
        

        #indices list for profiles not corresponding to our current run
        dlist=[]
        
        for i in range(len(selected_profiles)):
            if selected_profiles[i][0][0] not in names:
                dlist.append(i)
                #these are the profiles we shall ignore
                unselected_names.append(selected_profiles[i][0][0])
        dlist.reverse()
        
        #now only relevant profiles remain --> but are they available?
        for i in dlist:
            del selected_profiles[i]
            
        if len(selected_profiles)==0:
            menutxt+=FCOL[6]+'no known profiles were selected!'+FEND+'\n'
            menutxt+=FCOL[9]+FORM[0]+'--- script building was canceled ---'+FEND+'\n\n'
            return '-1'
        
    #indices list for profiles not available for our current run
    #this second check is relevant for flag-based execution too
    dlist=[]

    for i in range(len(selected_profiles)):
        if selected_profiles[i][0][2]=='no path found!':            
            res = shell('{} find '.format(SPACK_XPTH)+selected_profiles[i][0][3])
            if res.find('Kommando nicht gefunden')>-1 or res.find('command not found')>-1 or spack_problem!='':
                if spack_problem!='':
                    error_log('a {} run failed, reason: {}'.format(tag, spack_problem))
                else:
                    error_log('a {} run failed, reason: no valid spack binary-path available'.format(tag))
                menutxt+=FCOL[9]+FORM[0]+'no valid path to spack binary available!'+FEND+'\n'
                menutxt+=FCOL[9]+FORM[0]+'--- script building was canceled ---'+FEND+'\n\n'
                return '-1'
            error_log('profile: '+selected_profiles[i][0][0]+' was deselected! (no path known)'+'\n'+res, locals())
            menutxt+='\n'+FCOL[6]+'<warning> '+FEND+'profile: '+FCOL[6]+selected_profiles[i][0][0]+FEND+' was deselected! (no path known)'+'\n'+FCOL[6]+res+FEND
            dlist.append(i)
            unavail_names.append(selected_profiles[i][0][0])
    dlist.reverse()
    
    #now only relevant *and* available profiles remain
    for i in dlist:
        del selected_profiles[i]

    if len(selected_profiles)==0:
        menutxt+=FCOL[6]+'no selected profiles were available!'+FEND+'\n'
        menutxt+=FCOL[9]+FORM[0]+'--- script building was canceled ---'+FEND+'\n\n'
        return '-1'
    
    if dbg and menu_ctrl==True:
        menutxt+='\n\n'+FCOL[15]+'--- '+'summary'+' ---'+FEND+'\n\n'
        for name in unselected_names:
            menutxt+=FCOL[0]+name+ml+'(unselected)'+FEND+'\n'
        for name in unavail_names:
            menutxt+=FCOL[6]+name+ml+'(deselected)'+FEND+'\n'
        for arg_name in names:
            if arg_name not in avail_names:
                menutxt+=FCOL[7]+arg_name+ml+'(does not exist)'+FEND+'\n'
    
    if dbg and menu_ctrl==False:
        names = farg_to_list(farg, tag)
        menutxt+='\n\n'+FCOL[15]+'--- '+'summary'+' ---'+FEND+'\n\n'
        for arg_name in names:
            if arg_name not in avail_names:
                menutxt+=FCOL[7]+arg_name+ml+'(does not exist)'+FEND+'\n'
            else:
                del avail_names[avail_names.index(arg_name)]
        for name in unavail_names:
            menutxt+=FCOL[6]+name+ml+'(deselected)'+FEND+'\n'
        for name in avail_names:
            menutxt+=FCOL[0]+name+ml+'(unselected)'+FEND+'\n'
    
    #Skriptbau, ggf. mit zusätzlichen Argumenten
    if extra_args!='':
        skript=build_batch(selected_profiles, bench_id, extra_args)
        menutxt+='\n'+FCOL[4]+'script building completed:\n'+FEND+FORM[0]+FCOL[3]+skript+FEND+'\n'+'\n'
        #menutxt+='\n'+shell('sbatch '+skript)
    else:
        skript=build_batch(selected_profiles, bench_id)
        menutxt+='\n'+FCOL[4]+'script building completed:\n'+FEND+FORM[0]+FCOL[3]+skript+FEND+'\n'+'\n'
        #menutxt+='\n'+shell('sbatch '+skript)
      
    return skript

#Hiermit soll das Skript gebaut werden 
def build_batch(selected_profiles, bench_id, extra_args = ''):  

    """ 
    >>>>>   script building pipeline (2/5)           <<<<
    >>>>>   1.1 directory-managment                  <<<<
    >>>>>   1.2 batchscript & dependency-handling    <<<<
    """
  
    first_job=True
    tag = tag_id_switcher(bench_id)
    
    t_id = time.strftime('%H%M%S_%d%m%Y', time.localtime())
    
    #such files won't be persistent! (there's a clean up routine for them)
    if test_only:
        t_id+='[dummy]'
    
    #for no iterations this value will be incremented up to len(selected_profiles)
    dependency_offset = 0
    
    #counts desleceted profiles
    num_deselected = 0
    
    #Namen der Auftragsordner
    run_dir='{}/{}_run@{}/'.format(PROJECT_PTH,tag,t_id)
    res_dir='{}/{}_res@{}/'.format(PROJECT_PTH,tag,t_id)
    
    if os.path.isdir(run_dir[:-1])==False:     
        shell('mkdir -p '+run_dir[:-1])
    if os.path.isdir(res_dir[:-1])==False:     
        shell('mkdir -p '+res_dir[:-1])
        
    #Bauen des Batch-Skripts, anhand der Parameter aus der allgemeinen Config
    batchtxt=write_slurm_params(cfg_profiles[0][0],3)
    batchtxt+='#SBATCH --job-name='+tag+'_run'+'@'+t_id+'\n'
    batchtxt+='#SBATCH --output=/dev/null\n'
    batchtxt+='#SBATCH --error='+run_dir+'batch.err\n\n'
    
    #individual jobscripts
    for profile in selected_profiles:
        
        if os.path.isdir(res_dir+profile[0][0][:-4])==False:     
            shell('mkdir -p '+res_dir+profile[0][0][:-4])        
        
        #profile [1] <=> meta-settings [0] <=> first entry: how many iterations are disired?
        num = int(profile[1][0])
        
        if profile[0][2]=='no path found!':
            num_deselected+=1
            continue
        
        #different profiles might use the same package during the same run, so we have to update the benchmark-parameters
        for params in TRANSFER_PARAMS:
            if tag_id_switcher(bench_id) == params[0]:                
                _='python3 '+CONFIG_TO_DAT_XPTH+' '+profile[0][1]+' '+profile[0][2]+'/'+params[3]+' '+str(params[1])+' '+str(params[2])+'\n'              
                
                if first_job:
                    first_job=False
                    batchtxt+='id'+str(dependency_offset)+'=$(sbatch '
                    dependency_offset+=1
                else:
                    batchtxt+='id'+str(dependency_offset)+'=$(sbatch --dependency=afterany:${id'+str(dependency_offset-1)+'##* } '
                    dependency_offset+=1
                    
                if selected_profiles.index(profile)==(len(selected_profiles)-1-num_deselected):
                    batchtxt+=build_config_to_dat_script(_,profile[0][0][:-4],run_dir,True)+')\n'                
                else:
                     batchtxt+=build_config_to_dat_script(_,profile[0][0][:-4],run_dir,False)+')\n'
              
        
        #(1) we're building a dependency-chain for every queued profile *and* with possible iterations in mind!
        #(2) we don't need to transfer parameter between different iterations since they're adjacent in the dependency-chain
        if num!=0:
            for i in range(1, num+1):
                if first_job:
                    first_job=False
                    batchtxt+='id'+str(dependency_offset)+'=$(sbatch '
                    dependency_offset+=1
                else:
                    batchtxt+='id'+str(dependency_offset)+'=$(sbatch --dependency=afterany:${id'+str(dependency_offset-1)+'##* } '
                    dependency_offset+=1
                if extra_args!='':
                    batchtxt+=build_job(profile, bench_id, run_dir, res_dir, i, extra_args)+')\n'
                elif len(extra_args)==0:
                    batchtxt+=build_job(profile, bench_id, run_dir, res_dir, i)+')\n'
        else:
            if first_job:
                first_job=False
                batchtxt+='id'+str(dependency_offset)+'=$(sbatch ' 
                dependency_offset+=1
            else:
                batchtxt+='id'+str(dependency_offset)+'=$(sbatch --dependency=afterany:${id'+str(dependency_offset-1)+'##* } '
                dependency_offset+=1
            if extra_args!='':
                batchtxt+=build_job(profile, bench_id, run_dir, res_dir, 0, extra_args)+')\n'
            elif len(extra_args)==0:
                batchtxt+=build_job(profile, bench_id, run_dir, res_dir, 0)+')\n'
    
    batchtxt+='\nsource {}/share/spack/setup-env.sh\n'.format(SPACK_XPTH[:-9])
    batchtxt+='spack load python '+find_matplot_python_hash()+'\n'
    batchtxt+='sbatch --dependency=afterany:${id'+str(dependency_offset-1)+'##* } ' + build_plot(t_id,tag_id_switcher(bench_id),run_dir)   
    
    #Niederschreiben des Skripts & Rückgabe des entspr. Pfads hin
    file_w(run_dir+'batch.sh',batchtxt,'a')
    shell('chmod +x '+run_dir+'batch.sh')
    return run_dir+'batch.sh' 

def build_job(profile, bench_id, run_dir, res_dir, num=0, extra_args = ''):    
    """ 
    >>>>>   script building pipeline (3/5)           <<<<
    >>>>>   job-script design according to           <<<<
    >>>>>   the selected & available profiles        <<<<
    """
    
    #we read from the profiles how often a bench has to run 
    #[Finale]
    if num==0:
        num_workaround=''
        num=''
    else:
        #please be aware that »num=str(num)+'#'« would result in a comment
        #so we have to use this small work around
        num_workaround=str(num)+'\\#'
        num=str(num)+'#'
        
        
    
    jobtxt=''
    
    if profile[0][0].find('_cfg_')==-1:
        menutxt+=FCOL[6]+'<warning> '+FEND+'»{}« '.format(profile[0][0])+' doesn\'t match the expected config-name pattern: <tag>_cfg_<name>.txt'+'\n'
        error_log('»{}« '.format(profile[0][0])+' doesn\'t match the expected config-name pattern: <tag>_cfg_<name>.txt')
    
    
    #<tag>_cfg_<name>.txt --> <tag>_cfg_<name> (shortened) & <name> (shortest)
    shortened_name = profile[0][0][:-4]
    shortest_name = profile[0][0][profile[0][0].find('_cfg_')+5:-4]
    
    #Manche Dinge werden direkt ermittelt...
    if bench_id != OSU_ID:
        bin_path = find_binary(profile, bench_id)        
    else:
        bin_path = ''
    #Im fünften Config-Block eines Profils steht potentiell ein händisch gebautes Skript     
    if  len(profile[-1:][0])==0:               
        jobtxt=write_slurm_params(profile,len(profile)-2)
        #Jobname (<=> Profilname)
        jobtxt+='#SBATCH --job-name={}\n'.format(num_workaround+shortened_name)
        #Ziel für Output (sollte in (...)[results] landen)
        if profile[len(profile)-2][10]=='' and bench_id != HPCG_ID:
            jobtxt+='#SBATCH --output={}\n'.format(res_dir+shortened_name+'/'+num_workaround+shortened_name+'.out')
        #Output wird für hpcg manuell in execute_line() gehandelt
        if bench_id == HPCG_ID:
            jobtxt+='#SBATCH --output=/dev/null\n'
        #Ziel für Fehler (sollte in (...)[results] landen)
        if profile[len(profile)-2][11]=='':
            jobtxt+='#SBATCH --error={}\n'.format(res_dir+shortened_name+'/'+num_workaround+shortened_name+'.err')
        jobtxt+='\n'
        #Sourcen von spack   
        jobtxt+='source {}/share/spack/setup-env.sh\n'.format(SPACK_XPTH[:-9])
        #Laden der passenden Umgebung
        jobtxt+= 'spack load {}\n'.format(profile[0][3])   
        jobtxt+='\n'
        #Skriptzeile in der eine Binary ausgeführt wird
        jobtxt+=execute_line(bench_id, bin_path, profile[len(profile)-2][1], profile[len(profile)-2][2], extra_args, res_dir+num_workaround+shortened_name+'/'+num_workaround+shortened_name+'.out', res_dir+num_workaround+shortened_name)
        #TODO: Entladen von Modulen, nötig? Das ist ja ein abgeschlossenes Jobscript...
        #jobtxt+= 'spack unload {}\n'.format(profile[0][3])
    else:
        for i in range(len(profile[-1:][0])):
            jobtxt+=profile[-1:][0][i]
    
    #Niederschreiben des Skripts & Rückgabe des entspr. Pfads hin
    if os.path.isdir(run_dir[:-1])==True:
        file_w(run_dir+'{}.sh'.format(num+shortened_name),jobtxt,'a')
        shell('chmod +x '+run_dir+'{}.sh'.format(num+shortened_name)) 
    return run_dir+'{}.sh'.format(num_workaround+shortened_name)

def execute_line(bench_id, bin_path, node_count, proc_count, extra_args, output, res_dir):
    
    """ 
    >>>>>   script building pipeline (4/5)           <<<<
    >>>>>   final design of the execution line       <<<<
    >>>>>   individual handling per benchmark        <<<<
    """
    
    if full_bin_paths:
        bin_reference = bin_path
    else:
        bin_reference = ''

    txt = ''    
    if bench_id==HPL_ID:
        #we will have access issues regarding hpl.dat if we don't change directory to bin_path, maybe there's a nicer solution
        txt+='cd {}'.format(bin_path)+'\n'
        txt+='mpirun -np {pcount} {bpath}xhpl'.format(pcount = proc_count, bpath = bin_reference)        
    elif bench_id==OSU_ID:
        txt+='mpirun -n {ncount} osu_{exargs}'.format(ncount=node_count,exargs=extra_args)
    elif bench_id==HPCG_ID:
        #All results are automatically saved in the execution directory        
        txt+='cd {}'.format(res_dir[:res_dir.rfind('/')+1]+res_dir[res_dir.rfind('#')+1:])+'\n'
        txt+='mpirun -np {pcount} {bpath}xhpcg; '.format(pcount = proc_count, bpath = bin_reference)
        txt+='mv HPCG*.txt {}.out; mv hpcg*T*.txt hpcg_meta@{}.txt'.format(output[output.rfind('/')+1:-4],output[output.rfind('/')+1:-4])
    
    return txt

def build_plot(t_id, bench,run_dir):

    """ 
    >>>>>   script building pipeline (5/5)           <<<<
    >>>>>   graph drawing via plot.py                <<<<
    >>>>>   individual handling per benchmark        <<<<
    """

    jobtxt=write_slurm_params(cfg_profiles[0][0],3)
    jobtxt+='#SBATCH --job-name='+bench+'_plot\n' 
    jobtxt+='#SBATCH --error='+run_dir.replace('run','res')+'plot.err\n'   
    jobtxt+='#SBATCH --output='+run_dir.replace('run','res')+'plot.out\n\n'   
    jobtxt+= 'python3 {}/plot.py '.format(LOC)+t_id+' '+bench
    
    #Niederschreiben des Skripts & Rückgabe des entspr. Pfads
    if os.path.isdir(run_dir[:-1])==True:
        file_w(run_dir+'plot.sh',jobtxt,'a')
        shell('chmod +x '+run_dir+'plot.sh')
    return run_dir+'plot.sh'

def build_config_to_dat_script(txt,name,run_dir,is_last=False):
  
    """ 
    >>>>>   script building pipeline (2.1/5)         <<<<
    >>>>>   update dat parameters                    <<<<
    """

    jobtxt=write_slurm_params(cfg_profiles[0][0],3)
    jobtxt+='#SBATCH --job-name=cfg_to_dat#{}\n'.format(name) 
    jobtxt+='#SBATCH --error=/dev/null\n\n'  
    jobtxt+='#SBATCH --output=/dev/null\n\n'   
    jobtxt+= txt+'\n'
    
    if is_last:
        jobtxt+='rm {}cfg_to_dat*.sh'.format(run_dir)
        
    if os.path.isdir(run_dir[:-1])==True:
        file_w('{}cfg_to_dat_{}.sh'.format(run_dir,name),jobtxt,'a')
        shell('chmod +x {}cfg_to_dat_{}.sh'.format(run_dir,name))
    
    return '{}cfg_to_dat_{}.sh'.format(run_dir,name)


#Installation
def view_installed_specs(name=0):
    try:
        if name==0:
            return shell('{} find --show-full-compiler'.format(SPACK_XPTH))
        else:
            print('{} find --show-full-compiler '.format(SPACK_XPTH)+name)
            return shell('{} find --show-full-compiler '.format(SPACK_XPTH)+name)  
    
    except Exception as exc:
        error_log('spec:'+str(name), locals(), traceback.format_exc())

#Prüft Specausdruck auf grobe Syntaxfehler
def check_expr_syn(expr, name):
    global menutxt
    expr_list=['@%','%@','^%','%^','^@','@^']
    """
    Hinweis bzgl. regulärem Ausdruck:
    {min,max} min/max vorkommen der vorrangegangenen Zeichenkette 
    \w Symbolmenge: [a-z, A-Z, 0-9, _]            
    * Vorangegangene Zeichenkette kommt beliebig oft vor (inkl. 0 mal)
    (...) Gruppe -> praktisch eine Zeichenkette
    \. Punktsymbol, da einfach nur . für einzelnes Zeichen steht            
    """
    #Nicht abgedeckt @...
    syn_err=re.search(r'@{1,1}(\w*\.*[%]{0,0}\w*)*@{1,}',expr)
    if syn_err:
        message= '\n'+FCOL[6]+'<warning> '+FEND+'profile: '+FCOL[6]+name+FEND+' was deselected! (syntax error: {})\n{}{}\n'.format(syn_err[0],expr,FCOL[8])+('^').rjust(syn_err.span()[0]+1)+('^').rjust(len(syn_err[0])-1)+FEND
        menutxt+=message
        error_log('syntax error in {}: {}\n'.format(name,expr)+('^').rjust(syn_err.span()[0]+21+len(name))+('^').rjust(len(syn_err[0])-1))        
        return message
    
    for _ in expr_list:
        pos=expr.find(_)        
        if pos != -1:           
            message='\n'+FCOL[6]+'<warning> '+FEND+'profile: '+FCOL[6]+name+FEND+' was deselected! (syntax error)\n{}{}\n'.format(expr,FCOL[8])+('^').rjust(pos+1)+FEND+'\n'
            menutxt+=message
            error_log('syntax error in {}: {}\n'.format(name,expr)+('^').rjust(pos+21+len(name)))           
            return message
    return 'True'

#Schreibt Script zum installieren der specs 
#Übergibt alle benötigen Argumente an Install.py
def install_spec(expr):  
    global menutxt
    #Slurmparameter 
    meta=cfg_profiles[0][0][2][0]+'#'+cfg_profiles[0][0][2][1]+'#'+cfg_profiles[0][0][2][2]+'#'+cfg_profiles[0][0][2][3]+'#'+SPACK_XPTH[:-9]
    expr_=''    
    #String aller Specs
    for e in expr:
        expr_+=e[0]+'\$'+e[1]+'#'
    
    #Printen der Job ID klappt noch nicht
    cmd='source {}/share/spack/setup-env.sh ; python3 {}/install.py {} {}'.format(SPACK_XPTH[:-9], LOC,meta,expr_[:len(expr_)-1])
    p=subprocess.run(str(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    
    menutxt+=p.stdout.decode()
    
    #run script    
    if os.path.isfile('{}/install.sh'.format(LOC))==True:
        
        return shell('chmod +x {}/install.sh ; sbatch {}/install.sh'.format(LOC,LOC))

    #Return script path or some informations
    else:
        menutxt+=FCOL[6]+'\n    there is nothing to install'+FEND+'\n'
        menutxt+=FCOL[9]+FORM[0]+'--- script building was canceled ---'+FEND+'\n\n'
        return ''
        
def show_highlights(func, res_id='', bench_tag='', count=1):
    try: 
        clean_values()
        #no specific result_ID
        if res_id == '':
            finished_benchs=check_finished_results(bench=bench_tag)           
            print_finished_results(finished_benchs)             
            while True: 
                answer=input_format()                    
                if int(answer) > (len(finished_benchs)):
                    clear()
                    print_finished_results(finished_benchs,FCOL[9]+'invalid input'+FEND+': to select option »(n) ...« use the corresponding integer »input:n«')
                    continue
                    
                else:
                    for i in range (0,len(finished_benchs)+1,1):
                        if int(answer) == 0:
                            return ''
                        elif int(answer) == i:
                            res=finished_benchs[i-1]
                            res_id=res[res.find('@')+1:-9]
                            pos=res[:res.find('@')].rfind('/')
                            bench_tag=res[pos+1:res.find('_')]                            
                    break                    
                clear()
                print_finished_results(finished_benchs)
        
        elif bench_tag=='':
            finished_benchs=glob.glob('{}/projects/{}*res@{}/plot.out'.format(LOC,bench,res_id))
            res=finished_benchs[0]
            pos=res[:res.find('@')].rfind('/')
            bench_tag=res[pos+1:res.find('_')]
        
        _=read_values(res_id,bench_tag)
        label_pos=2
        
        #length of decimal places
        decimal=6
        #formats number length
        max_len=max([len(str(int(max(i[0][1])))) for i in _[1]])+decimal+1
        
        if _[0][2]=='':
                label_pos=1
        
       
        if func=='max': 
            values=[[str('{:{}.{}f}'.format(max(i[0][1]),max_len,decimal))+' ['+_[0][label_pos]+']',i[0][2][1:i[0][2].find(')')]] for i in _[1]]
        
        elif func=='min':
            values=[[str('{:{}.{}f}'.format(min(i[0][1]),max_len,decimal))+' ['+_[0][label_pos]+']',i[0][2][1:i[0][2].find(')')]] for i in _[1]]
                    
        
        print([max(i[0][1]) for i in _[1]])
        
        return(draw_table(values[:count],t_width,0,0.9,'Highlights ({})'.format(func)))       
       
    except Exception as exc:     
        error_log('', locals(), traceback.format_exc())

def print_finished_results(res_list,txt_=''):
    txt='\n'+ml+FCOL[15]+'<info>'+FEND+ml+'some benchmarks are finished: which result do you wish to inspect??'
    txt+='\n      '+ml+ml+FCOL[0]+'results are sorted by their complition time (newest projects first)\n\n'+FEND
    txt+='      {}(0){} skip'.format(ml+ml+ml,mr)   
    for res in res_list:        
        pos=res[:res.find('@')].rfind('/')
        txt+='\n      {}({}){} {}'.format(ml+ml+ml,str(res_list.index(res)+1),mr,res[pos+1:-9])
    
    if txt_!='':
        txt+='\n\n      '+ml+ml+txt_
        
    print(txt)
    
    
#returns a list of finished benchmarks
def check_finished_results(selected='new',bench=''):
    try:
        finished_benchs=[]
        results = glob.glob('{}/projects/{}*res@*/plot.out'.format(LOC,bench))
        for res in results:
            if selected == 'all' or file_r(res,0).find('fetched')==-1:
                _=file_r(res,0).split()
                
                if len(_)<2:
                    continue
                
                time=_[0]+' '+_[1]
                finished_benchs.append([res,time])
        
        finished_benchs=sorted(finished_benchs.copy(), key=lambda row:(row[1]),reverse=True)
        return [i[0] for i in finished_benchs]        
    except Exception as exc:     
        error_log('', locals(), traceback.format_exc())

"""
Menu Functions

"""

#Hauptmenü
def print_menu(txt = ''):
    global menutxt, get_info
    info = ''
    calc_terminal_size()
    refresh_format_params()
    clear()
    print(FBGR[11]+FORM[0]+'{:^{pos}}'.format('Main Menu', pos=t_width))
    print(FEND+ml+'(0)'+mr+' Exit')
    print(ml+'(1)'+mr+' Options')
    print(ml+'(2)'+mr+' Info')
    print(ml+'(3)'+mr+' View finished runs')
    if (refresh_intervall!=0 and ((time.time()-print_menu.updatetime)>refresh_intervall or print_menu.updatetime==0)) or get_info:
        opt_lines=''
        try:         
            for id in range(len(BENCH_ID_LIST)):
                if id==MISC_ID:
                    continue
                if (function_check(tag_id_switcher(id)+'_menu') and function_check('print_'+tag_id_switcher(id)+'_menu'))!=True:
                    implementation_status = ' '*(int(MAX_TAG_L-len(tag_id_switcher(id))))+FCOL[9]+'--- no menu implementation --- '+FEND
                    get_info = False
                    opt_lines+=ml+'({})'.format(id+3)+mr+' {}'.format(tag_id_switcher(id)).upper()+implementation_status+'\n'
                else:
                    implementation_status = ' '*(int(MAX_TAG_L-len(tag_id_switcher(id))))
                    avail_pkg(id)
                    get_info = False
                    opt_lines+=ml+'({})'.format(id+3)+mr+' {}'.format(tag_id_switcher(id)).upper()+implementation_status+pkg_info[id][0]+pkg_info[id][1]+pkg_info[id][2]+'\n'
            print(opt_lines[:-1])
        except Exception as exc:
            error_log('', locals(), traceback.format_exc())
            for id in range(len(BENCH_ID_LIST)):
                if id==MISC_ID:
                    continue
                print(ml+'({})'.format(id+3)+mr+' {}'.format(tag_id_switcher(id)).upper()+' '*(int(MAX_TAG_L-len(tag_id_switcher(id))))+'... package information refresh failed')               
    else:
        for id in range(len(BENCH_ID_LIST)):
            if id==MISC_ID:
                continue
            if (function_check(tag_id_switcher(id)+'_menu') and function_check('print_'+tag_id_switcher(id)+'_menu'))!=True:
                implementation_status = ' '*(int(MAX_TAG_L-len(tag_id_switcher(id))))+FCOL[9]+'--- no menu implementation --- '+FEND
            else:
                implementation_status = ' '*(int(MAX_TAG_L-len(tag_id_switcher(id))))
            if pkg_info[id][0]!='empty':
                print(ml+'({})'.format(id+3)+mr+' {}'.format(tag_id_switcher(id)).upper()+implementation_status+pkg_info[id][0]+pkg_info[id][1]+pkg_info[id][2]+' {}s ago'.format(int(time.time()-pkg_info[id][3])))
            else:
                print(ml+'({})'.format(id+3)+mr+' {}'.format(tag_id_switcher(id)).upper()+implementation_status)           
    print(ml+'({})'.format(len(BENCH_ID_LIST)+3)+mr+' Errors '+check_err_stack())
    if dbg:
        info='\n'
        info+=FCOL[15]+'subshell-use   '+FEND+'<=> '+FCOL[15]+'$'+FEND+FCOL[7]+'»cmd«                              '+FCOL[0]+'(Debugging)'+FEND+'\n'
        info+=FCOL[15]+'code eval.     '+FEND+'<=> '+FCOL[15]+'code:'+FEND+FCOL[7]+'»pyth. expr«'+FEND+', e.g. '+FEND+FCOL[7]+'»ƒ(...)«    '+FCOL[0]+'(Debugging)'+FEND+'\n'
        info+='\n\n'
    print((info+menutxt).replace('\n','\n'+ml)+str(txt))
    #angesammelte Nachrichten leeren...
    menutxt=''
print_menu.updatetime=0

def menu():
    save_times()
    global error_stack, get_info, menutxt, MAX_TAG_L
 
    for i in BENCH_ID_LIST:
        if i==MISC_ID:
            continue
        if len(str(tag_id_switcher(id)))>MAX_TAG_L:
            MAX_TAG_L = len(str(tag_id_switcher(id)))
    MAX_TAG_L+=len(mr)
 
    #Damit man die Optionen sehen kann
    print_menu(initm)
    
    #Interaktivität mit Nutzereingabe
    while True:
        opt = input_format()

        if opt == '0' or opt == 'q':
            clear()
            #SystemExit(0)
            break
        elif opt == '1' or opt == 'Options':       
            options_menu()
        elif opt == '2' or opt == 'Info':
            #Wir wollen auf jeden Fall auch die package Infos, selbst wenn refresh aus oder zu früh ist
            get_info = True
            if dbg:      
                menutxt+=draw_table(stat_table, t_width, 0, 0.9, title='Boot Up Stats')
                menutxt+='\n'
            if info_feed:
                if spack_problem=='':
                    menutxt+=FCOL[15]+'<info>    '+FEND+'currently used spack binary:   '+FCOL[15]+SPACK_XPTH[:-10]+FEND+FCOL[0]+FEND+SPACK_XPTH[-10:]+FEND+'\n'
                    menutxt+=FCOL[15]+'<info>    '+FEND+'currently used platform:       '+shell(SPACK_XPTH+' arch')+'\n'
                else:
                    menutxt+=FCOL[15]+'<info>    '+FEND+'currently used spack binary:   '+FCOL[6]+SPACK_XPTH[:-10]+FEND+'\n'
                    menutxt+=FCOL[6]+'<warning> '+FEND+'{}\n'.format(spack_problem)
            print_menu('')
        elif opt == '3' or opt == 'View finished runs':
            print_finished_runs_menu()  
            
        elif opt.isdigit() and int(opt)>3 and int(opt)<=len(BENCH_ID_LIST)+2:
            #-2 ist der Offset der die Positionen 'Option' und 'Info' ausgleicht
            try:
                func = globals()['{}_menu'.format(tag_id_switcher(int(opt)-3))]
                func()
                print_menu()
            except KeyError:
                print_menu(FORM[1]+FCOL[9]+'invalid input'+FEND+': this is option is not implemented!')            
        elif opt == str(len(BENCH_ID_LIST)+3):
            menutxt+=show_err_stack()
            print_menu()
        elif opt[0:5] == 'code:':
            r = code_eval(opt[5:])
            print_menu(r)
        elif opt[0] == '$':
            r = str(shell(opt[1:]))
            print_menu(FCOL[15]+'- - - stdout - - -'+FEND+'\n'+r)
        else:
            print_menu(FORM[1]+FCOL[9]+'invalid input'+FEND+': to select option »(n) ...« use the corresponding integer »input:n« ')   

#Options-Menü
def print_options_menu(txt = ''):
    global menutxt
    calc_terminal_size()
    refresh_format_params()
    clear()
    print(FBGR[11]+FORM[0]+'{:^{pos}}'.format('Options', pos=t_width))
    print(FEND+ml+'(0) '+mr+' return to main menu')
    
    print(ml+'(1) '+mr+' clean projects')
    print(ml+'(2) '+mr+' clean error-log (log.txt)')
    print(ml+'(3) '+mr+' clean run-time variables (mem.txt)')
    print(ml+'(4) '+mr+' show bench profiles')
    print(ml+'(5) '+mr+' change form-factor')
    print(ml+'(6) '+mr+' change refresh-intervall')
    print(ml+'(7) '+mr+' dis-/enable colour & format')
    print(ml+'(8) '+mr+' dis-/enable debug mode')
    print(ml+'(9) '+mr+' dis-/enable <info>-feed')
    print(ml+'(10)'+mr+' dis-/enable termination logging')
    print(ml+'(11)'+mr+' dis-/enable path logging')
    print(ml+'(12)'+mr+' dis-/enable whitespace normalization (configs)')
    print(ml+'(13)'+mr+' dis-/enable python installation check')
    
    print(' ')
    print(menutxt.replace('\n','\n'+ml)+'\n'+str(txt))
    #angesammelte Nachrichten leeren...
    menutxt=''

def options_menu():    
    print_options_menu()
    global menutxt, colour_support, refresh_intervall, form_factor_menu
    while True:
        opt = input_format()
        if opt == '0' or opt == 'q':
            clear()
            print_menu()
            break
        elif opt == '1' or opt == 'clean projects':
            print_options_menu(clean('projects'))
        elif opt == '2' or opt == 'clean log':
            print_options_menu(clean('log'))
        elif opt == '3' or opt == 'clean mem':
            print_options_menu(clean('mem'))
        elif opt == '4' or opt == 'show':
            #i = 0
            txt=ml+FCOL[13]+FORM[0]+'which bench do you wish to inspect?'+FEND
            txt+='\n\n'+ml+FBGR[0]+'possible choices:'+FEND+'\n'+ml
            left_size=t_width-len(ml)
            for id in BENCH_ID_LIST:
                if left_size<len(str(id)+' ('+tag_id_switcher(id)+')'+mr):
                    left_size-=len(ml)
                    txt+='\n'+ml
                txt+=FORM[0]+str(id)+' ('+tag_id_switcher(id)+')'+FEND+mr
                left_size-=len(str(id)+' ('+tag_id_switcher(id)+')'+mr)
            print_options_menu(txt)
            print_options_menu(config_out(int(input_format())))
        elif opt == '5' or opt == 'form-factor':
            print_options_menu('...current form-factor: {}\n...please insert the new value'.format(form_factor_menu))
            form_factor_menu = int(input_format())
            file_w('{}/mem.txt'.format(LOC),'form_factor_menu\t\t\t[{}]'.format(str(form_factor_menu)),2)
            calc_terminal_size()
            refresh_format_params()
            print_options_menu(FCOL[4]+'done!'+FEND)
        elif opt == '6' or opt == 'refresh-intervall':
            if refresh_intervall!=0:
                print_options_menu('...current refresh rate is at {}s\n...please insert the new value'.format(refresh_intervall))
            else:
                print_options_menu('...refresh rate is at 0s: information about package availability won\'t be evaluated!\n...please insert the new value')
            refresh_intervall = int(input_format())
            file_w('{}/mem.txt'.format(LOC),'refresh_intervall\t\t\t[{}]'.format(str(refresh_intervall)),3)
            print_options_menu(FCOL[4]+'done!'+FEND)
        elif opt == '7' or opt == 'colour':
            if colour_support==1:
                colour_support = 0
                file_w('{}/mem.txt'.format(LOC),'colour_support\t\t\t[{}]'.format(str(colour_support)),4)
                color_check()
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...colour & format off'+FEND)
            elif colour_support==0:
                colour_support = 1
                file_w('{}/mem.txt'.format(LOC),'colour_support\t\t\t[{}]'.format(str(colour_support)),4)
                color_check()
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...colour & format on'+FEND)
            else:
                print_options_menu(FCOL[9]+'invalid value! (error)'+FEND+'\n colour_support has to be either 0 or 1!')
        elif opt == '8' or opt == 'debug':
            if dbg:
                mode_switch('dbg', 0)
                file_w('{}/mem.txt'.format(LOC),'debug_mode\t\t\t[0]',5)
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...debug mode off'+FEND)
            else:
                mode_switch('dbg', 1)
                file_w('{}/mem.txt'.format(LOC),'debug_mode\t\t\t[1]',5)
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...debug mode on'+FEND)
        elif opt == '9':
            if info_feed==True:
                mode_switch('info_feed', 0)
                file_w('{}/mem.txt'.format(LOC),'info_feed\t\t\t[0]',6)
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...info feed mode off'+FEND)
            else:
                mode_switch('info_feed', 1)
                file_w('{}/mem.txt'.format(LOC),'info_feed\t\t\t[1]',6)
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...info feed mode on'+FEND)
        elif opt == '10':
            if termination_logging==True:
                mode_switch('termination_logging', 0)
                file_w('{}/mem.txt'.format(LOC),'termination_logging\t\t\t[0]',7)
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...termination logging mode off'+FEND)
            else:
                mode_switch('termination_logging', 1)
                file_w('{}/mem.txt'.format(LOC),'termination_logging\t\t\t[1]',7)
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...termination logging mode on'+FEND)
        elif opt == '11':
            if path_logging==True:
                mode_switch('path_logging', 0)
                file_w('{}/mem.txt'.format(LOC),'path_logging\t\t\t[0]',8)
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...path logging mode off'+FEND)
            else:
                mode_switch('path_logging', 1)
                file_w('{}/mem.txt'.format(LOC),'path_logging\t\t\t[1]',8)
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...path logging mode on'+FEND)
        elif opt == '12':
            if auto_space_normalization==True:
                mode_switch('auto_space_normalization', 0)
                file_w('{}/mem.txt'.format(LOC),'auto_space_normalization\t\t\t[0]',9)
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...whitespace normalization mode off'+FEND)
            else:
                mode_switch('auto_space_normalization', 1)
                file_w('{}/mem.txt'.format(LOC),'auto_space_normalization\t\t\t[1]',9)
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...whitespace normalization mode on'+FEND)
        elif opt == '13':
            if check_python_setting==True:
                mode_switch('check_python_setting', 0)
                file_w('{}/mem.txt'.format(LOC),'check_python_setting\t\t\t[0]',10)
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...python check mode off'+FEND)
            else:
                mode_switch('check_python_setting', 1)
                file_w('{}/mem.txt'.format(LOC),'check_python_setting\t\t\t[1]',10)
                print_options_menu(FCOL[4]+'done!'+FEND+FORM[1]+' ...python check mode on'+FEND)
        
        else:
            print_hpl_menu(FORM[1]+FCOL[9]+'invalid input'+FEND+': to select option »(n) ...« use the corresponding integer »input:n« ')

def print_finished_runs_menu(txt = ''):
    global menutxt
    print(txt)
    txt=show_highlights('max')    
    if txt!='':
        print_finished_runs_menu('\n'+txt)
    else:
        print_menu()
#############################
####    functions for    ####
####       - OSU -       ####
#### regulation via menu ####
#############################

def print_osu_menu(txt = ''):
    global menutxt
    calc_terminal_size()
    refresh_format_params()
    clear()
    print(FBGR[11]+FORM[0]+'{:^{pos}}'.format('OSU', pos=t_width))
    print(FEND+ml+'(0)'+mr+' return to main menu')
    print(ml+'(1)'+mr+' run')
    print(ml+'(2)'+mr+' view installed packages')
    print(ml+'(3)'+mr+' install packages')
    print(' ')
    print(menutxt.replace('\n','\n'+ml)+str(txt))
    #angesammelte Nachrichten leeren...
    menutxt='\n'

def osu_menu():
    global menutxt
    print_osu_menu()
        
    while True:
        opt = input_format()
        if opt == '0' or opt == 'q':
            clear()
            return 0
        elif opt == '1' or opt == 'run':
            txt='\n'+ml+FCOL[13]+FORM[0]+'which profiles do you wish to run?\n\n'+FEND
            txt+=ml+FCOL[0]+FORM[0]+'how to reference profiles: \n'+FEND+FCOL[0]+ml+'osu_cfg_test.txt \t\t\t<=> \ttest \n'+ml+'osu_cfg_1.txt,...,osu_cfg_5.txt \t<=> \t1-5 \n\n'+ml+'e.g. valid input: »1-3,test,9 latency«\n'+ml+'     abort: »cancel«\n\n'+FEND
            txt+=ml+FCOL[0]+FORM[0]+'color-coding: \n'+FEND+FCOL[0]+ml+'green \t\t\t\t<=> \tinstalled \n'+ml+'yellow \t\t\t\t<=> \tmissing \n'+ml+'red \t\t\t\t\t<=> \terror '+FORM[1]+'(e.g. invalid specs etc.) '+FEND
            txt+='\n\n'+ml+FCOL[15]+'--- found {} profiles ---'.format(tag_id_switcher(OSU_ID))+FEND+'\n'+ml
            left_size=t_width-len(ml)
            for name in avail_pkg(OSU_ID):
                if left_size<len(name+mr):
                    txt+='\n'+ml
                    left_size=t_width-len(ml)
                txt+=FORM[0]+name+FEND+mr
                left_size-=len(name+mr)
            if spack_problem!='':
                txt+='\n\n'+ml+FCOL[6]+'<warning> '+FEND+'no availability information!\n'+ml+'          reason: {}\n'.format(spack_problem)+'          '+ml+FCOL[6]+SPACK_XPTH+FEND
            print_osu_menu(txt)
            expr=input_format().split()            
            if len(expr)<2:
                txt+='invalid input, possible reason: unspecified test-type e.g. latency'                
                print_osu_menu(txt)

            if expr=='cancel':
                clear()
                return 0
            print(expr[0].replace(' ',''))
            scr_pth = bench_run(OSU_ID, expr[0].replace(' ',''),expr[1])           
            menutxt+='\n'+FCOL[4]+shell('sbatch {}'.format(scr_pth))+FEND
            print_osu_menu('')
        elif opt == '2' or opt == 'view':
            print_osu_menu(view_installed_specs(tag_id_switcher(OSU_ID)))
        elif opt == '3'or opt == 'install':           
            txt='\n'+ml+FCOL[13]+FORM[0]+'which profiles do you wish to install?\n\n'+FEND
            txt+=ml+FCOL[0]+FORM[0]+'how to reference profiles: \n'+FEND+FCOL[0]+ml+'osu_cfg_test.txt \t\t\t<=> \ttest \n'+ml+'osu_cfg_1.txt,...,osu_cfg_5.txt \t<=> \t1-5 \n\n'+ml+'e.g. valid input: »1-3,test,9«\n'+ml+FORM[0]+'     abort: »cancel«\n\n'+FEND
            txt+=ml+FCOL[0]+FORM[0]+'color-coding: \n'+FEND+FCOL[0]+ml+'teal/beige \t\t\t\t<=> \tpot. installable \n'+ml+'grey \t\t\t\t<=> \tinstalled \n'+ml+'red \t\t\t\t\t<=> \terror '+FORM[1]+'(e.g. syntax errors etc.) '+FEND
            txt+='\n\n'+ml+FCOL[15]+'--- found {} profiles ---'.format(tag_id_switcher(OSU_ID))+FEND+'\n'+ml
            left_size=t_width-len(ml)
            for name in avail_pkg(OSU_ID):
                if left_size<len(name+mr):
                    txt+='\n'+ml
                    left_size=t_width-len(ml)
                #replace() enables a different color coding than for run    
                txt+=name.replace(FCOL[7],FCOL[15]).replace(FCOL[4],FCOL[0])+FEND+mr
                left_size-=len(name+mr)
            print_osu_menu(txt)
            
            #preparation for install_spec
            expr=input_format()
            if expr=='cancel':
                clear()
                return 0
            elif expr=='' or expr =='all':
                expr=get_all_specs('osu')
            else:
                names=farg_to_list(expr,'osu')
                expr=get_all_specs('osu',names)   
            print_osu_menu(install_spec(expr))
            
        else:
            print_osu_menu(FORM[1]+FCOL[9]+'invalid input'+FEND+': to select option »(n) ...« use the corresponding integer »input:n« ')


#############################
####    functions for    ####
####       - HPL -       ####
#### regulation via menu ####
#############################

def print_hpl_menu(txt = ''):
    global menutxt
    calc_terminal_size()
    refresh_format_params()
    clear()
    print(FBGR[11]+FORM[0]+'{:^{pos}}'.format('HPL', pos=t_width))
    print(FEND+ml+'(0)'+mr+' return to main menu')
    print(ml+'(1)'+mr+' run')
    print(ml+'(2)'+mr+' view installed packages')
    print(ml+'(3)'+mr+' install packages')
    print(' ')
    #that's the part where we get feedback via menutxt
    print(menutxt.replace('\n','\n'+ml)+str(txt))
    menutxt='\n'

def hpl_menu():
    global menutxt
    print_hpl_menu()
        
    while True:
        opt = input_format()
        if opt == '0' or opt == 'q':
            clear()
            return 0
        elif opt == '1' or opt == 'run':
            txt='\n'+ml+FCOL[13]+FORM[0]+'which profiles do you wish to run?\n\n'+FEND
            txt+=ml+FCOL[0]+FORM[0]+'how to reference profiles: \n'+FEND+FCOL[0]+ml+'hpl_cfg_test.txt \t\t\t<=> \ttest \n'+ml+'hpl_cfg_1.txt,...,hpl_cfg_5.txt \t<=> \t1-5 \n\n'+ml+'e.g. valid input: »1-3,test,9«\n'+ml+'     abort: »cancel«\n\n'+FEND
            txt+=ml+FCOL[0]+FORM[0]+'color-coding: \n'+FEND+FCOL[0]+ml+'green \t\t\t\t<=> \tinstalled \n'+ml+'yellow \t\t\t\t<=> \tmissing \n'+ml+'red \t\t\t\t\t<=> \terror '+FORM[1]+'(e.g. syntax errors etc.) '+FEND
            txt+='\n\n'+ml+FCOL[15]+'--- found {} profiles ---'.format(tag_id_switcher(HPL_ID))+FEND+'\n'+ml
            left_size=t_width-len(ml)
            for name in avail_pkg(HPL_ID):
                if left_size<len(name+mr):
                    txt+='\n'+ml
                    left_size=t_width-len(ml)
                txt+=FORM[0]+name+FEND+mr
                left_size-=len(name+mr)
            if spack_problem!='':
                txt+='\n\n'+ml+FCOL[6]+'<warning> '+FEND+'no availability information!\n'+ml+'          reason: {}\n'.format(spack_problem)+'          '+ml+FCOL[6]+SPACK_XPTH+FEND
            print_hpl_menu(txt)
            expr=input_format()
            if expr=='cancel':
                clear()
                return 0
            scr_pth = bench_run(HPL_ID, expr.replace(' ',''))
            menutxt+='\n'+FCOL[4]+shell('sbatch {}'.format(scr_pth))+FEND
            print_hpl_menu('')
        elif opt == '2' or opt == 'view':
            print_hpl_menu(view_installed_specs(tag_id_switcher(HPL_ID)))
        elif opt == '3'or opt == 'install':           
            txt='\n'+ml+FCOL[13]+FORM[0]+'which profiles do you wish to install?\n\n'+FEND
            txt+=ml+FCOL[0]+FORM[0]+'how to reference profiles: \n'+FEND+FCOL[0]+ml+'hpl_cfg_test.txt \t\t\t<=> \ttest \n'+ml+'hpl_cfg_1.txt,...,hpl_cfg_5.txt \t<=> \t1-5 \n\n'+ml+'e.g. valid input: »1-3,test,9«\n'+ml+'     abort: »cancel«\n\n'+FEND
            txt+=ml+FCOL[0]+FORM[0]+'color-coding: \n'+FEND+FCOL[0]+ml+'teal/beige \t\t\t\t<=> \tpot. installable \n'+ml+'grey \t\t\t\t<=> \tinstalled \n'+ml+'red \t\t\t\t\t<=> \terror '+FORM[1]+'(e.g. syntax errors etc.) '+FEND
            txt+='\n\n'+ml+FCOL[15]+'--- found {} profiles ---'.format(tag_id_switcher(HPL_ID))+FEND+'\n'+ml
            left_size=t_width-len(ml)
            for name in avail_pkg(HPL_ID):
                if left_size<len(name+mr):
                    txt+='\n'+ml
                    left_size=t_width-len(ml)
                #replace() enables a different color coding than for run    
                txt+=name.replace(FCOL[7],FCOL[15]).replace(FCOL[4],FCOL[0])+FEND+mr
                left_size-=len(name+mr)
            print_hpl_menu(txt)
            
            #preparation for install_spec
            expr=input_format()
            if expr=='cancel':
                clear()
                return 0
            elif expr=='' or expr =='all':
                expr=get_all_specs('hpl')
            else:
                names=farg_to_list(expr,'hpl')
                expr=get_all_specs('hpl',names)   
            print_hpl_menu(install_spec(expr))
            
        else:
            print_hpl_menu(FORM[1]+FCOL[9]+'invalid input'+FEND+': to select option »(n) ...« use the corresponding integer »input:n«')


#############################
####    functions for    ####
####      - HPCG -       ####
#### regulation via menu ####
#############################

def print_hpcg_menu(txt = ''):
    global menutxt
    calc_terminal_size()
    refresh_format_params()
    clear()
    print(FBGR[11]+FORM[0]+'{:^{pos}}'.format('HPCG', pos=t_width))
    print(FEND+ml+'(0)'+mr+' return to main menu')
    print(ml+'(1)'+mr+' run')
    print(ml+'(2)'+mr+' view installed packages')
    print(ml+'(3)'+mr+' install packages')
    print(' ')
    #that's the part where we get feedback via menutxt
    print(menutxt.replace('\n','\n'+ml)+str(txt))
    menutxt='\n'

def hpcg_menu():
    global menutxt
    print_hpcg_menu()
        
    while True:
        opt = input_format()
        if opt == '0' or opt == 'q':
            clear()
            return 0
        elif opt == '1' or opt == 'run':
            txt='\n'+ml+FCOL[13]+FORM[0]+'which profiles do you wish to run?\n\n'+FEND
            txt+=ml+FCOL[0]+FORM[0]+'how to reference profiles: \n'+FEND+FCOL[0]+ml+'hpcg_cfg_test.txt \t\t\t<=> \ttest \n'+ml+'hpcg_cfg_1.txt,...,hpcg_cfg_5.txt \t<=> \t1-5 \n\n'+ml+'e.g. valid input: »1-3,test,9«\n'+ml+'     abort: »cancel«\n\n'+FEND
            txt+=ml+FCOL[0]+FORM[0]+'color-coding: \n'+FEND+FCOL[0]+ml+'green \t\t\t\t<=> \tinstalled \n'+ml+'yellow \t\t\t\t<=> \tmissing \n'+ml+'red \t\t\t\t\t<=> \terror '+FORM[1]+'(e.g. syntax errors etc.) '+FEND
            txt+='\n\n'+ml+FCOL[15]+'--- found {} profiles ---'.format(tag_id_switcher(HPCG_ID))+FEND+'\n'+ml
            left_size=t_width-len(ml)
            for name in avail_pkg(HPCG_ID):
                if left_size<len(name+mr):
                    txt+='\n'+ml
                    left_size=t_width-len(ml)
                txt+=FORM[0]+name+FEND+mr
                left_size-=len(name+mr)
            if spack_problem!='':
                txt+='\n\n'+ml+FCOL[6]+'<warning> '+FEND+'no availability information!\n'+ml+'          reason: {}\n'.format(spack_problem)+'          '+ml+FCOL[6]+SPACK_XPTH+FEND
            print_hpcg_menu(txt)
            expr=input_format()
            if expr=='cancel':
                clear()
                return 0
            scr_pth = bench_run(HPCG_ID, expr.replace(' ',''))
            menutxt+='\n'+FCOL[4]+shell('sbatch {}'.format(scr_pth))+FEND
            print_hpcg_menu('')
        elif opt == '2' or opt == 'view':
            print_hpcg_menu(view_installed_specs(tag_id_switcher(HPCG_ID)))
        elif opt == '3'or opt == 'install':           
            txt='\n'+ml+FCOL[13]+FORM[0]+'which profiles do you wish to install?\n\n'+FEND
            txt+=ml+FCOL[0]+FORM[0]+'how to reference profiles: \n'+FEND+FCOL[0]+ml+'hpcg_cfg_test.txt \t\t\t<=> \ttest \n'+ml+'hpcg_cfg_1.txt,...,hpl_cfg_5.txt \t<=> \t1-5 \n\n'+ml+'e.g. valid input: »1-3,test,9«\n'+ml+'     abort: »cancel«\n\n'+FEND
            txt+=ml+FCOL[0]+FORM[0]+'color-coding: \n'+FEND+FCOL[0]+ml+'teal/beige \t\t\t\t<=> \tpot. installable \n'+ml+'grey \t\t\t\t<=> \tinstalled \n'+ml+'red \t\t\t\t\t<=> \terror '+FORM[1]+'(e.g. syntax errors etc.) '+FEND
            txt+='\n\n'+ml+FCOL[15]+'--- found {} profiles ---'.format(tag_id_switcher(HPCG_ID))+FEND+'\n'+ml
            left_size=t_width-len(ml)
            for name in avail_pkg(HPCG_ID):
                if left_size<len(name+mr):
                    txt+='\n'+ml
                    left_size=t_width-len(ml)
                #replace() enables a different color coding than for run    
                txt+=name.replace(FCOL[7],FCOL[15]).replace(FCOL[4],FCOL[0])+FEND+mr
                left_size-=len(name+mr)
            print_hpcg_menu(txt)
            
            #preparation for install_spec
            expr=input_format()
            if expr=='cancel':
                clear()
                return 0
            elif expr=='' or expr =='all':
                expr=get_all_specs('hpcg')
            else:
                names=farg_to_list(expr,'hpcg')
                expr=get_all_specs('hpcg',names)   
            print_hpcg_menu(install_spec(expr))
            
        else:
            print_hpcg_menu(FORM[1]+FCOL[9]+'invalid input'+FEND+': to select option »(n) ...« use the corresponding integer »input:n«')


    
"""
Allgemeine I/O Funktionen
"""

#Lesefunktion: In welche Datei? An welche Position?  
def file_r(name, pos):  
    try:     
        with open(name, 'r') as f:      
            stringlist = f.readlines()
            return stringlist[int(pos)]
    except Exception as exc:
        error_log('target file for reading-operation: '+name+'\nline: '+str(pos), locals(), traceback.format_exc())        

def count_line(name):
     with open (name, 'r') as f:
        num_lines = sum(1 for line in f if line.rstrip())
        return num_lines

#Schreibfunktion: In welche Datei? Welchen Text? An welche Position? bzw. 'a' für anhängen/append
def file_w(name, txt, pos):
    try:
        if(pos!='a'):
            with open(name, 'r') as f:      
                stringlist = f.readlines()
            while len(stringlist)<=pos:
                stringlist.append('\n')           
            stringlist[int(pos)]=txt+'\n'
            with open(name, 'w') as f:
                f.writelines(stringlist)
        else:
            with open(name, "a") as f:     
                f.write(txt+'\n')
    except Exception as exc:
        error_log('target file for writing-operation: '+name+'\nline: '+str(pos)+'\ntext: '+str(txt), locals(), traceback.format_exc())


def get_mem_digit(pos):
    r = str(file_r('{}/mem.txt'.format(LOC), pos))
    r = r[r.find('[')+1:r.find(']')]
    if len(r)>0:
        return int(r)
    else:
        return 0

"""
    try:     
        
    except Exception as exc:     
        error_log('') 
"""
        



"""
Main Initialization
"""

#############################
#####  time stats data  #####
##### - autoregulated - #####
##### various functions #####
#############################

#var.-init-phase starts
init_t = time.time()
#other stats (evaluation in corresponding functions)
evaluate_paths_t = 0
prepare_array_t = 0
check_data_t = 0
check_dirs_t = 0
get_cfg_t = 0
#we're going to aggregate the stats into this list
stat_table = []


#############################
### miscellaneous params. ###
###   - autoregulated -   ###
###   via various func.   ###
###   &com. line args.    ###
#############################

#how do we currently control the program, via flag or via menu?
menu_ctrl=False

#enforces a package info refresh if true
get_info = False

#if true we only produce non-persistent dummy projects
#plausible if we only want to trigger errors along the way
test_only=False

#menu padding (left, quite frequently used)
ml = ''
#menu padding (right, seldom used)
mr = ''


#############################
### *important constants* ###
###    first point for    ###
###   expansion of supp.  ###
###       benchmarks      ###
#############################

#supported benchmarks (HPL, OSU, ...) and their IDs
MISC_ID = 0
HPL_ID = 1
OSU_ID = 2
HPCG_ID = 3

#we also want to have something iterable corresponding to our supported benchmarks
BENCH_ID_LIST = [MISC_ID, HPL_ID, OSU_ID, HPCG_ID]
BENCHS_WITHOUT_EXTRA_ARGS =[HPL_ID,HPCG_ID]

#format: tag, offset in local config files, offset in package config files (like HPL.dat)  
TRANSFER_PARAMS = [['hpl', 16, 2, 'HPL.dat'], ['hpcg', 12, 2, 'hpcg.dat']]


#############################
###   info. aggregation   ###
###   - autoregulated -   ###
###   various functions   ###
#############################

#initial message for menu boot up
initm = ''

#most important culmination point for <info>,<warning> strings etc.
menutxt=''

#Sammelt kürzliche Fehlermeldungen
error_stack = []

#we memorize the most serious problem regarding the specified path to the spack binary
spack_problem = ''

#info array regarding availability of packages; first entry (<=> MISC_ID) is a dummy
#pattern: [[<<available>>, <<miss>>, <<error>>], ...]
pkg_info = []

#Trägt Informationen des Config-Ordners; Ersteintrag für Metadaten
#Index: [Benchmark-id][Profil-Nr.][Abschnitt][Zeile im Abschnitt]
cfg_profiles = [[],[],[],[]]

#Pfade zu den Benchmarks (Index <=> Benchmark-ID; Ersteintrag führt zur allg. config!)
BENCH_PTHS = []

#python will check per default
#check_python_setting = True

#############################
#####  important paths  #####
#####  - userdefined -  #####
#####     mostly via    #####
#####     config.txt    #####
#############################

try:
    #location of sb.py
    LOC = str(os.path.dirname(os.path.abspath(__file__)))

    evaluate_paths()

    #location of the program that transfers benchmark settings from our configs to the actual package
    CONFIG_TO_DAT_XPTH = LOC+'/config_to_dat.py'

    #location of the spack binary (validity will be tested down the line)
    SPACK_XPTH = config_cut(file_r(BENCH_PTHS[MISC_ID]+'config.txt', 4)).rstrip()

    #from what root do we look for spack installations?
    SPACK_SEARCH_ROOT = config_cut(file_r(BENCH_PTHS[MISC_ID]+'config.txt', 5)).rstrip()
    
    prepare_array()
    
    get_cfg(tag_id_switcher(MISC_ID))
    
    #should python installation be checked 
    check_data()
    check_python_setting=int(get_mem_digit(10))
    extensive_spack_evaluation()
    
    

    #where do want our results to be stored in?
    PROJECT_PTH=str(file_r(BENCH_PTHS[MISC_ID]+'config.txt', 6)).rstrip()
    if os.path.isdir(PROJECT_PTH[:PROJECT_PTH.find('/project')])==False:
            PROJECT_PTH=LOC+'/projects'
            file_w(BENCH_PTHS[MISC_ID]+'config.txt',PROJECT_PTH,6)

    #python version for matplotlib (e.g. python%gcc@8.5.0) [TODO?]
    PYTHON_MATPLOTLIB = ''
    
except Exception as exc:
    error_log('failed to calculate basic paths', locals(), traceback.format_exc())
    initm+='\n'+ml+FCOL[6]+'<warning> '+FEND+'failed to calculate basic paths'


#############################
#####  special options  #####
#####  - userdefined -  #####
#####     mostly via    #####
#####       mem.txt     #####
#############################

#this option wasn't discarded for legacy reasons (unavailable via mem.txt)
full_bin_paths=False

#size of the terminal (unavailable via mem.txt)
t_width = 300
try:
    calc_terminal_size()
except Exception as exc:
    error_log('failed to determine the terminal width', locals(), traceback.format_exc())
    initm+='\n'+ml+FCOL[6]+'<warning> '+FEND+'failed to determine the terminal width'

#regular settings (these are via mem.txt)
try:
    #scales elements in the menu; 0 <=> center aligned text (originally, not fully implemented)
    form_factor_menu = int(get_mem_digit(2))
    refresh_format_params()
    #how often availability information regarding packages should be refreshed (might take a time!)
    refresh_intervall = int(get_mem_digit(3))
    #whether we support colored output
    colour_support = int(get_mem_digit(4))
    color_check()    
        
    #these might help to regulate excessive logging
    mode_switch('dbg', int(get_mem_digit(5)))
    mode_switch('info_feed', int(get_mem_digit(6)))
    mode_switch('termination_logging',int(get_mem_digit(7)))
    mode_switch('path_logging',int(get_mem_digit(8)))
    mode_switch('auto_space_normalization',int(get_mem_digit(9)))    
except Exception as exc:
    error_log('failed to read settings from: '+LOC+'mem.txt', locals(), traceback.format_exc())
    initm+='\n'+ml+FCOL[6]+'<warning> '+FEND+'failed to read settings from: '+LOC+'mem.txt'

#############################
####  last init-actions  ####
#############################

clean_dummy_projects()
#prepare_array()
#check_data()
check_dirs()
#get_cfg(tag_id_switcher(MISC_ID))

#relevant for better indentation in menu functions 
MAX_TAG_L = 0


#############################
#####  init-phase ends  #####
#############################
init_t = time.time()-init_t


def main():
    cl_arg()

    
if __name__ == "__main__":
    main()
