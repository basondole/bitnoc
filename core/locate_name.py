# This code accepts a string input of description and searches the hosts to find matching interface description
# The affected hosts are defined in the Basondole Tools device menu and are accessed via ssh using paramiko lib
# AUTHOR: Paul S.I. Basondole Python 3.7

import re
import time
import socket
import paramiko
import threading


__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"



class TafutaJina:

   @staticmethod
   def LoginGetDescription(loopbackIp,ipDict,name,username,password,lock,context_output):


      sshClient = paramiko.SSHClient()
      sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

      try:
         sshClient.connect(loopbackIp, username=username, password=password, timeout=10,allow_agent=False,look_for_keys=False)
         authenticated = True
      except (socket.error, paramiko.AuthenticationException):
         authenticated = False
         with lock:
            context_output['error']+='\n '+ (time.ctime()+" (user = "+username+") failed authentication > "+loopbackIp)
      
      if authenticated==True:

         console_output = ''
         cli = sshClient.invoke_shell()
         time.sleep(1)

         if ipDict[loopbackIp]['software'] == 'junos':
            cli.send('set cli screen-length 0\n')
            cli.send('set cli screen-width 0\n')
            time.sleep(2)
            cli.recv(65536)
            cli.send('\n') # invoke the prompt
            cli.send('show interfaces description | match '+'"'+name+'"\n')

         elif ipDict[loopbackIp]['software'] == 'ios':
            cli.send("terminal length 0\n")
            cli.send('terminal width 0\n')
            time.sleep(2)
            cli.recv(65536)
            cli.send('\n') # invoke the prompt
            cli.send('show interfaces description | include ' +name.capitalize()+'|'+name.upper()+'|'+name.lower()+'|'+name+"\n")

         time.sleep(5)
         cli.close()
         while True:
            cli_output = cli.recv(65536).decode("utf-8")
            if not cli_output:
               break
            for line in cli_output:
               console_output+= str(line)
         sshClient.close()
         return console_output


   @staticmethod
   def getIfName(loopbackIp,ipDict,name,username,password,lock,context_output):

      desc = TafutaJina.LoginGetDescription(loopbackIp,ipDict,name,username,password,lock,context_output)
      if not desc:
         return


      lines = [line for line in desc.split("\n") if line]
      lines.pop(-1) # remove the last line which is the router prompt
      for line in lines:
         # since there is a prompt the show keyword
         # is not supposed to be the first in line
         if 'show interfaces description' in line and not re.search(r'^show',line):
            index = lines.index(line)
            break

      # if the show interfaces description call is not found return
      try:
         index
      except:
         return
      
      for line in lines[index+1:]:
         # if line start with a word character
         # to avoid lines with preceeding white space
         if re.search(r'^\S',line):
            with lock:
               context_output['description']+=((ipDict[loopbackIp])['hostname']+'.'+(loopbackIp.split('.'))[-1]).ljust(20)
               # interface name admin status operation state
               context_output['description']+=line.split()[0].rjust(13)+line.split()[1].rjust(7)+line.split()[2].rjust(8)
               # interface description from the 4th item to last
               context_output['description']+='   '+' '.join(line.split()[3:])
               context_output['description']+=("\n")


   @staticmethod
   def nameCheck(username,password,ipDict,name,context_output):

      context_output['description'] = ''
      context_output['out'] = ''
      context_output['error'] = ''

      ipList = list(ipDict.keys()) # useful in indentifying the last ip to run operation on

      threads = []
      lock = threading.Lock()

      for loopbackIp in ipDict:

         t = threading.Thread(target=TafutaJina.getIfName,
                              args=(loopbackIp,ipDict,name,username, password,lock,context_output))
         t.start()
         threads.append(t)

      for t in threads:
         t.join()

      if context_output['error']:
         errors = [ error.strip() for error in context_output['error'].split('\n') if error.strip()]
      else:
         errors = []
      if context_output['out']:
         summary_output = context_output['out'] # this info will be added in the end of output


      if context_output['description']:
         context_output['out']+=' DEVICE'.ljust(20)+' INTERFACE'.ljust(16)+' ADMIN'.ljust(7)+' STATUS'.ljust(9)+' DESCRIPTION\n'
         context_output['out']+=' ------'.ljust(21)+'-------------'.ljust(16)+'-----'.ljust(7)+'------'.ljust(9)+'-----------\n'

         lines = [line for line in context_output['description'].split('\n') if line]
         lines.sort()
         for line in lines:
            context_output['out']+='\n '+ line
         context_output['out']+='\n'
         context_output['out']+='\n'
         context_output['out']+='\n Summary:'
         context_output['out']+='\n --------\n'
         context_output['out']+=' [{}] match(es) for [{}] in active configuration of [{}/{}] checked device(s)'.format(
                            len(lines),name,len(ipDict)-len(errors),len(ipDict))
         context_output['out']+='\n'

      else:
         context_output['out']+='\n Summary:'
         context_output['out']+='\n --------\n'
         context_output['out']+=' [0] match for [{}] in active configuration of [{}/{}] checked device(s)'.format(
                                        name,len(ipDict)-len(errors),len(ipDict))


      try:
         context_output['out']+='\n'+ summary_output +'\n'
      except:
         context_output['out']+='\n\n' # if summary output not there

      context_output['out']+='\n <span class="token function">Errors:\n -------'
      if not context_output['error']:
         context_output['out']+= '\n [0] error(s)</span>\n'
      else:
         context_output['out']+= '\n [{}] error(s)'.format(len(errors))
         context_output['out']+= '\n'
         context_output['out']+= context_output['error'] +'</span>\n'

      result = context_output['out']

      return result



def locate_name(username,password,ipDict,name,context_output):

      start_time = time.time()
      
      result = TafutaJina.nameCheck(username,password,ipDict,name,context_output)

      run_time = round(time.time()-start_time)

      result = result + '\n'+ '[Finished in %s seconds]'%str(run_time)

      return result
