# This code accepts host ip and interface name for input and finds unused vlans from the interface (as sub-intefaces)
# The affected host is accessed via ssh using paramiko lib
# AUTHOR: Paul S.I. Basondole Python 3.7

import os
import re
import sys
import time
import socket
import getpass
import paramiko
import datetime

__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"


def ciscoPort(interface):
   ''' remove the interface name and get only slot/port numbers in cisco
   For example: "Gi0/0/1" ---> "0/0/1"
   '''
   port = ''
   for x in range(len(re.findall(r'[0-9]',interface))):
      port += re.findall(r'[0-9]',interface)[x]
      if x == len(re.findall(r'[0-9]',interface))-1: continue
      else: port += '/'
   return port


def LoginGetTerse(loopbackIp,ipDict,interface,username,password, context_output):

 
  sshClient = paramiko.SSHClient()
  sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

  try:
     sshClient.connect(loopbackIp, username=username, password=password, timeout=10,allow_agent=False,look_for_keys=False)
     authenticated = True
  except Exception as e:
     authenticated = False
     context_output['error']+='\n '+(time.ctime()+" (user = "+username+") failed authentication > "+loopbackIp)


  if authenticated==True:

     console_output = ''
     cli = sshClient.invoke_shell()

     if ipDict[loopbackIp]['software'] == 'junos':
        cli.send('set cli screen-length 0\n')
        cli.send('set cli screen-width 0\n')
        time.sleep(1)
        cli.recv(65536)
        cli.send("show interface terse | match ^"+interface+"\n")

     if ipDict[loopbackIp]['software'] == 'ios':
        cli.send('terminal length 0\n')
        cli.send('terminal width 0\n')
        time.sleep(1)
        cli.recv(65536)
        cli.send('show ip interface brief | include .*%s\.\n'%ciscoPort(interface))

     time.sleep(5)
     cli.close()
     while True:
        cli_output = cli.recv(65536).decode("utf-8")
        if not cli_output:
          break
        for line in cli_output:
          console_output+=(line)

     sshClient.close()

     return console_output


def getUsedVlan(host,ipDict,interface,console_output):

   if not console_output:
      return []

   try:
      output_lines = console_output.split('\n')
   except Exception:
      return [vlan for vlan in range(1,4095)] # if interface info cant begotten assume all have been used

   usedVlans = []

   if ipDict[host]['software'] == 'junos': regex = re.escape(interface) + r'\.(\S+)'
   if ipDict[host]['software'] == 'ios': regex = re.escape(ciscoPort(interface)) + r'\.(\S+)'


   for line in output_lines:
      if line.strip(): 
         vlantag = re.findall(regex,line.split()[0]) # returns list
         if vlantag: usedVlans.append(vlantag[0].strip())

   return usedVlans




def findAllFreeVlan(host,interface,usedVlans, context_output):

   freeVlans = []

   if len(usedVlans)==0:
      freeVlans = [vlan for vlan in range(1,4095)]
      try:
         context_output['out']+='\n ['+ (host+': '+interface+']')
         context_output['out']+='\n '+ ("is not tagged... all vlan tags are available if tagging is required\n")
      except Exception:
        pass # if the function is not run as main it wont have the context_output['out'] variable

      return freeVlans


   if int(usedVlans[0])>1:
      for freeVlanPrefix in range(1,int(usedVlans[0])):
         freeVlans.append(freeVlanPrefix)

   for x in range(len(usedVlans)):
      if int(usedVlans[x])-int(usedVlans[x-1]) > 1:
         diff = int(usedVlans[x])-int(usedVlans[x-1])
         counter = 0
         while diff != 1:
            diff -=1
            counter +=1
            if int(usedVlans[x-1])+counter <= 4094:
               freeVlans.append(int(usedVlans[x-1])+counter)

   if int(usedVlans[-1]) <= 4094:
      for freeVlanSufix in range(int(usedVlans[-1])+1,4095): #counting from zero 4094 is the 4095th number
         freeVlans.append(freeVlanSufix)

   else:
      if len(freeVlans) == 0:
         try:
            context_output['out']+='\n ['+ (host+': '+interface+']')
            context_output['out']+='\n '+ ('all vlan tags are used... no free Vlan tag available')
         except NameError: pass


   return freeVlans # list





def groupVlans(freeVlans):
   tempdic={}
   for vlan in freeVlans:
      if vlan-1 in tempdic:
         tempdic[vlan-1]= vlan
      elif vlan-1 in tempdic.values():
         for key in tempdic.keys():
            if vlan-1==tempdic[key]:
               foundkey = key
         tempdic[foundkey]=vlan
      else:
         tempdic[vlan]=0
   keylist = sorted(tempdic)
   noRangeVlan = []
   rangeVlan = []
   for key in keylist:
      if tempdic[key] > 0:
         if tempdic[key] > 4094: tempdic[key] = 4094
         rangeVlan.append("["+(str(key)).rjust(4)+"-"+(str(tempdic[key])).ljust(4)+"]")
      else:
         noRangeVlan.append((str(key)).ljust(4))

   formatedRangeVlan = ""
   column = 0
   for vRange in rangeVlan:
      formatedRangeVlan +=(" "+vRange)
      column +=1
      if column%6==0:
         formatedRangeVlan +=("\n")

   column = 0
   formatedNoRangeVlan = ""
   for noVRange in noRangeVlan:
      formatedNoRangeVlan +=(" "+noVRange)
      column +=1
      if column%14==0:
         formatedNoRangeVlan +=("\n")

   return formatedRangeVlan, formatedNoRangeVlan # string


def vlanFinder(host,ipDict,interface,username,password, context_output):

   console_output = LoginGetTerse(host,ipDict,interface,username,password,context_output)

   if type(console_output) == str:
   
      usedVlans = getUsedVlan(host,ipDict,interface,console_output)

      if usedVlans:
         freeVlans = findAllFreeVlan(host,interface,usedVlans,context_output)

      else: freeVlans = [x for x in range(1,4095)]

   else:
      freeVlans = ['ConnectError']


   return freeVlans #list



def display_all_vlans(host,interface,freeVlans,context_output):

   if len(freeVlans) == 4094:
      context_output['out']+='\n ['+ (host+': '+interface+']')
      context_output['out']+='\n '+ ("is not tagged... all Vlans are available if tagging is required\n")

   if 'ConnectError' not in freeVlans:
      formatedRangeVlan, formatedNoRangeVlan = groupVlans(freeVlans)
   else: formatedRangeVlan, formatedNoRangeVlan = None, None

   if context_output['out']: summary_output = context_output['out'] # this info will be added in the end of output
   if context_output['errors']: errors = [error.strip() for error in context_output['errors'].split('\n') if error.strip()]

   context_output['out'] ='\n'+ ("Tags information:")
   context_output['out']+='\n'+ ("-----------------")
   context_output['out']+='\n'
   if formatedNoRangeVlan:
      context_output['out']+='\n'+ (" Lones:")
      context_output['out']+='\n'+ (" ------")
      context_output['out']+='\n'+ (formatedNoRangeVlan)
      context_output['out']+='\n'+'\n'
   if formatedRangeVlan:
      context_output['out']+='\n'+ (" Packs:")
      context_output['out']+='\n'+ (" ------")
      context_output['out']+='\n'+ (formatedRangeVlan)
      context_output['out']+='\n'

   total = len(freeVlans)
   if total > 4094:  total = 4094

   context_output['out']+='\n'
   context_output['out']+='\n Summary:\n --------'
   context_output['out']+= f'\n Total number of available VLAN tags on [{interface}] is {str(total)}'
   try: context_output['out']+='\n'+ summary_output +'\n'
   except: context_output['out']+='\n\n' # if summary output not there
   context_output['out']+='\n <span class="token function">Errors:\n -------'
   if not context_output['errors']: context_output['out']+= '\n </span>[0] error(s)\n'
   else:
      context_output['out']+= '\n [{}] error(s)'.format(len(errors))
      context_output['out']+=context_output['errors'] +'</span>\n'



def display_range_of_vlans(host,interface,freeVlans,startNumber,endNumber,context_output):

   if len(freeVlans) == 4094:
      context_output['out']+='\n ['+ (host+': '+interface+']')
      context_output['out']+='\n '+ ("is not tagged... all Vlans are available if tagging is required\n")

   vlanCount = [vlan for vlan in freeVlans if vlan in range(startNumber,endNumber+1)]

   if 'ConnectError' not in freeVlans:
       formatedRangeVlan, formatedNoRangeVlan = groupVlans(vlanCount)
   else: formatedRangeVlan, formatedNoRangeVlan = None, None

   if context_output['out']: summary_output = context_output['out'] # this info will be added in the end of output
   if context_output['errors']: errors = [error.strip() for error in context_output['errors'].split('\n') if error.strip()]

   context_output['out'] ='\n'+ ("Tags information:")
   context_output['out']+='\n'+ ("-----------------")
   context_output['out']+='\n'
   if formatedNoRangeVlan:
      context_output['out']+='\n'+ (" Lones:")
      context_output['out']+='\n'+ (" ------")
      context_output['out']+='\n'+ (formatedNoRangeVlan)
      context_output['out']+='\n'+'\n'
   if formatedRangeVlan:
      context_output['out']+='\n'+ (" Packs:")
      context_output['out']+='\n'+ (" ------")
      context_output['out']+='\n'+ (formatedRangeVlan)
      context_output['out']+='\n'

   context_output['out']+='\n'
   context_output['out']+='\n Summary:\n --------'
   context_output['out']+=f'\n Total number of available VLAN tags on [{interface}] is {str(len(vlanCount))}'
   try: context_output['out']+='\n'+ summary_output +'\n'
   except: context_output['out']+='\n\n' # if summary output not there
   context_output['out']+='\n <span class="token function">Errors:\n -------'
   if not context_output['errors']: context_output['out']+= '\n </span>[0] error(s)\n'
   else:
      context_output['out']+= '\n [{}] error(s)'.format(len(errors))
      context_output['out']+=context_output['errors'] +'</span>\n'




def singleVlanFinder(username,password,host,ipDict,interface,context_output,search=None,start=None,end=None):

   context_output['out'] = ''
   context_output['errors'] = ''

   freeVlans = vlanFinder(host,ipDict,interface,username,password,context_output)

   if not search:
      return freeVlans #list

   if freeVlans :
      if search == 'list_range' and start and end:
         display_range_of_vlans(host,interface,freeVlans,int(start),int(end),context_output)
      else:
         display_all_vlans(host,interface,freeVlans,context_output)

   return context_output['out']


         

def find_vlan_uno(username,password,host,ipDict,interface,context_output, search=None,start=None,end=None):
  
    start_time = time.time()

    result = singleVlanFinder(username,password,host,ipDict,interface,context_output,search=search,start=start,end=end)

    if not search:
      return result # list

    run_time = round(time.time()-start_time)

    result = str(result) + '\n'+ '[Finished in %s seconds]'%str(run_time)

    return result