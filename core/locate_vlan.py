# This code accepts an interger input of vlan-id and searches the hosts to find matching interfaces
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


class Getters:

  @staticmethod
  def sshGetData(loopbackIp,ipDict,vlan,username,password,lock, context_output):

    sshClient = paramiko.SSHClient()
    sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
       sshClient.connect(loopbackIp, username=username, password=password, timeout=10,allow_agent=False,look_for_keys=False)
       authenticated = True
    except (socket.error, paramiko.AuthenticationException):
       authenticated = False
       with lock:
        context_output['errors']+='\n '+ (time.ctime()+" (user = "+username+") failed authentication > "+loopbackIp)
       return '',''


    if authenticated==True:
       description_output = ''
       cli = sshClient.invoke_shell()
       time.sleep(1)

       if ipDict[loopbackIp]['software'] == 'junos':
          cli.send('set cli screen-length 0\n')
          cli.send('set cli screen-width 0\n')
          time.sleep(2)
          cli.recv(65536)
          cli.send('\n') # invoke the prompt
          cli.send('show interfaces description | match "\.%s "\n'%str(vlan))

       elif ipDict[loopbackIp]['software'] == 'ios':
          cli.send('terminal length 0\n')
          cli.send('terminal width 0\n')
          time.sleep(2)
          cli.recv(65536)
          cli.send('\n') # invoke the prompt
          cli.send('show interfaces description | include \.%s +\n'%str(vlan))

       time.sleep(5)
       cli.close()
       while True:
          cli_output = cli.recv(65536).decode("utf-8")
          if not cli_output:
            break
          for line in cli_output:
            description_output+=str(line)


       terse_output = ''
       try:
        cli = sshClient.invoke_shell()
       except EOFError:
          sshClient.connect(loopbackIp, username=username, password=password, timeout=10,allow_agent=False,look_for_keys=False)
          cli = sshClient.invoke_shell()

       if ipDict[loopbackIp]['software'] == 'junos':
          cli.send('set cli screen-length 0\n')
          cli.send('set cli screen-width 0\n')
          time.sleep(2)
          cli.recv(65536)
          cli.send('\n') # invoke the prompt
          cli.send('show interface terse | match "\.%s "\n'%str(vlan))

       elif ipDict[loopbackIp]['software'] == 'ios':
          cli.send('terminal length 0\n')
          cli.send('terminal width 0\n')
          time.sleep(2)
          cli.recv(65536)
          cli.send('\n') # invoke the prompt
          cli.send('show ip interface brief | include \.%s +\n'%str(vlan))

       time.sleep(5)
       cli.close()
       while True:
          cli_output = cli.recv(65536).decode("utf-8")
          if not cli_output:
            break
          for line in cli_output:
            terse_output+=str(line)

       sshClient.close()

       return description_output, terse_output



  @staticmethod
  def getUsedVlan(terse):

     lines = [line for line in terse.split("\n") if line]
     lines.pop(-1) # pop the last empty line containing the host name prompt

     usedVlans = []

     for line in lines:
        if ('show interface' in line or 'show ip interface' in line) and not re.search(r'^show',line):
           index = lines.index(line)
           break

     # if the show command is not found in the output return
     try: index
     except: return usedVlans

     for line in lines[index+1:]:
        if re.search(r'^\S',line): usedVlans.append(line) #match word character except white space

     return  usedVlans #list


  @staticmethod
  def getIfName(loopbackIp,ipDict,vlan_list,desc, context_output):

     desc = [line for line in desc.split("\n") if re.search(r'^\S',line)]
     desc.pop(-1) # pop the last empty line containing the host name prompt

     for line in desc:
        if 'show interfaces description' in line and not re.search(r'^show',line):
           index = desc.index(line)
           break

     if not desc: #if there is no description match return the interface terse output
        for vlan in vlan_list:
           if not re.search(r'^[ud]',vlan.split()[1]):
             continue #if the admin status doesnot start with u or d for up or down skip the line
           # hostname plus last octate of ip
           context_output['_match_']+=((ipDict[loopbackIp])['hostname']+'.'+(loopbackIp.split('.'))[-1]).ljust(20)
           # interface name admin status and operation state
           context_output['_match_']+=vlan.split()[0].rjust(13)+vlan.split()[1].rjust(7)+vlan.split()[2].rjust(8)
           context_output['_match_']+=("\n")

        return

     # if the show command is not found in the output return
     try:
        index
     except NameError:
        for vlan in vlan_list:
           if not re.search(r'^[ud]',vlan.split()[1]):
             continue #if the admin status doesnot start with u or d for up or down skip the line
           # hostname plus last octate of ip
           context_output['_match_']+=((ipDict[loopbackIp])['hostname']+'.'+(loopbackIp.split('.'))[-1]).ljust(20)
           # interface name admin status and operation state
           context_output['_match_']+=vlan.split()[0].rjust(13)+vlan.split()[1].rjust(7)+vlan.split()[2].rjust(8)
           context_output['_match_']+=("\n")
        return

     for vlan in vlan_list:
        if not re.search(r'^[ud]',vlan.split()[1]) and ipDict[loopbackIp]['software'] == 'junos':
          continue #if the admin status doesnot start with u or d for up or down skip the line
        for name in desc[index+1:]:
           # if the logical interface in terse matches the logical interface in desciption
           if vlan.split()[0] == name.split()[0] or ipDict[loopbackIp]['software'] == 'ios':
              # hostname plus last octate of ip
              context_output['_match_']+=((ipDict[loopbackIp])['hostname']+'.'+(loopbackIp.split('.'))[-1]).ljust(20)
              # interface name admin status and operation state
              context_output['_match_']+=name.split()[0].rjust(13)+name.split()[1].rjust(7)+name.split()[2].rjust(8)
              # actual description from the 4th item to last
              description = name.split()[3:]
              context_output['_match_']+='   '+' '.join(description)
              context_output['_match_']+=("\n")
           else:
              # hostname plus last octate of ip
              context_output['_match_']+=((ipDict[loopbackIp])['hostname']+'.'+(loopbackIp.split('.'))[-1]).ljust(20)
              # interface name admin status and operation state
              context_output['_match_']+=vlan.split()[0].rjust(13)+vlan.split()[1].rjust(7)+vlan.split()[2].rjust(8)
              context_output['_match_']+=("\n")


class Onesha:


  @staticmethod
  def kazi(loopbackIp,ipDict,vlan,username, password,lock, context_output):
      desc_match, vlan_match = Getters.sshGetData(loopbackIp,ipDict,vlan,username,
                                                  password,lock, context_output)
      if vlan_match:
         vlan_list = Getters.getUsedVlan(vlan_match)
         if vlan_list:
           Getters.getIfName(loopbackIp,ipDict,vlan_list,desc_match, context_output)
           context_output['_vlans_']+= str(loopbackIp).ljust(15)
           context_output['_vlans_']+= (": has a match for VLAN ")
           context_output['_vlans_']+= str(vlan)
           context_output['_vlans_']+= ("\n")



  @staticmethod
  def checkVlan(username,password,ipDict,vlan,context_output):

     context_output['out'] = ''
     context_output['errors'] = ''
     context_output['_match_'] = ''
     context_output['_vlans_'] = ''

     threads = []
     lock = threading.Lock()

     for loopbackIp in ipDict.keys():
        if '--' in ipDict[loopbackIp]['hostname']: continue
        t = threading.Thread(target=Onesha.kazi, args=(loopbackIp,ipDict,vlan,username,password,lock,context_output))
        t.start()
        threads.append(t)

     for t in threads:
      t.join()

     if context_output['errors']:
      errors = [ error.strip() for error in context_output['errors'].split('\n') if error.strip()]
     else:
      errors = []

     if context_output['out']:
       summary_output = context_output['out'] # this info will be added in the end of output

     if context_output['_match_']:
       lines =[line for line in context_output['_match_'].split('\n') if line.strip()]
       lines.sort()
     else:
      lines = []


     if context_output['_vlans_']:
       context_output['out'] = " DEVICE".ljust(20)+" INTERFACE".ljust(16)+" ADMIN".ljust(7)+" STATUS".ljust(9)+" DESCRIPTION\n"
       context_output['out']+= " ------".ljust(21)+"-------------".ljust(16)+"-----".ljust(7)+"------".ljust(9)+"-----------\n"

     for line in lines:
      context_output['out']+= '\n '+line

     if lines:
      context_output['out']+='\n'
      context_output['out']+='\n'

     context_output['out']+='\n Summary:'
     context_output['out']+='\n --------\n'
     context_output['out']+= ' [{}] match(es) for vlan tag [{}] in active configuration of [{}/{}] checked device(s)'.format(
                               len(lines),vlan,len(ipDict)-len(errors),len(ipDict))

     try: context_output['out']+='\n'+ summary_output +'\n'
     except: context_output['out']+='\n\n' # if summary output not there

     context_output['out']+='\n <span class="token function">Errors:\n -------'
     if not context_output['errors']:
      context_output['out']+= '\n [0] error(s)</span>\n'
     else:
       context_output['out']+= '\n [{}] error(s)'.format(len(errors))
       context_output['out']+= '\n'
       context_output['out']+= context_output['errors'] +'</span>\n'

     return context_output['out']



def locate_vlan(username,password,ipDict,vlan,context_output):

    start_time = time.time()

    result = Onesha.checkVlan(username,password,ipDict,vlan,context_output)

    run_time = round(time.time()-start_time)

    result = result + '\n'+ '[Finished in %s seconds]'%str(run_time)

    return result
