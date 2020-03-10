# This code accepts a string input of ipv4 subnet and searches the hosts to find matching subnets and hosts
# The affected hosts are defined in the Basondole Tools device menu and are accessed via ssh using paramiko lib


import re
import time
import ipaddress
import socket
import paramiko
import threading
from IPy import IP



__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"



class Parse:
   ''' Parses different output from different devices
   '''

   @staticmethod
   def convertToCidr(key):
      ''' For cisco ios converts a line given as key with address or address/subnetmask or address/wildcard
      to cidr notation
      '''

      # matching vrf routes
      if 'ip route vrf ' in key:
         keystriped = key.strip('ip route vrf ').split()
         vrf = keystriped[0]
         address = keystriped[1]
         mask = keystriped[2]
         #remove the extracted items from the list
         keystriped.remove(vrf)
         keystriped.remove(address)
         keystriped.remove(mask)
         address = ipaddress.ip_interface(address+'/'+mask)
         key = 'ip route vrf '+vrf+' '+str(address)+' '+' '.join(keystriped) #append the remainder of the keystriped
         return key

      # matching global routes
      elif 'ip route 'in key:
         keystriped= key.strip('ip route ').split()
         pref = keystriped[0]+'/'+keystriped[1]
         pref = ipaddress.ip_interface(pref)
         #remove the extracted items from the list
         keystriped.pop(0)
         keystriped.pop(0)
         key = 'ip route '+str(pref)+' '+' '.join(keystriped)
         return key

      # matching ip address on interface
      elif 'ip address ' in key:
         keystriped= key.strip('ip address ').split()
         pref = ipaddress.ip_interface(keystriped[0]+'/'+keystriped[1])
         #remove the extracted items from the list
         keystriped.remove(keystriped[0])
         keystriped.remove(keystriped[0])
         key = 'ip address '+str(pref)+' '+' '.join(keystriped)
         return key


      # matching access-lists and elements
      elif 'access-list ' in key or re.findall(r'permit|deny',key): # the or is for named ACL

         ip_addresses = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',key)

         if len(ip_addresses)==4: # extended access list with source and destination
            source = []
            for octate in range(4):
               source.append(str(int(ip_addresses[0].split('.')[octate])+int(ip_addresses[1].split('.')[octate])))

            source_ip = IP(ip_addresses[0]+'-'+('.'.join(source)))
            destination = []
            for octate in range(4):
               destination.append(str(int(ip_addresses[2].split('.')[octate])+int(ip_addresses[3].split('.')[octate])))

            destination_ip = IP(ip_addresses[2]+'-'+('.'.join(destination)))

            key = key.split()
            source_index = key.index(ip_addresses[0])
            key.insert(source_index,str(source_ip))
            key.remove(ip_addresses[0])
            key.remove(ip_addresses[1])

            destination_index = key.index(ip_addresses[2])
            key.insert(destination_index,str(destination_ip))
            key.remove(ip_addresses[2])
            key.remove(ip_addresses[3])

            key = ' '.join(key)

         elif len(ip_addresses)==3: # extended access list with source and destination (one being specific host)
            source = []
            for octate in range(4):
               source.append(str(int(ip_addresses[0].split('.')[octate])+int(ip_addresses[1].split('.')[octate])))
            
            try: 
               source_ip = IP(ip_addresses[0]+'-'+('.'.join(source)))
               ipaddress.ip_network(source_ip) # test if it a valid ip network
               destination_ip = ip_addresses[2]+'/32'

               key = key.split()
               source_index = key.index(ip_addresses[0])
               key.insert(source_index,str(source_ip))
               key.remove(ip_addresses[0])
               key.remove(ip_addresses[1])
               destination_index = key.index(ip_addresses[2])
               key.insert(destination_index,str(destination_ip))
               key.remove(ip_addresses[2])
               key = ' '.join(key)

            except Exception:
               source_ip = ip_addresses[0]+'/32'
               destination = []
               for octate in range(4):
                  destination.append(str(int(ip_addresses[1].split('.')[octate])+int(ip_addresses[2].split('.')[octate])))
               destination_ip = IP(ip_addresses[1]+'-'+('.'.join(destination)))
               key = key.split()
               source_index = key.index(ip_addresses[0])
               key.insert(source_index,str(source_ip))
               key.remove(ip_addresses[0])
               destination_index = key.index(ip_addresses[1])
               key.insert(destination_index,str(destination_ip))
               key.remove(ip_addresses[1])
               key.remove(ip_addresses[2])
               key = ' '.join(key)


         elif len(ip_addresses)==2 and 'any' in key: #if source or destination is any
            address = []
            for octate in range(4):
               address.append(str(int(ip_addresses[0].split('.')[octate])+int(ip_addresses[1].split('.')[octate])))
            
            address_ip = IP(ip_addresses[0]+'-'+('.'.join(address)))

            key = key.split()
            address_index = key.index(ip_addresses[0])
            key.insert(address_index,str(address_ip))
            key.remove(ip_addresses[0])
            key.remove(ip_addresses[1])
            key = ' '.join(key)

         elif 'host' in key and 'any' in key: #if source or destination is any and the other is host
            address_ip = ip_addresses[0]+'/32'
            key = key.split()
            address_index = key.index(ip_addresses[0])
            key.insert(address_index,str(address_ip))
            key.remove(ip_addresses[0])
            key = ' '.join(key)

         elif len(re.findall(r'host',key))==2 : #if source and destination are both host
            source_ip = ip_addresses[0]+'/32'
            destination_ip = ip_addresses[1]+'/32'
            key = key.split()
            source_index = key.index(ip_addresses[0])
            key.insert(source_index,str(source_ip))
            key.remove(ip_addresses[0])
            destination_index = key.index(ip_addresses[1])
            key.insert(destination_index,str(destination_ip))
            key.remove(ip_addresses[1])
            key = ' '.join(key)


         else: #standard ACL

            keystriped = key.split()
            end = []
            ip = keystriped[-2]
            wildcard = keystriped[-1]
            if re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',ip):
               if re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',wildcard):
                  for octate in range(4):
                     end.append(str(int(ip.split('.')[octate])+int(wildcard.split('.')[octate])))
                  pref = IP(ip+'-'+('.'.join(end)))
                  keystriped.remove(keystriped[-1])
                  keystriped.remove(keystriped[-1])
                  key = ' '.join(keystriped)+' '+str(pref)
            else:
               key = key.strip()+'/32'

         return key

      # match any other address available
      else: 
         if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',key):
            ip_addresses = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',key)
            address_ip = ip_addresses[0]+'/32'
            key = key.split()
            address_index = key.index(ip_addresses[0])
            key.insert(address_index,str(address_ip))
            key.remove(ip_addresses[0])
            key = ' '.join(key)
            return key




   @staticmethod
   def parseCiscoOutput(loopbackIp,ipDict,output,subnet):

      sections = {}
      regex = r'^(interface|ip route|ip prefix-list|access-list|ip access-list)'
      for line in output.split('\n'):
         if re.findall(regex,line):
            sections[line.strip()] = []
            key = line.strip()
            continue

         try: 
            if not re.search(r'^\S',line): # match lines starting with non word character as lines within a section start with space
               if line: sections[key].append(line.strip()) 
         except UnboundLocalError:
            pass #the key is undefined, the regex wasnt matched
         except KeyError:
            pass #key is not in the dictionary

      subnet = ipaddress.ip_network(subnet, strict = False)
      ipregex = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}'


      for key in sections.keys():

         if re.search(r'^ip route',key):
            # ip route section
            key = Parse.convertToCidr(key) #convert doted decimal to cidr

            try:
               prefix = re.findall(ipregex,key)[0] # get the subnet/mask from the ip route entry

               if ipaddress.ip_network(prefix, strict = False).subnet_of(subnet): # check if it matches the search subnet
                  context_output['matching_subnets'] +=((ipDict[loopbackIp])['hostname']+'.'+(loopbackIp.split('.'))[-1]).ljust(20)
                  context_output['matching_subnets'] +=": "+key.strip()+"\n"

            except (IndexError,TypeError): pass # no ip address found

         elif 'ip prefix-list' in key:
            # ip prefix-list section
            try:
               prefix = re.findall(ipregex,key)[0] # get the subnet/mask from the ip route entry

               if ipaddress.ip_network(prefix, strict = False).subnet_of(subnet):
                  context_output['matching_subnets'] +=((ipDict[loopbackIp])['hostname']+'.'+(loopbackIp.split('.'))[-1]).ljust(20)
                  context_output['matching_subnets'] +=": "+key.strip()+"\n"
            except (IndexError,TypeError):  pass # no ip address found
    

         elif 'access-list' in key:
            # access-lis section
            if sections[key]: # mainly for named ACL
               for value in sections[key]:
                  # below two lines are just extra checks and may be skipped to one liner as line = convertToCidr(value)
                  # line 195 aleady takes care of this but I'll keep these two lines just in case
                  if value: line = Parse.convertToCidr(value) # check if the value of the key is not empty
                  else: line = Parse.convertToCidr(key) # if the value is empty use the key itself

                  try:
                     prefix = re.findall(ipregex,line)[0]
                     if ipaddress.ip_network(prefix, strict = False).subnet_of(subnet):
                        context_output['matching_subnets'] +=((ipDict[loopbackIp])['hostname']+'.'+(loopbackIp.split('.'))[-1]).ljust(20)
                        if value: context_output['matching_subnets'] +=": "+key.strip()+' '+line.strip()+"\n"
                        else: context_output['matching_subnets'] +=": "+line.strip()+"\n"
                  except (IndexError,TypeError):   pass # no ip address found

            else: # for keys with no values
               key = Parse.convertToCidr(key)
               try:
                  prefix = re.findall(ipregex,key)[0]
                  if ipaddress.ip_network(prefix, strict = False).subnet_of(subnet):
                    context_output['matching_subnets'] +=((ipDict[loopbackIp])['hostname']+'.'+(loopbackIp.split('.'))[-1]).ljust(20)
                    context_output['matching_subnets'] +=": "+key.strip()+"\n"
               except (IndexError,TypeError): pass # no ip address found

         else:
            # interface section
            for value in sections[key]:
               value = Parse.convertToCidr(value)
               if not value: continue # skip if the value does no contain ip address
               try:
                  prefix = re.findall(ipregex,value)[0]

                  if ipaddress.ip_network(prefix, strict = False).subnet_of(subnet):
                     context_output['matching_subnets'] +=((ipDict[loopbackIp])['hostname']+'.'+(loopbackIp.split('.'))[-1]).ljust(20)
                     context_output['matching_subnets'] +=": "+key.strip()+' '+value.strip()+"\n"

               except (IndexError,TypeError): pass # no ip address found

      return


   @staticmethod
   def parseJunosOutput(output,ipDict,loopbackIp,subnet):
      sections = {}
      regex = r'inet address|static route|route-filter|prefix-list'
      for line in output.split('\n'):
         if re.findall(regex,line):

            if 'interface' in line and 'unit' in line: # convert unit to dotted notation
               line = line.split()
               interface_index = line.index('interfaces')
               interface = line[interface_index+1]
               vlan = line[interface_index+3]
               line.insert(interface_index+1,interface+'.'+vlan)
               line.remove(interface)
               line.remove('unit')
               line.remove(vlan)
               line = ' '.join(line)

            sections[line.strip('set ')] = []
            key = line.strip('set ')
            continue

         try:
            if line:
               if 'interface' in line and 'unit' in line: # convert unit to dotted notation from ge-0/0/0 unit 10 to ge-0/0/0.10
                  line = line.split()
                  interface_index = line.index('interfaces')
                  interface = line[interface_index + 1]
                  vlan = line[interface_index + 3]
                  line.insert(1,interface+'.'+vlan)
                  line.remove(interface)
                  line.remove('unit')
                  line.remove(vlan)
                  line = ' '.join(line)

               sections[key].append(line.strip()) 

         except UnboundLocalError: pass #the key is undefined, the regex wasnt matched
         except KeyError: pass #key is not in the dictionary


      subnet = ipaddress.ip_network(subnet, strict = False)
      ipregex = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}'


      for key in sections.keys():
         try:
            prefix = re.findall(ipregex,key)[0]

            if prefix:
               if ipaddress.ip_network(prefix, strict = False).subnet_of(subnet):
                 context_output['matching_subnets'] +=((ipDict[loopbackIp])['hostname']+'.'+(loopbackIp.split('.'))[-1]).ljust(20)
                 context_output['matching_subnets'] +=": "+key.strip()+"\n"
         except IndexError: pass # no ip address found



class kazi:

   @staticmethod
   def sshCheckSubnets(loopbackIp,ipDict,username,password,subnet,lock,context_output):

      sshClient = paramiko.SSHClient()
      sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

      try:
         sshClient.connect(loopbackIp, username=username, password=password,timeout=10,allow_agent=False,look_for_keys=False)
         authenticated = True
      except Exception as e:
         authenticated = False
         with lock:
            context_output['errors']+='\n '+(time.ctime()+" (user = "+username+") failed authentication > "+loopbackIp)


      if authenticated:
         console_output = ''
         secureCli = sshClient.invoke_shell()
         if ipDict[loopbackIp]['software'] == 'junos':
            secureCli.send('set cli screen-length 0\n')
            secureCli.send('set cli screen-width 0\n')
            # time.sleep(1)
            # secureCli.recv(65536)
            secureCli.send('show configuration interfaces| display set | match "interfaces.*inet.*address" \n')
            secureCli.send('show configuration routing-options | display set | match routing-options.*static \n')
            secureCli.send('show configuration policy-options | display set | match policy-options.*route-filter \n')
            secureCli.send('show configuration policy-options | display set | match policy-options.*prefix-list |except statement \n')
            time.sleep(10)
            secureCli.close()
            while True:
               cli_output = secureCli.recv(65535).decode("utf-8")
               if not cli_output:
                  break
               for line in cli_output:
                  console_output += str(line)
            sshClient.close()
            Parse.parseJunosOutput(console_output,ipDict,loopbackIp,subnet)

         elif ipDict[loopbackIp]['software'] == 'ios':
            secureCli.send('terminal length 0\n')
            secureCli.send('terminal width 0\n')
            # time.sleep(1)
            # secureCli.recv(65536)
            secureCli.send("sh run | se ^interface\n")
            secureCli.send("sh run | se ^ip route\n")
            secureCli.send("sh run | se ^ip prefix-list\n")
            secureCli.send("sh run | se access-list\n")
            time.sleep(10)
            secureCli.close()
            while True:
               cli_output = secureCli.recv(65535).decode("utf-8")
               if not cli_output: break
               for line in cli_output: console_output += str(line)

            sshClient.close()

            Parse.parseCiscoOutput(loopbackIp,ipDict,console_output,subnet)




   @staticmethod
   def ipCheck(username,password,subnet,ipDict,context_output):

         threads = []
         lock = threading.Lock()

         for loopbackIp in ipDict.keys():
            loopbackIp=loopbackIp.strip()
            if not loopbackIp: continue

            process = threading.Thread(target=kazi.sshCheckSubnets, args=(loopbackIp,ipDict,username,password,subnet,lock,context_output))
            process.start()
            threads.append(process)

         for process in threads:
            process.join()

         if context_output['errors']:
            errors = [ error.strip() for error in context_output['errors'].split('\n') if error.strip()]
         else:
            errors = []

         if context_output['out']:
            summary_output = context_output['out'] # this info will be added in the end of output


         if context_output['matching_subnets']:
            context_output['out'] ='\n Configured ipv4 addresses:'
            context_output['out']+='\n --------------------------'
            context_output['out']+='\n DEVICE'.ljust(20)+ 'SECTION'
            context_output['out']+='\n ------'.ljust(20)+ '-------'
            lines = [line for line in context_output['matching_subnets'].split('\n') if line]
            lines.sort()
            for line in lines: context_output['out']+='\n '+line
            context_output['out']+='\n'
            context_output['out']+='\n'
            context_output['out']+='\n Summary:'
            context_output['out']+='\n --------\n'
            context_output['out']+=' [{}] match(es) for {} or its subnets in active configuration of [{}/{}] checked device(s)'.format(
                             len(lines),subnet,len(ipDict)-len(errors),len(ipDict))

         else:
            context_output['out']+='\n Summary:'
            context_output['out']+='\n --------\n'
            context_output['out']+=' [0] match for {} or its subnets in active configuration of [{}/{}] checked device(s)'.format(
                                          subnet,len(ipDict)-len(errors),len(ipDict))

         try:
            context_output['out']+='\n'+ summary_output +'\n'
         except:
            context_output['out']+='\n\n' # if summary output not there

         context_output['out']+='\n <span class="token function">Errors:\n -------'
         if not context_output['errors']:
            context_output['out']+= '\n [0] error(s)</span>\n'
         else:
           context_output['out']+= '\n [{}] error(s)'.format(len(errors))
           context_output['out']+= '\n'
           context_output['out']+= context_output['errors'] +'</span>\n'


   @staticmethod
   def ipLocate(username,password,ipDict,subnet,context_output):
      context_output['matching_subnets'] = ''
      context_output['out'] = ''
      context_output['errors'] = ''
      context_output['matching_subnets'] = ''
      kazi.ipCheck(username,password,subnet,ipDict,context_output)
      result = context_output['out']
      return result



def locate_ip(username,password,ipDict,subnet,context_output):
   start_time = time.time()
   result = kazi.ipLocate(username,password,ipDict,subnet,context_output)
   run_time = round(time.time()-start_time)
   result = result + '\n\n'+ '[Finished in %s seconds]'%str(run_time)
   return result




