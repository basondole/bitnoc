from jnpr.junos import Device
from lxml import etree
import xml.etree.ElementTree
import re
import threading
import paramiko
import time

def make_dict_from_tree(element_tree):
    """Traverse the given XML element tree to convert it into a dictionary.
 
    :param element_tree: An XML element tree
    :type element_tree: xml.etree.ElementTree
    :rtype: dict
    """
    def internal_iter(tree, accum):
        """Recursively iterate through the elements of the tree accumulating
        a dictionary result.
 
        :param tree: The XML element tree
        :type tree: xml.etree.ElementTree
        :param accum: Dictionary into which data is accumulated
        :type accum: dict
        :rtype: dict
        """
        if tree is None:
            return accum
 
        if tree:
            accum[tree.tag] = {}
            for each in tree:
                result = internal_iter(each, {})
                if each.tag in accum[tree.tag]:
                    if not isinstance(accum[tree.tag][each.tag], list):
                        accum[tree.tag][each.tag] = [
                            accum[tree.tag][each.tag]
                        ]
                    accum[tree.tag][each.tag].append(result[each.tag])
                else:
                    accum[tree.tag].update(result)
        else:
            try: accum[tree.tag] = tree.text.strip()
            except AttributeError: accum[tree.tag] = tree.text
 
        return accum
 
    return internal_iter(element_tree, {})





def plain_number(policer_name):
  '''Convert 5M to 5,000,000
  '''
  # take the last value eg name as BW-L2-policer_30M => ['2', '30']
  number = int(re.findall('\d+',policer_name)[-1]) if re.findall('\d+',policer_name) else 0
  # take the last value eg 'BW-L2-policer_30M' => ['-', 'M']
  suffix = re.findall('\d+(\S)',policer_name)[-1] if re.findall('\d+(\S)',policer_name) else 'k'
  if suffix.lower() == 'g':
    limit = number * 1_000_000_000
  elif suffix.lower() == 'm':
    limit = number * 1_000_000
  elif suffix.lower() == 'k':
    limit = number * 1_000
  return limit


class Junos:

  def parse_fields(pif):
    '''Refine rpc data and initialize missing fields
    '''
    for attr in ('description','address-family', 'layer2-input-policer-information','layer2-output-policer-information'):
      try: 
        if type(pif[attr]) == str: pif[attr] = pif[attr].strip() 
      except KeyError: pif[attr] = ''
    if pif['layer2-input-policer-information'] or pif['layer2-output-policer-information']:
      pif['policer-information'] = ''
      pif['service-type'] = ''
      if type(pif['address-family']) == dict:
        pif['service-type'] = pif['address-family']['address-family-name']
      elif type(pif['address-family']) == list:
        for ad_fam in pif['address-family']:
          pif['service-type'] += f"{ad_fam['address-family-name'].strip()}/"
      try: pif['policer-information'] += pif['layer2-input-policer-information']['layer2-input-policer']
      except KeyError: pif['policer-information'] += '-'
      try:
         pif['policer-information'] += f"/{pif['layer2-output-policer-information']['layer2-output-policer']}"
      except KeyError: pif['policer-information'] += '/-'
    elif type(pif['address-family']) == dict:
      pif['policer-information'] = ''
      pif['service-type'] = pif['address-family']['address-family-name']
      try: pif['policer-information'] += pif['address-family']['policer-information']['policer-input']
      except KeyError: pif['policer-information'] += '-'
      except TypeError: pif['policer-information'] += '-' # ['policer-information'] is string
      try: pif['policer-information'] += f"/{pif['address-family']['policer-information']['policer-output']}"
      except KeyError: pif['policer-information'] += '/-'
      except TypeError: pif['policer-information'] += '/-' # ['policer-information'] is string
    elif type(pif['address-family']) == list:
      pif['policer-information'] = ''
      pif['service-type'] = ''
      for ad_fam in pif['address-family']:
        pif['service-type'] += f"{ad_fam['address-family-name'].strip()}/"
        if ad_fam['address-family-name'].strip() in ('inet','ccc'): # check policers for inet or ccc
          try:
            pif['policer-information'] += ad_fam['policer-information']['policer-input']
          except KeyError: pif['policer-information'] += '-'
          except TypeError: pif['policer-information'] += '-' # ad_fam['policer-information'] is string
          try:
            pif['policer-information'] += f"/{ad_fam['policer-information']['policer-output']}"
          except KeyError: pif['policer-information'] += '/-'
          except TypeError: pif['policer-information'] += '/-' # ad_fam['policer-information'] is string
        else: pif['policer-information'] = '-/-'
    else:
      pif['policer-information'] = '-/-'
      pif['service-type'] = ''
    pif['policer-information'] = pif['policer-information'].replace(f"-{pif['name']}",'')
    in_out = pif['policer-information'].split('/')
    pif['policer-information-calculated'] = f"{plain_number(in_out[0])}/{plain_number(in_out[1])}"
    return pif


  def compile_data(intf):
    '''Fetch interesting fields from the rpc-reply
    '''
    if not intf['interface-information']:
      return [] # no matching interfaces found
    services = []
    for pif in intf['interface-information']['physical-interface']:
      pif = Junos.parse_fields(pif)
      # print(pif['name'],pif['admin-status'],pif['oper-status'],pif['description'],
      #       pif['policer-information'],pif['policer-information-calculated'],pif['service-type'])
      services.append({
        'name': pif['name'],
        'admin-status': pif['admin-status'],
        'oper-status': pif['oper-status'],
        'description': pif['description'],
        'policer-information': pif['policer-information'],
        'policer-information-calculated': pif['policer-information-calculated'],
        'service-type': pif['service-type'].strip('/')
        })
      try:
        if type(pif['logical-interface']) == dict:
           subif = pif['logical-interface']
           subif['admin-status'] = 'down' if 'iff-down' in subif['if-config-flags'].keys()  else 'up'
           subif = Junos.parse_fields(subif)
           # print(subif['name'],subif['admin-status'],pif['oper-status'],subif['description'],
           #       subif['policer-information'],subif['policer-information-calculated'],subif['service-type'])
           name = subif['name'].split('.')[0]
           vlan_id = subif['name'].split('.')[1]
           services.append({
            'name': name,
            'vlan-id': vlan_id,
            'admin-status': subif['admin-status'],
            'oper-status': pif['oper-status'],
            'description': subif['description'],
            'policer-information': subif['policer-information'],
            'policer-information-calculated': subif['policer-information-calculated'],
            'service-type': subif['service-type'].strip('/')
            })

        elif type(pif['logical-interface']) ==  list:
          for subif in pif['logical-interface']:
            subif['admin-status'] = 'down' if 'iff-down' in subif['if-config-flags'].keys()  else 'up'
            subif = Junos.parse_fields(subif)
            # print(subif['name'],subif['admin-status'],pif['oper-status'],subif['description'],
            #       subif['policer-information'],subif['policer-information-calculated'],subif['service-type'])
            name = subif['name'].split('.')[0]
            vlan_id = subif['name'].split('.')[1]
            services.append({
            'name': name,
            'vlan-id': vlan_id,
            'admin-status': subif['admin-status'],
            'oper-status': pif['oper-status'],
            'description': subif['description'],
            'policer-information': subif['policer-information'],
            'policer-information-calculated': subif['policer-information-calculated'],
            'service-type': subif['service-type'].strip('/')
            })
      except KeyError: continue # no logical interfaces
    return services



  def get_if_data(user,passwd,host):
    '''Connect to device and get interface information
    '''
    with Device(user=user,passwd=passwd,host=host) as dev:
       reply = dev.rpc.get_interface_information(detail=True, interface_name='[afgxe][met]*')
    intf = make_dict_from_tree(xml.etree.ElementTree.fromstring(etree.tostring(reply, encoding='unicode')))
    return intf



class Cisco:

  def get_run_sec_if(username,password,host, context_output):

   
    sshClient = paramiko.SSHClient()
    sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
       sshClient.connect(host, username=username, password=password, timeout=10,allow_agent=False,look_for_keys=False)
       authenticated = True
    except Exception as e:
       authenticated = False
       context_output['errors'] += f' {time.ctime()} user = {username} failed authentication > {host}\n'
       return []

    if authenticated==True:

       console_output = ''
       cli = sshClient.invoke_shell()
       cli.send('terminal length 0\n')
       cli.send('terminal width 0\n')
       time.sleep(1)
       cli.recv(65536)
       
       cli.send('show run | section ^interface [GFE]\n')
       time.sleep(5)

       cli.send('show interfaces | include ^[EFG]\n')
       time.sleep(5)
       
       cli.send('show ethernet service instance | i ^[1-9]\n')
       time.sleep(2)

       cli.close()
       while True:
          cli_output = cli.recv(65536).decode("utf-8")
          if not cli_output:
            break
          for line in cli_output:
            console_output+=(line)

       sshClient.close()

       return console_output


  def parse_data(console_output):
    if not console_output:
      return []
    all_output = console_output.split('show interfaces | include ^[EFG]\r')
    sh_run_output = all_output[0]
    sh_intf_output = all_output[1].split('show ethernet service instance | i ^[1-9]\r\n')[0]
    sh_evc_output = all_output[1].split('show ethernet service instance | i ^[1-9]\r\n')[1]

    sh_run_output = sh_run_output.split('\n')
    sh_run_output.pop(0) # first line with show run | section interface
    sh_run_output.pop(-1) # last line with hostname
    if_data = {}


    sh_intf_output = sh_intf_output.split('\r\n')
    sh_intf_output.pop(-1)
    sh_evc_output = sh_evc_output.split('\r\n')
    sh_evc_output.pop(-1)
    if_state = {}

    # pprint(sh_run_output)
    # pprint(sh_intf_output)
    # print(sh_evc_output)

    for line in sh_evc_output:
      #line format: '2141        Static    GigabitEthernet0/0/2     Up'
      line = line.strip().split()
      name = f'{line[2]}:{line[0]}'
      state = line[3].lower()
      if_state[name] = {'state': state}


    for line in sh_intf_output:
      #line format: 'GigabitEthernet0/0/2.4051 is up, line protocol is up '
      line = line.strip().split(',') 
      name = line[0].split()[0]
      admin_state = line[0].split()[-1]
      op_state = line[1].split()[-1]
      if_state[name] = {
                      'admin_state': admin_state,
                      'op_state': op_state
                      }

    for line in sh_run_output:
      line = line.strip('\r')
      if re.search(r'^interface', line):
        interface = re.findall(r'^interface (\S+)',line)[0]
        if_data[interface] = {
                              'name': interface,
                              'admin-status': if_state[interface]['admin_state'],
                              'oper-status': if_state[interface]['op_state'],
                              'description': '',
                              'service-type': ''
                            }
        continue
      elif re.findall(r'^ service instance (\S+)', line):
        service_evc_name = re.findall(r'^ service instance (\S+)', line)[0]
        service_evc_name = f'{interface}:{service_evc_name}'
        if_data[service_evc_name] = {
                                      'name': service_evc_name,
                                      'admin-status': if_state[interface]['admin_state'],
                                      'oper-status': if_state[service_evc_name]['state'],
                                      'description': '',
                                      'service-type': ''
                                      }
        continue

      else:
        description = re.findall(r'^ description ((\S|\s)+)',line)
        in_policer = re.findall(r'^ service-policy input (\S+)',line)
        out_policer = re.findall(r'^ service-policy output (\S+)',line)
        service_internet = re.findall(r'^ ip address (\S+)',line)
        service_l3mpls = re.findall(r'^ vrf (\S+)',line)
        service_l2mpls = re.findall(r'^ xconnect (\S+)',line)
        evc_in_policer = re.findall(r'^  service-policy input (\S+)',line)
        evc_out_policer = re.findall(r'^  service-policy output (\S+)',line)
        evc_description = re.findall(r'^  description ((\S|\s)+)',line)
        evc_service_l2mpls = re.findall(r'^  xconnect (\S+)',line)
        evc_service_efp =  re.findall(r'^  bridge-domain (\d+)',line)
        # efp ethernet flow point: attaches bridge-domain to physical interface
        
        if description:
          if_data[interface]['description'] = line.replace(' description ','')
          continue
        elif in_policer:
          if_data[interface]['policer-information-in'] = in_policer[0]
          continue
        elif out_policer:
          if_data[interface]['policer-information-out'] = out_policer[0]
          continue
        elif service_l3mpls:
          if_data[interface]['service-type'] = 'vrf'
          continue
        elif service_internet and not if_data[interface]['service-type']:
          if_data[interface]['service-type'] = 'inet'
          continue
        elif service_l2mpls and not if_data[interface]['service-type']:
          if_data[interface]['service-type'] = 'l2ckt'
          continue
        elif evc_description:
          if_data[service_evc_name]['description'] = line.replace('  description ','')
          continue
        elif evc_in_policer:
          if_data[service_evc_name]['policer-information-in'] = evc_in_policer[0]
          continue
        elif evc_out_policer:
          if_data[service_evc_name]['policer-information-out'] = evc_out_policer[0]
          continue
        elif evc_service_l2mpls:
          if_data[service_evc_name]['service-type'] = 'evc/l2ckt'
          continue
        elif evc_service_efp:
          if_data[service_evc_name]['service-type'] = 'evc'
        continue

    return if_data


  def fix_cisco_data(if_data):
    services = []
    for interface in if_data:
      if_data[interface]['policer-information'] = ''
      if_data[interface]['policer-information-calculated'] = ''
      try:
        if_data[interface]['policer-information'] += f'{if_data[interface]["policer-information-in"]}/'
      except KeyError:
        if_data[interface]['policer-information'] += '-/'
      try:
        if_data[interface]['policer-information'] += if_data[interface]['policer-information-out']
      except KeyError:
        if_data[interface]['policer-information'] += '-'

      in_out = if_data[interface]['policer-information'].split('/')
      if_data[interface]['policer-information-calculated'] = f"{plain_number(in_out[0])}/{plain_number(in_out[1])}"

      if ':' in if_data[interface]['name']:
        if_data[interface]['vlan-id'] = if_data[interface]['name'].split(':')[1]
        if_data[interface]['name'] = if_data[interface]['name'].split(':')[0]
      else:
        if_data[interface]['vlan-id'] = if_data[interface]['name'].split('.')[1] if '.' in if_data[interface]['name'] else '0'
        if_data[interface]['name'] = if_data[interface]['name'].split('.')[0]

      
      services.append({
        'name': if_data[interface]['name'],
        'vlan-id': if_data[interface]['vlan-id'],
        'admin-status': if_data[interface]['admin-status'],
        'oper-status': if_data[interface]['oper-status'],
        'description': if_data[interface]['description'],
        'policer-information': if_data[interface]['policer-information'],
        'policer-information-calculated': if_data[interface]['policer-information-calculated'],
        'service-type': if_data[interface]['service-type']
        })
    return services
                  





  def get_data(host,username,password, context_output):
    sh_run_output = Cisco.get_run_sec_if(username, password, host, context_output) 
    return Cisco.fix_cisco_data(Cisco.parse_data(sh_run_output))



def worker(user,passwd,host,hosts,context_output):

  context_output['results'] = {}

  if hosts[host]['software'] == 'junos':
    # outcome = Junos.show_details(Junos.compile_data(Junos.get_if_data(user,passwd,host)))
    outcome = Junos.compile_data(Junos.get_if_data(user,passwd,host))
  elif hosts[host]['software'] == 'ios':
    outcome = Cisco.get_data(host, user, passwd, context_output)
  in_total = 0
  out_total = 0
  for service in outcome:
    in_total += int(service['policer-information-calculated'].split('/')[0])
    out_total += int(service['policer-information-calculated'].split('/')[1])
  total = f'{str(in_total)}/{str(out_total)}'
  context_output['results'].update(
    {f'{hosts[host]["hostname"]} {host}': {
                                           'services':outcome,
                                           'total': total}
                                           })


def get_intf_summary(user,passwd,hosts,context_output):
  context_output['errors'] = ''
  threads = []
  for host in hosts:
    t = threading.Thread(target=worker, args=(user,passwd,host,hosts,context_output))
    t.start()
    threads.append(t)
  for t in threads:
    t.join()
  return context_output


if __name__ == '__main__':
  global context_output
  user='fisi'
  passwd='fisi123'

  hosts={'192.168.56.50':{'software': 'junos', 'hostname': 'sample'},
         '192.168.56.36':{'software': 'junos', 'hostname': 'sample'},
         '192.168.56.63':{'software': 'ios', 'hostname': 'sample'},
         }
  context_output = {}
  
  shit = get_intf_summary(user,passwd,hosts,context_output)

  from pprint import pprint

  pprint(shit)


# {'sample 192.168.56.36': {'services': [{'admin-status': 'up',
#                                         'description': 'BasoNX',
#                                         'name': 'em0.0',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'inet/iso/mpls/'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'em1.111',
#                                         'oper-status': 'down',
#                                         'policer-information': 'BW-policer_5M-inet-i/BW-policer_5M-inet-o',
#                                         'policer-information-calculated': '5000000/5000000',
#                                         'service-type': 'inet'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'em1.222',
#                                         'oper-status': 'down',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': ''},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'em1.300',
#                                         'oper-status': 'down',
#                                         'policer-information': '2Mbps-inet-i/2Mbps-inet-o',
#                                         'policer-information-calculated': '2000000/2000000',
#                                         'service-type': 'inet'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'em1.400',
#                                         'oper-status': 'down',
#                                         'policer-information': 'BW-policer_1M-inet-i/BW-policer_1M-inet-o',
#                                         'policer-information-calculated': '1000000/1000000',
#                                         'service-type': 'inet'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'em1.450',
#                                         'oper-status': 'down',
#                                         'policer-information': 'BW-policer_5M-inet-i/BW-policer_5M-inet-o',
#                                         'policer-information-calculated': '5000000/5000000',
#                                         'service-type': 'inet'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'em1.999',
#                                         'oper-status': 'down',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': ''},
#                                        {'admin-status': 'up',
#                                         'description': 'bootstrap',
#                                         'name': 'em2.100',
#                                         'oper-status': 'down',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'inet'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'em2.111',
#                                         'oper-status': 'down',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'inet'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'em2.200',
#                                         'oper-status': 'down',
#                                         'policer-information': '2Mbps-inet-i/2Mbps-inet-o',
#                                         'policer-information-calculated': '2000000/2000000',
#                                         'service-type': 'inet'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'em2.222',
#                                         'oper-status': 'down',
#                                         'policer-information': '10M-inet-i/10M-inet-o',
#                                         'policer-information-calculated': '10000000/10000000',
#                                         'service-type': 'inet'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'em2.333',
#                                         'oper-status': 'down',
#                                         'policer-information': 'BW-policer_10M-inet-i/BW-policer_10M-inet-o',
#                                         'policer-information-calculated': '10000000/10000000',
#                                         'service-type': 'inet'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'em2.450',
#                                         'oper-status': 'down',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': ''},
#                                        {'admin-status': 'up',
#                                         'description': 'CONFIGURED BY NAPLAM',
#                                         'name': 'em2.555',
#                                         'oper-status': 'down',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': ''},
#                                        {'admin-status': 'up',
#                                         'description': 'BasoNX',
#                                         'name': 'em2.666',
#                                         'oper-status': 'down',
#                                         'policer-information': '20M-inet-i/20M-inet-o',
#                                         'policer-information-calculated': '20000000/20000000',
#                                         'service-type': 'inet'},
#                                        {'admin-status': 'up',
#                                         'description': 'configured by ansible',
#                                         'name': 'em2.999',
#                                         'oper-status': 'down',
#                                         'policer-information': '2Mbps-inet-i/2Mbps-inet-o',
#                                         'policer-information-calculated': '2000000/2000000',
#                                         'service-type': 'inet'},
#                                        {'admin-status': 'up',
#                                         'description': 'MPLS L2',
#                                         'name': 'em2.1000',
#                                         'oper-status': 'down',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'ccc'},
#                                        {'admin-status': 'up',
#                                         'description': 'BT test l2',
#                                         'name': 'em2.1002',
#                                         'oper-status': 'down',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'ccc'},
#                                        {'admin-status': 'up',
#                                         'description': 'backhaul configured by '
#                                                        'ansible',
#                                         'name': 'em3.0',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'inet/iso/inet6/'},
#                                        {'admin-status': 'up',
#                                         'description': 'connection to ios',
#                                         'name': 'em4.100',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'inet/iso/inet6/mpls/'},
#                                        {'admin-status': 'up',
#                                         'description': 'connection to iosxe',
#                                         'name': 'em4.300',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'inet/iso/inet6/mpls/'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'em4.900',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'inet'}],
#                           'total': '57000000/57000000'},
#  'sample 192.168.56.50': {'services': [{'admin-status': 'up',
#                                         'description': 'management',
#                                         'name': 'ge-0/0/0.0',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'inet/iso/mpls/'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'ge-0/0/1.100',
#                                         'oper-status': 'up',
#                                         'policer-information': '50Mbps-inet-i/50Mbps-inet-o',
#                                         'policer-information-calculated': '50000000/50000000',
#                                         'service-type': 'inet'},
#                                        {'admin-status': 'down',
#                                         'description': 'sub-if',
#                                         'name': 'ge-0/0/1.200',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': ''}],
#                           'total': '50000000/50000000'},
#  'sample 192.168.56.63': {'services': [{'admin-status': 'up',
#                                         'description': 'management',
#                                         'name': 'FastEthernet0/0',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'internet'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'FastEthernet0/1',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': ''},
#                                        {'admin-status': 'up',
#                                         'description': 'connection to '
#                                                        'junos-vbox',
#                                         'name': 'FastEthernet0/1.100',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'internet'},
#                                        {'admin-status': 'up',
#                                         'description': 'connection to '
#                                                        'iosxe-vmware',
#                                         'name': 'FastEthernet0/1.200',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'internet'},
#                                        {'admin-status': 'up',
#                                         'description': 'connection to '
#                                                        'veos-vbox',
#                                         'name': 'FastEthernet0/1.400',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'internet'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'FastEthernet0/1.600',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'internet'},
#                                        {'admin-status': 'up',
#                                         'description': '',
#                                         'name': 'FastEthernet0/1.800',
#                                         'oper-status': 'up',
#                                         'policer-information': '10Mbps/-',
#                                         'policer-information-calculated': '10000000/0',
#                                         'service-type': 'L3 mpls'},
#                                        {'admin-status': 'up',
#                                         'description': 'l2 connection',
#                                         'name': 'FastEthernet0/1.2000',
#                                         'oper-status': 'up',
#                                         'policer-information': '-/-',
#                                         'policer-information-calculated': '0/0',
#                                         'service-type': 'L2 mpls'}],
#                           'total': '10000000/0'}}
# [Finished in 14.7s]