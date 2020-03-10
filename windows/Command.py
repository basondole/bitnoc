# This module is part of the core Basondole Tools
# This code provides GUI for user to issue commands to hosts
# The commands will be sent to the hosts via SSH and the output will be returned on a window
# Commands and hosts can be input directly in the input window or can be loaded from a file
# Does not play well with commands that result to infinite lines of output such us continous ping

import re
import time
import paramiko
import socket
import threading
import ipaddress


__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"



class Command():

    def __init__(self, ipDict, username, password,commandList,deviceList, context_output):

         self.context_output = context_output
         self.context_output['out'] = ''
         self.context_output['errors'] = ''

         self.commandList = commandList
         self.deviceList = deviceList
         self.username = username
         self.password = password



    def execute(self):
         start_time = time.time()
         result = Command.fanya(self)
         run_time = round(time.time()-start_time)
         result = result + '\n'+ '[Finished in %s seconds]'%str(run_time)
         return result



    @staticmethod
    def fanya(self):

           self.context_output['_op_out_'] = ''

           threads = []
           lock = threading.Lock()

           self.deviceList.sort()

           for ip in self.deviceList:
               try:  ipaddress.ip_address(ip)
               except Exception as e: 
                  self.context_output['errors'] +=  '\n'+(time.ctime())+' '+str(e)
                  self.deviceList.remove(ip)  

           if not self.deviceList:
              return


           for ip in self.deviceList:

              ip = ip.strip()
              if not ip: continue


              t = threading.Thread(target=Command.kazi, args=(self,ip,lock))
              t.start()
              threads.append(t)


           for t in threads: t.join()

           self.devices, self.commands = [],[]


           if self.context_output['errors']: 
            errors = [ error.strip() for error in self.context_output['errors'].split('\n') if error.strip()]
           else: 
            errors =[]
           if self.context_output['out']:  summary_output  = self.context_output['out']
           self.context_output['out']+='\n'

           if not self.context_output['_op_out_']: 
               self.context_output['out']+='\n'
               self.context_output['out']+='\nSummary:'
               self.context_output['out']+='\n--------\n'
               self.context_output['out']+=' [0] command exected on [{}/{}] accessed device(s)'.format(
                               len(self.deviceList)-len(errors),len(self.deviceList))
               self.context_output['out']+='\n'

    
           if self.context_output['_op_out_']:
               self.context_output['out'] ='\n'+ self.context_output['_op_out_']
               self.context_output['out']+='\n'
               self.context_output['out']+='\n'
               self.context_output['out']+='\n Summary:'
               self.context_output['out']+='\n --------\n'
               self.context_output['out']+=' [{}] command(s) executed on [{}/{}] accessed device(s)'.format(
                               len(self.commandList ),len(self.deviceList)-len(errors),len(self.deviceList))
               self.context_output['out']+='\n'

           try: self.context_output['out']+='\n'+ summary_output +'\n'
           except: self.context_output['out']+='\n\n' # if summary output not there
           self.context_output['out']+='\n <span class="token function">Errors:'
           self.context_output['out']+='\n -------'
           if not self.context_output['errors']: self.context_output['out']+= '\n </span>[0] error(s)\n'
           else:
             self.context_output['out']+= '\n [{}] error(s)'.format(len(errors))
             self.context_output['out']+= '\n'+ self.context_output['errors'] +'</span>\n'


           return self.context_output['out']



    @staticmethod
    def kazi(self,ipaddress,lock):

       sshClient = paramiko.SSHClient()
       sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

       try:
          sshClient.connect(ipaddress, username=self.username, password=self.password, timeout=10,allow_agent=False,look_for_keys=False)
          authenticated = True

       except Exception:
          authenticated = False
          with lock:
            self.context_output['errors']+= '\n '+(time.ctime()+" (user = "+self.username+") failed authentication > "+ipaddress.ljust(15))

       if authenticated==True:
          console_output = ''
          secureCli = sshClient.invoke_shell()
          secureCli.send('set cli screen-length 0\n')
          secureCli.send('set cli screen-width 0\n')
          secureCli.send('terminal length 0\n')
          secureCli.send('terminal width 0\n')

          time.sleep(1)
          pre_output = secureCli.recv(65535).decode("utf-8")
          cliprompt = pre_output.split('\n')[-1].strip()
          del pre_output

          for line in self.commandList:
             line = line.strip()
             if not line: continue
             secureCli.send(line)
             secureCli.send('\n')
             time.sleep(1)
          
          try:
             secureCli.close()
          except socket.error: pass # session already Closed
          time.sleep(5)
          while True:
             cli_output = secureCli.recv(65535).decode("utf-8")
             if not cli_output: break
             for line in cli_output:  console_output+=str(line)
          
          sshClient.close()

          output_lines = console_output.split('\n')
          output_lines[0] = cliprompt+str(output_lines[0])
          if cliprompt == output_lines[-1].strip():
             output_lines.pop(-1)

          for index,line in enumerate(output_lines):
             line = line.rstrip()
             output_lines[index] = line

             if re.search(r'^'+cliprompt,line):
                line = line.split(cliprompt)
                line = ' '.join(line)

                head = '\n'
                head += line.strip() +'\n'+ ''.join(['-' for x in range(len(line.strip()))])
                output_lines[index] = head


          output_lines = '\n'.join(output_lines)
          output_lines = output_lines.split('\n')


          if self.context_output['_op_out_']: self.context_output['_op_out_'] += '\n'+'\n'

          with lock:
                 self.context_output['_op_out_'] += '\n'+ ('['+ipaddress+']')
                 for line in output_lines:
                    self.context_output['_op_out_'] += '\n' + '   '+line





def devices_to_list(ip_dict,option):
   ''' Creates list of devices from a given dictionary and vendor option
   '''
   ipList = list(ip_dict.keys())
   ipList.sort()

   ios_devices = []
   junos_devices = []


   for ip in ipList:
      try:
         if 'junos' in ip_dict[ip]['software']:
            junos_devices.append(ip)
         elif 'ios' in ip_dict[ip]['software']:
            ios_devices.append(ip)
      except Exception: pass

   if option == 'junos':
    return junos_devices
   elif option == 'ios':
   	return ios_devices