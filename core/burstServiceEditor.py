# This code provides methods for gu client to interact with server to manage the data file used by burstman
# The data file will be stored on a server
# This code is used as a client to manage the file on the server


import re
import paramiko
import socket
from windows.WindowDialog import Dialog
from windows.WindowOutput import Display
from other.Essential import delEmptyLine, resource_path


__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"

warning_icon = resource_path(r"warning-icon.png")
cancel_icon = resource_path(r"cancel-icon.png")
check_icon = resource_path(r"check-icon.png")

class BurstServer():

   def __init__(self,server,clientfile,keypath,parent=None,port=22):

      self.parent = parent
      self.port = port
      self.server = server
      self.clientfile = clientfile
      self.sshClient = paramiko.SSHClient()
      self.sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      self.up = True

      try: self.key = paramiko.RSAKey.from_private_key_file((keypath))
      except Exception as e:
         Dialog(self.parent,prompt='Error bad private key: '+str(e)+'\n',icon=cancel_icon)
         self.up = False
         return


      #try to connect without credentials to check if server is up
      try:
         self.sshClient.connect(self.server,timeout=10,port=self.port)
         self.sshClient.close()
      except paramiko.ssh_exception.AuthenticationException: pass
      except socket.timeout:
         self.up = False
         Dialog(self.parent,prompt='Error: '+self.server+' Server timed out\n',icon=cancel_icon)
         return
      except Exception as e:
         self.up = False
         Dialog(self.parent,prompt='Error:'+str(e)+'\n',icon=cancel_icon)
         return


   def get_file_from_server(self,serverlogin):

      command = 'cat '+self.clientfile

      try:
         self.sshClient.connect(self.server, username = serverlogin, pkey = self.key, port=self.port)

         stdin , stdout, stderr = self.sshClient.exec_command(command)
         strfile = stdout.read().decode("utf-8")
         self.sshClient.close()

      except Exception as e:
         Dialog(self.parent,prompt=str(e)+'\n',icon=cancel_icon)
         strfile = ''

      return strfile



   def save_file_to_server(self,serverlogin,cleanFile):

      if not cleanFile:
         ans = Dialog(self.parent,
                      prompt='The client database is going to be deleted\nIf this is not an error click ok to delete\n',
                      icon=cancel_icon)
         if ans.lower() != 'ok' : return

      command = 'echo "'+cleanFile+'" > '+self.clientfile

      try:
         self.sshClient.connect(self.server, username = serverlogin, pkey = self.key, port=self.port)

         stdin , stdout, stderr = self.sshClient.exec_command(command)
         self.sshClient.close()

      except Exception as e: Dialog(self.parent,prompt=str(e)+'\n',icon=cancel_icon)

      return



class kazi():


   def __init__(self,server,serverlogin,clientfile,keypath,parent=None,port=None):

      self.warning = warning_icon
      self.error = cancel_icon
      self.ok = check_icon

      self.server = server
      self.login = serverlogin

      self.status = BurstServer(self.server,clientfile,keypath,parent=parent,port=port)



   def add(self,parent,data):

      ip,interface,vlan = data['ip'], data['interface'], data['vlan']

      clientsdata = self.view(parent,get=True) # collect existing clients information

      if type(clientsdata) == dict: # if the value is dict sometimes it is string
         try: 
            clientsdata[ip]['interfaces'][interface][vlan] # check if the client already exists
            proceed = Dialog(parent,
                      prompt='\n'.join(['Client alread exists in package:',
                                        'CIR: '+clientsdata[ip]['interfaces'][interface][vlan]['daybandwidth'],
                                        'PIR: '+clientsdata[ip]['interfaces'][interface][vlan]['nightbandwidth'],
                                        'Time: '+clientsdata[ip]['interfaces'][interface][vlan]['days']+' '+clientsdata[ip]['interfaces'][interface][vlan]['starttime']+' - '+clientsdata[ip]['interfaces'][interface][vlan]['endtime'],
                                        'Proceed anyway? \n']),
                      icon= self.warning)

            if proceed.ans.lower() != 'ok': return

         except KeyError: pass


      update = self.format_client_data(data) # create a single text line of client data


      if self.status.up: # if the server is up

         clientList, removed = self.deleteClient(ip,interface,vlan) # delete existing data for the service
         clientList = clientList + [update] # append the new data as a list
         strfile = '\n'.join(clientList) # create a string from the list
         cleanFile = delEmptyLine(strfile) # remove empty lines

         self.status.save_file_to_server(self.login,cleanFile) # save the uppdated file to server

         Dialog(parent,prompt= 'Client file updated successfully\n', icon=self.ok, button=False)

      else: Dialog(parent,prompt='Can not access server \n'+self.server+' \n', icon=self.error)



   def remove(self,parent,data):

      ip,interface,vlan = data['ip'], data['interface'], data['vlan']

      if self.status.up:
         clientList, removed = self.deleteClient(ip,interface,vlan)

         if removed:
            strfile = '\n'.join(clientList)
            cleanFile = delEmptyLine(strfile)
            self.status.save_file_to_server(self.login,cleanFile)
            Dialog(parent,prompt= 'Client file updated successfully\n',icon=self.ok, button=False)

         else: Dialog(parent,prompt= '\nClient not found on '+ip+' interface '+interface+'.'+vlan,icon=self.error)

      else: Dialog(parent,prompt='Can not access server \n'+self.server+' \n',icon=self.error)



   def update(self,parent,data):

      ip,interface,vlan = data['ip'], data['interface'], data['vlan']

      update = self.format_client_data(data)

      if self.status.up:

         clientList, removed = self.deleteClient(ip,interface,vlan)
         clientList = clientList + [update] # append the new data as a list
         strfile = '\n'.join(clientList)
         cleanFile = delEmptyLine(strfile)
         self.status.save_file_to_server(self.login,cleanFile)

         outputtext = ''
         outputtext+= '\n'
         outputtext+= 'Removed:'
         outputtext+= '--------'
         outputtext+= removed
         outputtext+= '\n'
         outputtext+= 'Added:'
         outputtext+= '------'
         outputtext+= update.strip()
         outputtext+= '\n'
         outputtext+= 'Client file updated successfully\n'

         Display('Burst clients',outputtext,parent,self)

      else: Dialog(parent,prompt='Can not access server \n'+self.server+' \n',icon=self.error)




   def view(self,parent,updatecursor = False, get=False):

      output = ''

      if updatecursor:
         parent.config(cursor="wait") #show a busy cursor on the main app window
         parent.update()

      if self.status.up:
         clients = self.status.get_file_from_server(self.login)

         if get:
            _dic = {} # a dict to collect data for each client
            for line in clients.split('\n'):
               _line = line.split('interface')
               _pe = _line[0].lstrip('pe=').strip() # get the pe address
               if _pe not in _dic and _pe.strip(): _dic[_pe] = {'interfaces':{}} # add the pe ip to the dict
               if _pe:
                  interface = (re.findall(r'interface\=(\S+)',line))[0]
                  if not interface in _dic[_pe]['interfaces']: _dic[_pe]['interfaces'][interface] = {}
                  vlan = (re.findall(r'vlan\=(\S+)',line))[0]
                  if not vlan in _dic[_pe]['interfaces'][interface]:

                     _dic[_pe]['interfaces'][interface][vlan]={'daybandwidth':((re.findall(r'daybandwidth\=(\S+)',line))[0]),
                                                               'nightbandwidth':((re.findall(r'nightbandwidth\=(\S+)',line))[0]),
                                                               'starttime':((re.findall(r'starttime\=(\S+)',line))[0]),
                                                               'endtime':((re.findall(r'endtime\=(\S+)',line))[0]),
                                                               'days':((re.findall(r'days\=(\S+)',line))[0]),
                                                               'name':((re.findall(r'name\=(\S+)',line))[0])}


            return _dic



         for sn, line in enumerate(clients.split('\n')):
             if sn%50==0:
               output+= 'EDGE'.ljust(17)+'INTERFACE'.ljust(10)+'VLAN'.ljust(6)+'DAYBANDWIDTH'.ljust(17)+'NIGHTBANDWIDTH'.ljust(17)+'START'.ljust(6)+'END'.ljust(6)+'DAYS'.ljust(10)+'NAME'+'\n'
               output+= '----'.ljust(17)+'---------'.ljust(10)+'----'.ljust(6)+'------------'.ljust(17)+'--------------'.ljust(17)+'-----'.ljust(6)+'---'.ljust(6)+'----'.ljust(10)+'----'+'\n'

             for index, item in enumerate(re.findall(r'\=(\S+)',line)):
               if index==0: output+= item.ljust(17) # EDGE
               if index==1: output+= item.ljust(10) # INTERFACE
               if index==2: output+= item.ljust(6)  #VLAN
               if index==3: output+= item.ljust(17) #DAYBANDWIDTH
               if index==4: output+= item.ljust(17) #NIGHTBANDWIDTH
               if index==5: output+= item.ljust(6)  #STARTTIME
               if index==6: output+= item.ljust(6)  #ENDTIME
               if index==7: output+= item.ljust(10) #DAYS APPLICABLE
               if index==8: output+= item           # SERVICE NAME

             output+='\n'

      else: Dialog(parent,prompt='Can not access server \n'+self.server+' \n',icon=self.error)


      return output





   def deleteClient(self,ip,interface,vlan):

      regex = r'.*'+ip+'.*'+interface+'.*'+vlan
      clients = self.status.get_file_from_server(self.login)
      clients = clients.split('\n')

      removed = ''
      # collect all the matchig lines
      index = [line for line in clients if re.match(regex,line)]

      for line in index:
         clients.remove(line) # delete the matched lines
         removed += line+'\n' # record the deleted lines

      return clients, removed # return data list and string



   def format_client_data(self,data):
      ''' combines data about a client in a single line
      '''
      pe = 'pe='+data['ip'].ljust(15)
      interface = 'interface='+data['interface'].ljust(8)
      vlan = 'vlan='+data['vlan'].ljust(4)
      daybandwidth = 'daybandwidth='+data['cir'].ljust(14)
      nightbandwidth = 'nightbandwidth='+data['pir'].ljust(14)
      starttime = 'starttime='+data['start'].ljust(4)
      endtime = 'endtime='+data['end'].ljust(4)
      days = 'days='+data['days'].ljust(8)
      name= 'name='+data['name'].replace(' ','-')
      client = pe+'  '+interface+'  '+vlan+'  '+daybandwidth+'  '+nightbandwidth+'  '+starttime+'  '+endtime+'  '+days+'  '+name
      return client



def burst_actions(parent,serverlogin,server,clientfile,keypath,action,data,port=22):

   d = kazi(server,serverlogin,clientfile,keypath,parent=parent,port=port)

   if action.lower() == 'add' : d.add(parent,data)
   elif action.lower() == 'remove': d.remove(parent,data)
   elif action.lower() == 'update': d.update(parent,data)
   elif action.lower() == 'view': d.view(parent)

