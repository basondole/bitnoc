# This module is part of the core Basondole Tools
# This is an initializing module used to gather data about hosts and verify user credentials

import re
import sys
import time
import socket
import paramiko
import threading
import yaml
from napalm import get_network_driver
from other.Essential import dotted
import copy

__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"

class Device:

   def __init__(self,username,password,path=None, dictdb=None):
       ''' Read the device attributes from a YAML file and return a dictionary
       '''
       
       if not dictdb:
        dictdb = readfile(path=path)

       # append new dictionary keys for instances, interfaces and errors logging
       _dictdb = {}
       for host in dictdb:
          if not dictdb[host]: continue
          _dictdb[host] = dictdb[host]
          _dictdb[host]['errors'] = {}
          _dictdb[host]['interfaces'] = []
          _dictdb[host]['instances'] = {}
          _dictdb[host]['xconnects'] = [('up',0),('down',0)]
          _dictdb[host]['policers'] = []
          _dictdb[host]['serialnumber'] = ''
          _dictdb[host]['version'] = ''
          _dictdb[host]['model'] = ''
          _dictdb[host]['hostid'] = ''
          _dictdb[host]['synced'] = False

       self.readfile = dictdb

       dictdb = _dictdb
       # create dotted dict
       self.devicesdict = dotted(dictdb)
       self.username = username
       self.password = password


   def database(self):
      return self.devicesdict


   def get_data(self):

     threads = []
     for host in self.devicesdict.keys():
        process = threading.Thread(target=Device.bigData, args=(self.username,self.password,host,self.devicesdict))
        process.start()
        threads.append(process)
     for process in threads:
        process.join()

     devicesDict = dotted(self.devicesdict)

     return devicesDict


   @staticmethod
   def connect(username,password,host,devicesDict,sshClient):
      #with lock: print (time.ctime()+" (user = "+username+") authentication starting " + host.rjust(15))
      try:
         sshClient.connect(host, username=username, password=password, timeout=40,allow_agent=False,look_for_keys=False)
         connected = True

      except (socket.error, paramiko.AuthenticationException):
         connected = False
         devicesDict[host]['errors']['connect'] = time.ctime()+' failed authentication'
         devicesDict[host]['policers'] = ['Null']
         devicesDict[host]['interfaces'] = ['Null']

      return connected

   @staticmethod
   def setTerminal(secureCli,software):
   
      if software == 'junos':
         secureCli.send('set cli screen-length 0\n')
         secureCli.send('set cli screen-width 0\n')
         time.sleep(0.5)
         secureCli.recv(65535)

      if software == 'ios':
         secureCli.send('terminal length 0\n')
         secureCli.send('terminal width 0\n')
         time.sleep(0.5)
         secureCli.recv(65535)

   @staticmethod
   def cli(host, username, password, sshClient):
      try: secureCli = sshClient.invoke_shell()
      except Exception:
         sshClient.connect(host, username=username, password=password, timeout=40,allow_agent=False,look_for_keys=False)
         secureCli = sshClient.invoke_shell()
      return secureCli


   @staticmethod
   def showInterfaces(secureCli,devicesDict,host):
          all_output = ''
          time.sleep(1)
          try:
              if devicesDict[host]['software'] == 'junos':
                 Device.setTerminal(secureCli,'junos') # set cli parameters widht and length
                 secureCli.send('show interfaces terse | except "\.|^ "\n')

              elif devicesDict[host]['software'] == 'ios':
                 Device.setTerminal(secureCli,'ios') # set cli parameters widht and length
                 secureCli.send('show interfaces description | exclude \.\n')
          except Exception as e:
            devicesDict[host]['errors']['interfaces'] = str(e)
            return

          time.sleep(5)
          secureCli.close()
          while True:
             output = secureCli.recv(65535).decode("utf-8")
             if not output: break
             for line in output: all_output += str(line)

          devicesDict[host]['interfaces']= format.interfaces(all_output)


   @staticmethod
   def showInstances(secureCli,devicesDict,host):

          all_output = ''
          time.sleep(1)
          try:
            if devicesDict[host]['software'] == 'junos':
               Device.setTerminal(secureCli,'junos') # set cli parameters widht and length
               secureCli.send('show configuration routing-instances | match "^[aA0-zZ9]"\n')

            elif devicesDict[host]['software'] == 'ios':
               Device.setTerminal(secureCli,'ios') # set cli parameters widht and length
               secureCli.send('show run vrf | i ^vrf definition|^ip vrf\n')
          except Exception as e:
            devicesDict[host]['errors']['instances'] = str(e)
            return

          time.sleep(5)
          secureCli.close()
          while True:
             output = secureCli.recv(65535).decode("utf-8")
             if not output: break
             for line in output: all_output += str(line)

          devicesDict[host]['instances']= (format.instances(devicesDict,host,all_output))


   @staticmethod
   def showXconnects(secureCli,devicesDict,host):

          all_output = ''
          time.sleep(1)
          try:
            if devicesDict[host]['software'] == 'junos':
               Device.setTerminal(secureCli,'junos') # set cli parameters widht and length
               secureCli.send('show l2circuit connections summary\n')

            elif devicesDict[host]['software'] == 'ios':
               Device.setTerminal(secureCli,'ios') # set cli parameters widht and length
               secureCli.send('show xconnect all\n')
          except Exception as e:
            devicesDict[host]['errors']['xconnects'] = str(e)
            return

          time.sleep(5)
          secureCli.close()
          while True:
             output = secureCli.recv(65535).decode("utf-8")
             if not output: break
             for line in output: all_output += str(line)

          devicesDict[host]['xconnects']= (format.xconnects(devicesDict,host,all_output))


   @staticmethod
   def showPolicers(secureCli,devicesDict,host):

      all_output = ''
      time.sleep(1)
      try:
         if devicesDict[host]['software'] == 'junos':
            Device.setTerminal(secureCli,'junos') # set cli parameters widht and length
            secureCli.send('show configuration firewall | match ^policer\n')

         elif devicesDict[host]['software'] == 'ios':
            Device.setTerminal(secureCli,'ios') # set cli parameters widht and length
            secureCli.send('show running-config | include ^policy-map\n')
      except Exception as e:
         devicesDict[host]['errors']['policers'] = str(e)
         return

      time.sleep(5)
      secureCli.close()
      while True:
         output = secureCli.recv(65535).decode("utf-8")
         if not output: break
         for line in output: all_output+=str(line)

      devicesDict[host]['policers'] = format.policers(devicesDict,host,all_output)
      devicesDict[host]['policers'].insert(0,'Unlimited')


   @staticmethod
   def assign_napalm_driver(devicesDict,host,username,password):
      ''' assign a napalm driver
      '''
      junosdriver = get_network_driver('junos')
      iosdriver = get_network_driver('ios')

      if devicesDict[host].software == 'ios':
          devicesDict[host].napalm = iosdriver(username=username,password=password,hostname=host,timeout=40)

      if devicesDict[host].software == 'junos':
          devicesDict[host].napalm = junosdriver(username=username,password=password,hostname=host,timeout=40)


   @staticmethod
   def facts(devicesDict,host):
      ''' Get device facts using napalm drivers
      '''

      try: devicesDict[host]['napalm'].open()
      except: return {}

      facts = devicesDict[host]['napalm'].get_facts()

      _facts = {'serialnumber': facts['serial_number'],
                'version': facts['os_version'],
                'model': facts['model'],
                'hostid': facts['hostname']}
       
      devicesDict[host]['napalm'].close()
       
      devicesDict[host].update(_facts)

      return _facts


   @staticmethod
   def genarate_logical_system_data(host,devicesDict,sshClient,username,password):

      if devicesDict[host]['errors']: return # return if the main system has errors

      if devicesDict[host]['logicalsystem']:
        
          for logicalsystem in  devicesDict[host]['logicalsystem'].keys():

              secureCli = Device.cli(host, username, password, sshClient)
              Device.setTerminal(secureCli,'junos') # set cli parameters widht and length
              secureCli.send('show configuration logical-system '+logicalsystem+' firewall | match ^policer\n')
              time.sleep(5)
              secureCli.close()
              policers_output = ''
              while True:
                 output = secureCli.recv(65535).decode("utf-8")
                 if not output: break
                 for line in output: policers_output += str(line)


              secureCli = Device.cli(host, username, password, sshClient)
              Device.setTerminal(secureCli,'junos') # set cli parameters widht and length
              secureCli.send('show configuration logical-system '+logicalsystem+' routing-instances | match "^[aA0-zZ9]"\n')
              time.sleep(5)
              secureCli.close()
              instances_output = ''
              while True:
                 output = secureCli.recv(65535).decode("utf-8")
                 if not output: break
                 for line in output: instances_output += str(line)


              secureCli = Device.cli(host, username, password, sshClient)
              Device.setTerminal(secureCli,'junos') # set cli parameters widht and length
              secureCli.send('show l2circuit connections summary logical-system '+logicalsystem+'\n')
              time.sleep(5)
              secureCli.close()
              xconnects_output = ''
              while True:
                 output = secureCli.recv(65535).decode("utf-8")
                 if not output: break
                 for line in output: xconnects_output += str(line)


              ls_ip = devicesDict[host]['logicalsystem'][logicalsystem]['ip']

              devicesDict[ls_ip] = {'policers': ['Unlimited'] + format.policers(devicesDict,host,policers_output),
                                    'instances': format.instances(devicesDict,host,instances_output),
                                    'xconnects': format.xconnects(devicesDict,host,xconnects_output),
                                    'software': devicesDict[host]['software'],
                                    'napalm': devicesDict[host]['napalm'],
                                    'hostname': devicesDict[host]['hostname']+"--"+logicalsystem,
                                    'logicalsystem': None,
                                    'systemname': logicalsystem,
                                    'interfaces': devicesDict[host]['interfaces'],
                                    'residentblock': devicesDict[host]['logicalsystem'][logicalsystem]['residentblock'],
                                    'mainsystemip': host,
                                    'synced' : True}
              

   @staticmethod
   def bigData(username,password,host,devicesDict):

       sshClient = paramiko.SSHClient()
       sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
       try:
         authenticated = Device.connect(username,password,host,devicesDict,sshClient)

         if authenticated == True:

            Device.assign_napalm_driver(devicesDict,host,username,password)
            
            secureCli = Device.cli(host, username, password, sshClient)
            Device.showInterfaces(secureCli,devicesDict,host)

            secureCli = Device.cli(host, username, password, sshClient)
            Device.showInstances(secureCli,devicesDict,host)

            secureCli = Device.cli(host, username, password, sshClient)
            Device.showXconnects(secureCli,devicesDict,host)

            secureCli = Device.cli(host, username, password, sshClient)
            Device.showPolicers(secureCli,devicesDict,host)

            Device.facts(devicesDict,host)

            Device.genarate_logical_system_data(host,devicesDict,sshClient,username,password)


            if not devicesDict[host]['errors']: devicesDict[host].synced = True

            sshClient.close()


       except socket.error:
          devicesDict[host]['errors']['socket'] = time.ctime()+' failed to connect'
          devicesDict[host]['policers'] = ['Null']
          devicesDict[host]['interfaces'] = ['Null']








class format:

   @staticmethod
   def interfaces(output):
      output = output.split('\n')
      for line in output:
         if re.findall(r'^Interface',line):
            _line = line
            break

      try:
         interfaceList = []
         for x in range(output.index(_line)+1,len(output)-1):
            if output[x] != '\r':
               interfaceList.append(output[x].split()[0])

      except Exception: pass

      return interfaceList


   @staticmethod
   def policers(devicesDict,ip,output):
      output = output.split('\n')
      policerList = []
      if devicesDict[ip]['software'] == 'ios': regex = r'^policy-map'
      if devicesDict[ip]['software'] == 'junos': regex = r'^policer'
      for item in output:
            if re.findall(regex,item):
               policerList.append(item.split()[1])
      return policerList

   
   @staticmethod
   def instances(devicesDict,ip,output):
      output = output.split('\n')
      instancesList = []
      if devicesDict[ip]['software'] == 'ios': 
         for line in output:
            if re.findall(r'(# )?show run vrf',line): # line where show command was issued
               _line = line

         for x in range(output.index(_line)+1,len(output)-1):
            # if line does not start with a word character skip
            # to avoid lines with preceeding white space
            if not re.search(r'^\S',output[x]): continue
            instancesList.append(output[x].split()[-1])

      if devicesDict[ip]['software'] == 'junos':
         for line in output:
            if re.findall(r'(> )?show configuration',line):  # line where show command was issued
               _line = line

         for x in range(output.index(_line)+1,len(output)-1):
            # if line does not start with a word character skip
            # to avoid lines with preceeding white space
            if not re.search(r'^\S',output[x]) or 'inactive' in output[x]:
               continue
            instancesList.append(output[x].split()[0])

      return instancesList


   @staticmethod
   def xconnects(devicesDict,ip,output):
      output = output.split('\n')
      xconnects = []

      up_circuits = 0
      down_circuits = 0

      if devicesDict[ip]['software'] == 'ios': 
         for line in output:
            if re.search(r'^DN',line):
               down_circuits += 1

            elif re.search(r'^UP',line):
               up_circuits += 1


      if devicesDict[ip]['software'] == 'junos':
          for line in output:
            vcs = re.findall(r'(up|down): (\d)+',line) # format [('up', '0'), ('down', '1')]

            if vcs:
                 up_circuits += int(vcs[0][1])
                 down_circuits += int(vcs[1][1])

      xconnects = [('up',up_circuits),('down',down_circuits)]

      return xconnects



def readfile(path=None):
   if path:
      path = path.replace('\\','/')
      if path.strip()[-1] != '/': devicefilepath = path+'/devices.yml'
      else: devicefilepath = path+'devices.yml'
   else: devicefilepath = 'devices.yml'

   with open(devicefilepath) as file:
      dictdb = yaml.load(file, Loader=yaml.BaseLoader)

   if not dictdb: dictdb = {}

   return dictdb

def ip_to_name_as_key(device_dict):

  devlist = list(device_dict.keys())
  devdata = {} # hostname is the key in this dict
  for dev in devlist:
    name = device_dict[dev]['hostname']
    devdata[name] = copy.copy(dict(device_dict[dev]))
    devdata[name]['ip'] = dev
    if device_dict[dev]['logicalsystem']:
      for subsystem in device_dict[dev]['logicalsystem']:
        devdata[ f'{name}--{subsystem}' ] = copy.copy(dict(device_dict[dev]))
        devdata[ f'{name}--{subsystem}' ]['hostname'] = f'{name}--{subsystem}'
        devdata[ f'{name}--{subsystem}' ]['systemname'] = subsystem
        devdata[ f'{name}--{subsystem}' ]['logicalsystem'] = subsystem
        devdata[ f'{name}--{subsystem}' ]['ip'] = device_dict[dev]['logicalsystem'][subsystem]['ip']
        devdata[ f'{name}--{subsystem}' ]['mainsystemip'] = dev


  return devdata

def verifyUser(username,password,server=None):
    ''' Verifies the user credential by login to the server
    '''
    if server: host = server
    else: return

    sshClient = paramiko.SSHClient()
    sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
       sshClient.connect(host, username=username, password=password,
                         timeout=40,allow_agent=False,look_for_keys=False)
       authenticated = True
    except (socket.error, paramiko.AuthenticationException):
       print(time.ctime()+" (user = "+username+") failed authentication > "+host.rjust(15))
       return None # no username and password


    if authenticated:
       sshClient.close()
       return username,password


