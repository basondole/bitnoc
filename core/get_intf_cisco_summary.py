import paramiko
import threading
import time
import re
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



def get_run_sec_if(username,password,host, context_output):

 
  sshClient = paramiko.SSHClient()
  sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

  try:
     sshClient.connect(host, username=username, password=password, timeout=10,allow_agent=False,look_for_keys=False)
     authenticated = True
  except Exception as e:
     authenticated = False
     context_output['error']+='\n '+(time.ctime()+" (user = "+username+") failed authentication > "+host)

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
        if_data[interface]['service-type'] = 'L3 mpls'
        continue
      elif service_internet and not if_data[interface]['service-type']:
        if_data[interface]['service-type'] = 'internet'
        continue
      elif service_l2mpls and not if_data[interface]['service-type']:
        if_data[interface]['service-type'] = 'L2 mpls'
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
        if_data[service_evc_name]['service-type'] = 'L2 mpls'
        continue
      elif evc_service_efp:
        if_data[service_evc_name]['service-type'] = 'Ethernet'
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
      if_data[interface]['vlan-id'] = 'EVC'+if_data[interface]['name'].split(':')[1]
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
  context_output = {}
  sh_run_output = get_run_sec_if(username, password, host, context_output) 
  return fix_cisco_data(parse_data(sh_run_output))





if __name__ == '__main__':
  global context_output
  context_output = {}
  user='fisi'
  passwd='fisi123'
  host = '192.168.56.63'


  from pprint import pprint
  shit = get_data(host,user,passwd, context_output)
  pprint(shit)

# [{'admin-status': '',
#   'description': '',
#   'name': 'GigabitEthernet0/0/0',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': ''},
#  {'admin-status': '',
#   'description': '### BACKHAUL TO KIJITONYAMA ###',
#   'name': 'GigabitEthernet0/0/0.38',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': '',
#   'description': '',
#   'name': 'GigabitEthernet0/0/1',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': ''},
#  {'admin-status': '',
#   'description': '### BACKHAUL TO ZANTEL via KIJITONYAMA ODF PASSIVELY ###',
#   'name': 'GigabitEthernet0/0/1.56',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': '',
#   'description': '### L2 SERVICES ###',
#   'name': 'GigabitEthernet0/0/2',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': ''},
#  {'admin-status': '',
#   'description': '0461/026: PRECISSION AIR SERVICES LIMITED NIDC',
#   'name': 'GigabitEthernet0/0/2:2141',
#   'oper-status': '',
#   'policer-information': '100Mbps/100Mbps',
#   'policer-information-calculated': '100000000/100000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '',
#   'name': 'GigabitEthernet0/0/2.409',
#   'oper-status': '',
#   'policer-information': '10Mbps/10Mbps',
#   'policer-information-calculated': '10000000/10000000',
#   'service-type': ''},
#  {'admin-status': '',
#   'description': '"461/028 - Precision Air Services Limited NDC"',
#   'name': 'GigabitEthernet0/0/2.2165',
#   'oper-status': '',
#   'policer-information': '100Mbps/100Mbps',
#   'policer-information-calculated': '100000000/100000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '0345/008: ACCESS KENYA GROUP CBA (NIDC)',
#   'name': 'GigabitEthernet0/0/2.2504',
#   'oper-status': '',
#   'policer-information': '10Mbps/10Mbps',
#   'policer-information-calculated': '10000000/10000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '### L3 SERVICES ###',
#   'name': 'GigabitEthernet0/0/3',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': ''},
#  {'admin-status': '',
#   'description': 'MANAGEMENT NETWORK',
#   'name': 'GigabitEthernet0/0/3.21',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': '',
#   'description': '7669/002: COMMERCIAL BANK OF AFRICA NIDC (CBA) (FIBER DATA)',
#   'name': 'GigabitEthernet0/0/3.153',
#   'oper-status': '',
#   'policer-information': '25Mbps/25Mbps',
#   'policer-information-calculated': '25000000/25000000',
#   'service-type': 'L3 mpls'},
#  {'admin-status': '',
#   'description': '0498/049: SELCOM POLYTECH PLC CBA NIDC',
#   'name': 'GigabitEthernet0/0/3.154',
#   'oper-status': '',
#   'policer-information': '5Mbps/5Mbps',
#   'policer-information-calculated': '5000000/5000000',
#   'service-type': 'L3 mpls'},
#  {'admin-status': '',
#   'description': '7669/005: COMMERCIAL BANK OF AFRICA NIDC (INTERNET)',
#   'name': 'GigabitEthernet0/0/3.155',
#   'oper-status': '',
#   'policer-information': '25Mbps/25Mbps',
#   'policer-information-calculated': '25000000/25000000',
#   'service-type': 'internet'},
#  {'admin-status': '',
#   'description': 'tzNIC NIDC INTERNET',
#   'name': 'GigabitEthernet0/0/3.200',
#   'oper-status': '',
#   'policer-information': '10Mbps/10Mbps',
#   'policer-information-calculated': '10000000/10000000',
#   'service-type': 'internet'},
#  {'admin-status': '',
#   'description': '### OOB MANAGEMENT ###',
#   'name': 'GigabitEthernet0',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L3 mpls'}]
# [Finished in 7.2s]

# [{'admin-status': '',
#   'description': '',
#   'name': 'GigabitEthernet0/0/0',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': ''},
#  {'admin-status': '',
#   'description': 'BACKHAUL TO ZANTEL (VLAN 61)',
#   'name': 'GigabitEthernet0/0/0.61',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': '',
#   'description': '',
#   'name': 'GigabitEthernet0/0/1',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': ''},
#  {'admin-status': '',
#   'description': 'BACKHAUL TO KIJITONYAMA (VLAN 60)',
#   'name': 'GigabitEthernet0/0/1.60',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': '',
#   'description': 'L2 SERVICES',
#   'name': 'GigabitEthernet0/0/2',
#   'oper-status': '',
#   'policer-information': '620Mbps/620Mbps',
#   'policer-information-calculated': '620000000/620000000',
#   'service-type': ''},
#  {'admin-status': '',
#   'description': '5280/033: BELL COMMUNICATIONS NEELKANTH SALT',
#   'name': 'GigabitEthernet0/0/2.839',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/002: BELL COMMUNICATIONS LITHULI 2448',
#   'name': 'GigabitEthernet0/0/2.3101',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"5280/004: Bell Communications Limited - Bell IT Plaza"',
#   'name': 'GigabitEthernet0/0/2.3102',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/005: BELL COMMUNICATIONS SEACLIFF HOTEL',
#   'name': 'GigabitEthernet0/0/2.3103',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/006: BELL COMMUNICATIONS CORAL BEACH',
#   'name': 'GigabitEthernet0/0/2.3104',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"5280/008: Bell Communications Limited - Bell Umoja House"',
#   'name': 'GigabitEthernet0/0/2.3105',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/007 Bell Communication Ltd - BW Plus Peninsula Hotel',
#   'name': 'GigabitEthernet0/0/2.3106',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/013: BELL COMMUNICATIONS MBALIMBALI LODGES ARAMEX',
#   'name': 'GigabitEthernet0/0/2.3107',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/012: BELL COMMUNICATIONS MBALIMBALI LODGES KALENGA',
#   'name': 'GigabitEthernet0/0/2.3108',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/015: BELL COMMUNICATIONS HB WORLDWIDE OFFICE',
#   'name': 'GigabitEthernet0/0/2.3109',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/016: BELL COMMUNICATIONS HB WORLDWIDE RESIDENCE',
#   'name': 'GigabitEthernet0/0/2.3110',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/017: BELL COMMUNICATIONS JK INTERNATIONAL AIRPORT',
#   'name': 'GigabitEthernet0/0/2.3111',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/018: BELL COMMUNICATIONS MLIMANI JUNCTION',
#   'name': 'GigabitEthernet0/0/2.3112',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': "5280/019: BELL COMMUNICATIONS EURO CABLE CHANG'OMBE",
#   'name': 'GigabitEthernet0/0/2.3113',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/020: BELL COMMUNICATIONS XPRESS RENT A CAR',
#   'name': 'GigabitEthernet0/0/2.3114',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/021: BELL COMMUNICATIONS SPEEDY TRANS',
#   'name': 'GigabitEthernet0/0/2.3115',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"5280/062: Bell Communication Ltd - Bell Communications Ltd '
#                  '- DR AGARWAL"',
#   'name': 'GigabitEthernet0/0/2.3116',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/023: BELL COMMUNICATIONS NAKUMATT OYSTERBAY',
#   'name': 'GigabitEthernet0/0/2.3117',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/024: BELL COMMUNICATIONS NAKUMATT MLIMANI CITY',
#   'name': 'GigabitEthernet0/0/2.3118',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/027: BELL COMMUNICATIONS Bell Shreeji Tower Mwisho ST',
#   'name': 'GigabitEthernet0/0/2.3119',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/026: BELL COMMUNICATIONS LAPTOP CITY @ MORROCO',
#   'name': 'GigabitEthernet0/0/2.3180',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/028: BELL COMMUNICATIONS SHOPPERS MASAKI',
#   'name': 'GigabitEthernet0/0/2.3181',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/029: BELL COMMUNICATIONS SHOPPERS MBEZI',
#   'name': 'GigabitEthernet0/0/2.3182',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/045: BELL COMMUNICATIONS LTD QFL OFFICE',
#   'name': 'GigabitEthernet0/0/2.3183',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/054: BELL COMMUNICATIONS SHOPPERS ARUSHA',
#   'name': 'GigabitEthernet0/0/2.3184',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/034: BELL COMMUNICATIONS 285 TOURE DRIVE',
#   'name': 'GigabitEthernet0/0/2.3185',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/035: BELL COMMUNICATIONS GOLDEN COACH',
#   'name': 'GigabitEthernet0/0/2.3186',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/036: BELL COMMUNICATIONS KOTRA TANZANIA, JUBILEE TOWER',
#   'name': 'GigabitEthernet0/0/2.3187',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/039: BELL COMMUNICATIONS QFL RESIDENCE, SUN PLAZA',
#   'name': 'GigabitEthernet0/0/2.3188',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"5280/064  Bell Communications Ltd - Bell GNB Town Office"',
#   'name': 'GigabitEthernet0/0/2.3189',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/040: BELL COMMUNICATIONS PEACE CORPS',
#   'name': 'GigabitEthernet0/0/2.3190',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/037: BELL COMMUNICATIONS RADIO MAARIFA ONNET TANGA',
#   'name': 'GigabitEthernet0/0/2.3191',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/041: BELL COMMUNICATIONS HOT POINT AGGREY ST.',
#   'name': 'GigabitEthernet0/0/2.3192',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/044: BELL COMMUNICATIONS TIX',
#   'name': 'GigabitEthernet0/0/2.3193',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/043: BELL COMMUNICATIONS CITY MALL',
#   'name': 'GigabitEthernet0/0/2.3194',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/042: BELL COMMUNICATIONS SEA SHELLS HOTEL',
#   'name': 'GigabitEthernet0/0/2.3195',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/047: BELL COMMUNICATIONS CABS OFFICE',
#   'name': 'GigabitEthernet0/0/2.3196',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/031: BELL COMMUNICATIONS 23 LAIBON ST. OYSTERBAY',
#   'name': 'GigabitEthernet0/0/2.3197',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/053: BELL COMMUNICATIONS QFL FACTORY',
#   'name': 'GigabitEthernet0/0/2.3198',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/055: BELL COMMUNICATIONS - ECONO LODGE',
#   'name': 'GigabitEthernet0/0/2.3199',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"5280/066  Bell Communications Ltd - Bell Moledina '
#                  'Residence"',
#   'name': 'GigabitEthernet0/0/2.3550',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': 'Bell Communications - Bell Moledina Warehouse ',
#   'name': 'GigabitEthernet0/0/2.3551',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/071: Bell Communications Ltd - Tarmal Soap',
#   'name': 'GigabitEthernet0/0/2.3552',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/069: Bell Communications Ltd - Capital Residence',
#   'name': 'GigabitEthernet0/0/2.3553',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"5280/070: Bell Communication Limited - Bell - RK Pharma"',
#   'name': 'GigabitEthernet0/0/2.3554',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/073:Bell Communications Ltd - Bell Iris Hotel',
#   'name': 'GigabitEthernet0/0/2.3555',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/075:Bell Communications Ltd - Bell Cellulant Mikocheni',
#   'name': 'GigabitEthernet0/0/2.3556',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/076: Bell Communications Ltd - Magore ST',
#   'name': 'GigabitEthernet0/0/2.3557',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"5280/077: Bell Communications - Bell Nelson Mandela"',
#   'name': 'GigabitEthernet0/0/2.3558',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"5280/079: Bell Communications Limited - BC Golden Manor '
#                  'Orphanage"',
#   'name': 'GigabitEthernet0/0/2.3559',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"5280/081: Bell Comm LTD - Habib Bank Nruma"',
#   'name': 'GigabitEthernet0/0/2.3560',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/078: Bell Communications Ltd - BC Upanga',
#   'name': 'GigabitEthernet0/0/2.3561',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/083:Bell Communication Ltd - BC-LE BLANC',
#   'name': 'GigabitEthernet0/0/2.3562',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/084:Bell Communication Ltd - Shoppers Dodoma',
#   'name': 'GigabitEthernet0/0/2.3563',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/086:Bell Communication Ltd - BC FES',
#   'name': 'GigabitEthernet0/0/2.3564',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/082:Bell Communication Ltd - Msasani',
#   'name': 'GigabitEthernet0/0/2.3565',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/085:Bell Communication Ltd - BC-136 Karume',
#   'name': 'GigabitEthernet0/0/2.3566',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/087: BELL COMMUNICATIONS 9 TOURE',
#   'name': 'GigabitEthernet0/0/2.3567',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': 'Bell Communication Ltd - BC SHOPPERS ARUSHA BACK',
#   'name': 'GigabitEthernet0/0/2.3568',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"BELL COMMUNICATIONS LIMITED - BEETLE MOTORS"',
#   'name': 'GigabitEthernet0/0/2.3569',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/056: Bell communications - GNB SOAP FACTORY',
#   'name': 'GigabitEthernet0/0/2.4050',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"Bell Communications  Pran Pen Residence"',
#   'name': 'GigabitEthernet0/0/2.4051',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '<<5280/058  Bell Communications Ltd - Pran Pen Warehouse>>',
#   'name': 'GigabitEthernet0/0/2.4052',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '<<5280/024  Bell Communications Ltd - Hotpoint Mlimani City '
#                  '>>',
#   'name': 'GigabitEthernet0/0/2.4053',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"5280/060  Bell Communications Ltd - Saleh Bhai Glass '
#                  'Office"',
#   'name': 'GigabitEthernet0/0/2.4054',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"5280/059: Bell Communication Ltd - Saleh Bhai Glass '
#                  'Workshop"',
#   'name': 'GigabitEthernet0/0/2.4055',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '"5280/061  Bell Communications Ltd - Vijana Tower',
#   'name': 'GigabitEthernet0/0/2.4056',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/067: BELL FREEDOM TRADERS',
#   'name': 'GigabitEthernet0/0/2.4057',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/065: Bell Communications - Palm Residence',
#   'name': 'GigabitEthernet0/0/2.4058',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '5280/063: Bell Communications LTD - Al Shifa Clinic',
#   'name': 'GigabitEthernet0/0/2.4059',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': 'PEERING FOR BELL',
#   'name': 'GigabitEthernet0/0/3',
#   'oper-status': '',
#   'policer-information': '100Mbps/100Mbps',
#   'policer-information-calculated': '100000000/100000000',
#   'service-type': ''},
#  {'admin-status': '',
#   'description': '5280/049: BELL COMMUNICATIONS DIRECT PEERING WITH LEVEL3 '
#                  'AS3356',
#   'name': 'GigabitEthernet0/0/3.104',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'},
#  {'admin-status': '',
#   'description': '',
#   'name': 'GigabitEthernet0',
#   'oper-status': '',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L3 mpls'}]
# [Finished in 7.5s]



# With getting interface states
# [{'admin-status': 'up',
#   'description': 'management',
#   'name': 'FastEthernet0/0',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': 'up',
#   'description': '',
#   'name': 'FastEthernet0/1',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': ''},
#  {'admin-status': 'up',
#   'description': 'connection to junos-vbox',
#   'name': 'FastEthernet0/1.100',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': 'up',
#   'description': 'connection to iosxe-vmware',
#   'name': 'FastEthernet0/1.200',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': 'up',
#   'description': 'connection to veos-vbox',
#   'name': 'FastEthernet0/1.400',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': 'up',
#   'description': '',
#   'name': 'FastEthernet0/1.600',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': 'up',
#   'description': '',
#   'name': 'FastEthernet0/1.800',
#   'oper-status': 'up',
#   'policer-information': '10Mbps/-',
#   'policer-information-calculated': '10000000/0',
#   'service-type': 'L3 mpls'},
#  {'admin-status': 'up',
#   'description': 'l2 connection',
#   'name': 'FastEthernet0/1.2000',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L2 mpls'}]
# [Finished in 14.2s]

# [{'admin-status': 'up',
#   'description': '',
#   'name': 'GigabitEthernet0/0/0',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': ''},
#  {'admin-status': 'up',
#   'description': 'BACKHAUL TO KIPAWA via AZAM SWITCH PORT Gi0/14',
#   'name': 'GigabitEthernet0/0/0.63',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': 'up',
#   'description': 'BACKHAUL TO UBUNGO (WLL) via AZAM SWITCH PORT Gi0/14',
#   'name': 'GigabitEthernet0/0/0.80',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': 'up',
#   'description': '',
#   'name': 'GigabitEthernet0/0/1',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': ''},
#  {'admin-status': 'up',
#   'description': 'BACKHAUL TO KIJITONYAMA SW3 PORT ge-0/0/0',
#   'name': 'GigabitEthernet0/0/1.64',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': 'up',
#   'description': 'L2 SERVICES TO AZAM SWITCH PORT Gi0/16',
#   'name': 'GigabitEthernet0/0/2',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': ''},
#  {'admin-status': 'up',
#   'description': '5867/014: AZAM MEDIA CHANNEL TEN',
#   'name': 'GigabitEthernet0/0/2:2960',
#   'oper-status': 'up',
#   'policer-information': '6Mbps/6Mbps',
#   'policer-information-calculated': '6000000/6000000',
#   'service-type': ''},
#  {'admin-status': 'up',
#   'description': '5867/042: AZAM MEDIA MABIBO FOR INTERNET FROM BAKHRESA',
#   'name': 'GigabitEthernet0/0/2:3013',
#   'oper-status': 'up',
#   'policer-information': '100Mbps/100Mbps',
#   'policer-information-calculated': '100000000/100000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': 'up',
#   'description': '3202/007: SimbaNET (U) LTD AZAM MEDIA KOLOLO',
#   'name': 'GigabitEthernet0/0/2.2057',
#   'oper-status': 'up',
#   'policer-information': '2Mbps/2Mbps',
#   'policer-information-calculated': '2000000/2000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': 'up',
#   'description': '3202/006: SimbaNET (U) LTD AZAM MEDIA TV-WEST',
#   'name': 'GigabitEthernet0/0/2.2090',
#   'oper-status': 'up',
#   'policer-information': '5Mbps/5Mbps',
#   'policer-information-calculated': '5000000/5000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': 'up',
#   'description': '0508/090: SimbaNET (K) LTD JAMIA MOSQUE HORIZON-TV',
#   'name': 'GigabitEthernet0/0/2.2470',
#   'oper-status': 'up',
#   'policer-information': '5Mbps/5Mbps',
#   'policer-information-calculated': '5000000/5000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': 'up',
#   'description': '9053/001: PILIPILI ENTERTAINMET Co BROADCAST POINT ',
#   'name': 'GigabitEthernet0/0/2.2922',
#   'oper-status': 'up',
#   'policer-information': '10Mbps/10Mbps',
#   'policer-information-calculated': '10000000/10000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': 'up',
#   'description': '3202/002: SimbaNET (U) LTD AZAM MEDIA MABIBO',
#   'name': 'GigabitEthernet0/0/2.2957',
#   'oper-status': 'up',
#   'policer-information': '20Mbps/20Mbps',
#   'policer-information-calculated': '20000000/20000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': 'up',
#   'description': '5867/013: AZAM MEDIA ZBC-TV',
#   'name': 'GigabitEthernet0/0/2.3019',
#   'oper-status': 'up',
#   'policer-information': '4Mbps/4Mbps',
#   'policer-information-calculated': '4000000/4000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': 'up',
#   'description': '0485/019: AZAM MEDIA INTERNET FROM BAKHRESA (BACKUP)',
#   'name': 'GigabitEthernet0/0/2.3031',
#   'oper-status': 'up',
#   'policer-information': '100Mbps/100Mbps',
#   'policer-information-calculated': '100000000/100000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': 'up',
#   'description': '8044/002: AZAM MEDIA MAHAASIN MEDIA TV',
#   'name': 'GigabitEthernet0/0/2.3034',
#   'oper-status': 'up',
#   'policer-information': '4Mbps/4Mbps',
#   'policer-information-calculated': '4000000/4000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': 'up',
#   'description': 'AZAM PAY TANZANIA LTD - MABIBO',
#   'name': 'GigabitEthernet0/0/2.3038',
#   'oper-status': 'up',
#   'policer-information': '150Mbps/150Mbps',
#   'policer-information-calculated': '150000000/150000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': 'up',
#   'description': '5867/017: SimbaNET (U) LTD AZAM MEDIA KAMPALA OFFICE',
#   'name': 'GigabitEthernet0/0/2.3043',
#   'oper-status': 'up',
#   'policer-information': '16Mbps/16Mbps',
#   'policer-information-calculated': '16000000/16000000',
#   'service-type': 'L2 mpls'},
#  {'admin-status': 'up',
#   'description': 'L3 SERVICES',
#   'name': 'GigabitEthernet0/0/3',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': ''},
#  {'admin-status': 'up',
#   'description': 'SWITCH MANAGEMENT',
#   'name': 'GigabitEthernet0/0/3.21',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'internet'},
#  {'admin-status': 'up',
#   'description': '4004/008: AZAM PAYTV LTD TABATA HQ (STREAMING APP INTERNET - '
#                  'VLAN 102)',
#   'name': 'GigabitEthernet0/0/3.102',
#   'oper-status': 'up',
#   'policer-information': '50Mbps/50Mbps',
#   'policer-information-calculated': '50000000/50000000',
#   'service-type': 'internet'},
#  {'admin-status': 'up',
#   'description': '',
#   'name': 'GigabitEthernet0',
#   'oper-status': 'up',
#   'policer-information': '-/-',
#   'policer-information-calculated': '0/0',
#   'service-type': 'L3 mpls'}]
# [Finished in 14.0s]