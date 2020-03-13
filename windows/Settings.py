# This module is part of the core Basondole Tools
# This code provides a settings window to control various settings of Basondole Tools
# Creates a hidden settings file in the current directory


import yaml
import os
import re
import subprocess


from other.Essential import resource_path


__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"

program_icon =resource_path(r'paul-icon1.ico')
warning_icon = resource_path(r'warning-icon.png')



def savesettings(settings):


    subprocess.check_call(["attrib","-H","main.conf"])

    with open('main.conf','w') as settingsfile:
        settingsfile.write('---\n')
        for key,value in settings.items(): 
            settingsfile.write(key+': '+value+'\n')
        settingsfile.write('\n')
        settingsfile.write('...\n')

    subprocess.check_call(["attrib","+H","main.conf"])

    return




def readsettings():
    try:

        with open('main.conf') as settings:
            setdict = yaml.load(settings, Loader=yaml.BaseLoader)


        if not setdict['general-authentication-server']:
            return 'Authentication server not found \nPlease go to general settings tab \nand specify the authentication server \n'
            
        if not setdict['general-database']:
            return 'Devices database not found \nPlease go to general settings tab \nand specify the database full path \n'
        
        try:
            if not setdict['bgp-neighbor-monitor-timer']:
                setdict['bgp-neighbor-monitor-timer'] = 5 #minutes
        except KeyError:
            setdict['bgp-neighbor-monitor-timer'] = 5 #minutes

        return setdict

    except (IOError,TypeError,FileNotFoundError):
        msg = "Settings missing. General settings are required for system to work. Please setup the system"
        return msg
