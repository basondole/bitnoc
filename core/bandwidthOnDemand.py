
# This class provides client methods to interact with server for creating or deleting shell scripts on a server
# These scripts will be used to change bandwidth configuration on routers on the specified date and time
# Task schedulrer used is linux 'at'
# The code can be ran from client or the server itself


import re
import time
import socket
import paramiko
from windows.WindowDialog import Dialog
from other.Essential import resource_path


__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"

cancel_icon = resource_path(r'cancel-icon.png')


class Server():

   def __init__(self,serverlogin,server,scriptPath,scriptname,keypath,parent=None,port=22):
      self.server = server
      self.serverlogin = serverlogin
      self.scriptPath = scriptPath
      self.scriptname = scriptname
      self.keypath = keypath
      self.port = port
      if parent: self.parent = parent
      self.sshClient = paramiko.SSHClient()
      self.sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      self.up = True

      try: self.key = paramiko.RSAKey.from_private_key_file(self.keypath)
      except Exception as e:
         Dialog(self.parent,prompt='Error: '+str(e)+'\n',icon=cancel_icon)
         self.up = False
         return


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


   def revertJob(self,revertDate):
 
         command = "at "+revertDate+" -M -f "+self.scriptPath.rstrip('/')+"/PendingTickets/"+self.scriptname+\
                   " 2>&1 | sed 's/^/#/' |awk 'END {print}' >>"+self.scriptPath.rstrip('/')+"/PendingTickets/"+self.scriptname
         try:
            self.sshClient.connect(self.server, username = self.serverlogin, pkey = self.key, port=self.port)
            stdin , stdout, stderr = self.sshClient.exec_command(command)
            self.sshClient.close()
         except Exception as e: Dialog(self.parent,prompt='Can not access server \n'+self.server+' \n'+str(e),icon=cancel_icon)


   def revertScript(self,task):
         command = 'echo "'+task+'" > '+self.scriptPath.rstrip('/')+'/PendingTickets/'+self.scriptname
         try:
            self.sshClient.connect(self.server, username = self.serverlogin, pkey = self.key, port=self.port )
            stdin , stdout, stderr = self.sshClient.exec_command(command)
            self.sshClient.close()
         except Exception as e: Dialog(self.parent,prompt='Can not access server \n'+self.server+' \n'+str(e),icon=cancel_icon)


   def retrieveRemoteFile(self,stdict=None,bigdict=None,updatecursor=False):
      if updatecursor:
         self.parent.config(cursor="wait") #show a busy cursor on the main app window
         self.parent.update()

      if self.up:
         strfile = ''
         command = 'cat '+self.scriptPath.rstrip('/')+'/PendingTickets/'+self.scriptname

         try:
            self.sshClient.connect(self.server, username = self.serverlogin, pkey = self.key, port=self.port )
            stdin , stdout, stderr = self.sshClient.exec_command(command)
            tickets = stdout.read().decode("utf-8")
            self.sshClient.close()
         except Exception as e:
            Dialog(self.parent,prompt='Can not access server \n'+self.server+' \n'+str(e),icon=cancel_icon)
            return


         regex = r'ST(\S+by.*\.log)'

         if stdict: sdict= {}
         if bigdict: bdict = {}

         sn = 1
         for line in tickets.split('\n'):

            if re.findall(regex,line) and 'sendmail' not in line: # look for ST number from the output of all scripts in pending tickets folder
               script = re.findall(regex,line)[0] # will get something like "078547byfisi.log\n"
               script = 'ST'+script # to create something like "ST078547byfisi.log\n"
               strfile+='   '+str(sn).rjust(3)+'. ' # add output line unmber
               strfile+=script.split('.')[0]+'\n' # will get something like "1. ST078547byfisi"
               sn+=1
               if bigdict:
                  bdict[script.split('by')[0].lstrip('ST')] = {}
                  if re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',line):
                     # pe ip address
                     bdict[script.split('by')[0].lstrip('ST')]['host']=re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',line)[0]
                  if re.findall(r'interface.(\S+)',line):
                     # physical interface
                     bdict[script.split('by')[0].lstrip('ST')]['interface'] = re.findall(r'interface.(\S+)',line)[0].split(':')[0].split('.')[0]
                     # logical interface
                     bdict[script.split('by')[0].lstrip('ST')]['vlan'] = re.findall(r'interface.(\S+)',line)[0].split(':')[0].split('.')[1].strip()
                  if re.findall(r'input.(\S+)',line):
                     # policer
                     bdict[script.split('by')[0].lstrip('ST')]['cir'] = re.findall(r'input.(\S+)',line)[0].split(':')[0].strip()

            elif re.findall(r'job.(\d+)',line): # look for at job number from the output of all scripts in pending tickets folder
               try: script # variable script is created in prior if statement
               except NameError: # if script was not defined from above  the script is corrupt
                  script = 'Unknown Ticket'
                  strfile+='   '+str(sn).rjust(3)+'. '
                  strfile+=script.split('.')[0]+'\n'
                  if bigdict: bdict[script] = []
                  if stdict: sdict[script] = []
               strfile+= (' '.rjust(8)+str(line)+'\n\n') # add the line with at job number to the ST number begotten from above

               if stdict: sdict[script.split('.')[0]]= re.findall(r'job.(\d+)',line)[0]
               if bigdict:
                  date = line.split()[4],line.split()[5],line.split()[-1]
                  bdict[script.split('by')[0].lstrip('ST')]['job'] = re.findall(r'job.(\d+)',line)[0]
                  bdict[script.split('by')[0].lstrip('ST')]['date'] = date

         if stdict: return sdict
         elif bigdict: return bdict
         else: return strfile
      else: Dialog(self.parent,prompt='Can not access server \n'+self.server+' \n',icon=cancel_icon)



   def deleteFromRemoteFile(self,scriptname,jobid,updatecursor=False):
         if updatecursor:
            self.parent.config(cursor="wait") #show a busy cursor on the main app window
            self.parent.update()

         scriptname = 'ST'+(scriptname.lstrip('ST').split('by')[0]).zfill(6)+'*.sh'
         command = 'rm '+self.scriptPath+'/PendingTickets/'+scriptname+'\natrm '+jobid+'\n'

         try:
            self.sshClient.connect(self.server, username = self.serverlogin, pkey = self.key, port=self.port )
            stdin , stdout, stderr = self.sshClient.exec_command(command)
            self.sshClient.close()
         except Exception as e: Dialog(self.parent,prompt='Can not access server \n'+self.server+' \n'+str(e),icon=cancel_icon)


def createJob(parent,serverlogin,server,directory,keypath,data,mail=False,port=22):


   pe = data['pe']
   st = data['ticket']
   revertDate = data['date']
   commandList = data['commands']

   stnumber = 'ST'+st.zfill(6)+'by'+parent.username
   scriptname = stnumber+'.sh'
   scriptPath = directory

   error = cancel_icon

   commandStr = ':'.join(commandList)
   heading = 'Changing bandwidth for ST'+ st.zfill(6)

   task = "echo 'Subject:"+heading+"' > "+scriptPath.rstrip('/')+"/Logs/"+stnumber+".log"
   task+= " && date >> "+scriptPath.rstrip('/')+"/Logs/"+stnumber+".log"
   task+= " && cd "+scriptPath+" && "+scriptPath.rstrip('/')+"/willdo -commands \'"+commandStr+"\' -ipaddress "+pe+" >> "+scriptPath.rstrip('/')+"/Logs/"+stnumber+".log"
   task+= "\nrm "+scriptPath.rstrip('/')+"/PendingTickets/"+scriptname
   if mail: task+= "\nsendmail "+mail+" < "+scriptPath.rstrip('/')+"/Logs/"+stnumber+".log"


   status = Server(serverlogin,server,scriptPath,scriptname,keypath,parent=parent,port=port)

   if status.up:
      status.revertScript(task)
      time.sleep(2)
      status.revertJob(revertDate)
      time.sleep(1)
      return status.retrieveRemoteFile()
   else:
      Dialog(parent,prompt='Can not access server \n'+server+' \n',icon=cancel_icon)
      return False

