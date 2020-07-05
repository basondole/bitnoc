import textfsm
import tempfile
import re
import threading
import time
from napalm import get_network_driver
from datetime import timedelta
from jnpr.junos import Device
from lxml import etree
import jxmlease

__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"

class getBGPdata:

    def kazi(ipdict,username,password,context_output,filtering={'state': False}, monitor=False):

        context_output['_out_'] = f'Last refresh {time.ctime()}\n'
        context_output['errors'] = ''

        if monitor:
          context_output['_bgp_neigbor_dict_'] = {}
          context_output['_bgp_neigbor_dict_']['refresh-time'] = time.ctime()
          context_output['_bgp_neigbor_dict_']['collectors'] = {}

        threads = []
        lock = threading.Lock()

        ipList = list(ipdict.keys())

        for ipaddress in ipList:

           t = threading.Thread(target=getBGPdata.bgp_summary,
                                args=(ipaddress,ipdict,username,password,lock,context_output),
                                kwargs={'filtering': filtering, 'monitor': monitor})
           t.start()
           threads.append(t)

        for t in threads:
          t.join()

        if monitor:
          return context_output['_bgp_neigbor_dict_']
        else:
          return context_output['_out_']



    def bgp_summary(host,ipdict,username,password,lock,context_output,filtering={'state': False}, monitor=False):


        def rpc_to_dict(rpc_element):
          rpc_xml = etree.tostring(rpc_element, pretty_print=True, encoding='unicode')
          parsed_dict = jxmlease.parse(rpc_xml)
          return parsed_dict

        bgp_neighbor_info = {}

        junosdriver = get_network_driver('junos')
        iosdriver = get_network_driver('ios')

        if ipdict[host]['software'] == 'ios':
            ipdict[host]['napalm'] = iosdriver(username=username,password=password,hostname=host)

        if ipdict[host]['software'] == 'junos':
            ipdict[host]['napalm'] = junosdriver(username=username,password=password,hostname=host)

        try:
          if not '--' in ipdict[host]['hostname']: # if it is not logical system
            ipdict[host]['napalm'].open()
        except Exception as e:
          prompt = f'INFO: bgp_summary.py via function bgp_summary says: Loading of napalm error {e} for {host}. Confirm if device is synced'
          print(prompt)
          context_output['errors']+= f'\n [{host} {ipdict[host]["hostname"]}]\n '
          context_output['errors']+= f'Loading of napalm error {e}. Confirm if device is synced\n'
          return

        if ipdict[host]['software'] == 'junos':

            if '--' in ipdict[host]['hostname']: # logical system
              main_system_ip = ipdict[host]['mainsystemip']
              system_name = ipdict[host]['systemname']
              router = Device(host=main_system_ip, user=username,passwd=password)
              router.open()
              rpc_element = (router.rpc.get_bgp_summary_information(logical_system=system_name))
              bgp_data = rpc_to_dict(rpc_element)
              try:
                bgp_data = bgp_data['bgp-information']['bgp-peer'] # list of dictionaries
              except KeyError:
                # incase bgp_data equals to {'output': 'BGP is not running'}
                with lock:
                  context_output['errors']+= f'\n [{host} {ipdict[host]["hostname"]}]\n '
                  context_output['errors']+= str(bgp_data).strip('\{').strip('\}') + '\n'
                return


              for peer in bgp_data:
                try:
                  if type(peer['bgp-rib']) == list: # if the peer has many ribs it is 'prolly a route reflector
                    table = 'inet.0'
                  else:
                     table = peer['bgp-rib']['name'] # vrf is in form of TEST.inet.0
                except KeyError:
                  # with virtual olive image the bgp-rib key misses from the peer dict thus cant access peer['bgp-rib']
                  prompt = f'INFO: bgp_summary.py via function bgp_summary says: Logical system {ipdict[host]["hostname"]} rpc-reply missing bgp-rib key'
                  print(prompt)
                  with lock:
                    context_output['errors']+= f'\n [{host} {ipdict[host]["hostname"]}]\n '
                    context_output['errors']+= 'Not supported for this system. rpc-reply missing bgp-rib key\n'
                  return


                if filtering['state'] and bgp_data[peer]['peer-state'].lower() == 'established':
                  continue
                bgp_neighbor_info[peer] = {'peer': bgp_data[peer]['peer-address'],
                                           'peer_as': bgp_data[peer]['peer-as'],
                                           'state': bgp_data[peer]['peer-state'],
                                           'time': bgp_data[peer]['elapsed-time'],
                                           'vrf': table,
                                           'status': 'Enabled',}
              
              # ping the peers that are down
              if filtering['loss']:
              
                for peer in bgp_neighbor_info:

                    table = bgp_neighbor_info[peer]['vrf']
                    if table == 'inet.0':
                      rpc_ping = router.rpc.ping(rapid=True, host=peer, logical_system=system_name)
                    else:
                      vrf_name = table.split('.')[0]
                      rpc_ping = router.rpc.ping(rapid=True, host=peer, logical_system=system_name, routing_instance=vrf_name)

                    ping_results = rpc_to_dict(rpc_ping)

                    try:
                        packet_loss = ping_results['probe-results-summary']['packet-loss']
                        packet_loss = f'Loss {packet_loss}%'
                    except KeyError:
                        packet_loss = ping_results['rpc-error']['error-message'][0:9] # take only nine characters of the error statement

                    bgp_neighbor_info[peer]['ping'] = packet_loss

              # route entries for extracting outgoing interface for peers that are down
              if filtering['alias']:
                for peer in bgp_neighbor_info:

                  rpc_show_route = router.rpc.get_route_information(logical_system=system_name, destination=peer, table=bgp_neighbor_info[peer]['vrf'])
                  routes_data = rpc_to_dict(rpc_show_route)
                  routes_data = routes_data['route-information']['route-table']
                  egress_interface = routes_data ['rt']['rt-entry']['nh']['via']

                  bgp_neighbor_info[peer]['interface'] = egress_interface

              # arp entries
              if filtering['arp']:

                for peer in bgp_neighbor_info:

                  bgp_neighbor_info[peer]['if_arp'] = []
                  if filtering['alias']:
                    rpc_arp = router.rpc.get_arp_table_information(interface=bgp_neighbor_info[peer]['interface'])
                    arp_data = rpc_to_dict(rpc_arp)
                    arp_table = arp_data['arp-table-information']['arp-table-entry']
                    if type(arp_table) == list:
                      for arp_entry in arp_table:
                        bgp_neighbor_info[peer]['if_arp'].append(f"{arp_entry['ip-address']}:{arp_entry['mac-address']}")
                    else:
                      bgp_neighbor_info[peer]['if_arp'].append(f"{arp_table['ip-address']}:{arp_table['mac-address']}")
                  
                  bgp_neighbor_info[peer]['ip_arp'] = []
                  rpc_arp = router.rpc.get_arp_table_information(hostname=peer)
                  arp_data = rpc_to_dict(rpc_arp)
                  arp_table = arp_data['arp-table-information']['arp-table-entry']
                  if type(arp_table) == list:
                    for arp_entry in arp_table:
                      bgp_neighbor_info[peer]['ip_arp'].append(f"{arp_entry['ip-address']}:{arp_entry['mac-address']}")
                  else:
                    bgp_neighbor_info[peer]['ip_arp'].append(f"{arp_table['ip-address']}:{arp_table['mac-address']}")


                  # for presentation purposes when using format.presentation method
                  if not bgp_neighbor_info[peer]['ip_arp']:
                    bgp_neighbor_info[peer]['ip_arp'] = ['-']
                  if filtering['alias']:
                    if not bgp_neighbor_info[peer]['if_arp']:
                      bgp_neighbor_info[peer]['if_arp'] = ['-']

                  # consolidate arp entries
                  bgp_neighbor_info[peer]['arp'] = bgp_neighbor_info[peer]['if_arp'] + bgp_neighbor_info[peer]['ip_arp']

              router.close() # close pyez session

            else:
              # main system bgp

              bgp_data = ipdict[host]['napalm'].get_bgp_neighbors()

              for table in bgp_data:
                  for peer in bgp_data[table]['peers']:
                      state = bgp_data[table]['peers'][peer]['is_up']
                      if state == True: state = 'Established'
                      else: state = 'Down'

                      if filtering['state'] and state.lower() == 'established':
                        continue

                      status = bgp_data[table]['peers'][peer]['is_enabled']
                      if status == True: status = 'Enabled'
                      else: status = 'Shutdown'
                      duration = str(timedelta(seconds=bgp_data[table]['peers'][peer]['uptime']))
                      if 'days' in duration: duration = duration.replace(' days,','d')
                      elif 'day' in duration: duration = duration.replace(' day,','d')
                      bgp_neighbor_info[peer] = {'peer': peer,
                                                 'peer_as': bgp_data[table]['peers'][peer]['remote_as'],
                                                 'state': state,
                                                 'status': status,
                                                 'time': duration,
                                                 'vrf': table}
              # ping the peers that are down
              if filtering['loss']:

                for peer in bgp_neighbor_info:

                    table = bgp_neighbor_info[peer]['vrf']
                    if table == 'global': table = ''

                    ping_results = ipdict[host]['napalm'].ping(peer,vrf=table)
                    try:
                        packet_loss = ping_results['success']['packet_loss']
                        packet_loss = 'Loss %d%%'%(packet_loss*20)

                    except KeyError:
                        try: 
                            packet_loss = ping_results['error']
                            if packet_loss == 'Packet loss 100': packet_loss='Loss 100%'
                            else: packet_loss = ping_results['error'][0:9] # take only nine characters of the error statement
                        except: packet_loss = ' '

                    bgp_neighbor_info[peer]['ping'] = packet_loss


              # route entries for extracting outgoig interface for peers that are down
              if filtering['alias']:

                for peer in bgp_neighbor_info:

                  routes_data = ipdict[host]['napalm'].get_route_to(peer)

                  table = bgp_neighbor_info[peer]['vrf']

                  if table == 'global': 
                    if ':' in peer:
                      table = 'inet6.0'
                    else:
                      table = 'inet.0'


                  egress_interface = []

                  for route in routes_data:
                      if route != '0.0.0.0/0':
                          for entry in  routes_data[route]:
                             if entry['routing_table'].startswith(table):
                                egress_interface.append(entry['outgoing_interface'])

                  try:
                      egress_interface
                      egress_interface = egress_interface[0] # take the first entry if there are many

                  except: egress_interface = ''

                  bgp_neighbor_info[peer]['interface'] = egress_interface


              # arp entries
              if filtering['arp']:

                arp_table = ipdict[host]['napalm'].get_arp_table()

                for peer in bgp_neighbor_info:

                  bgp_neighbor_info[peer]['ip_arp'] = []
                  bgp_neighbor_info[peer]['if_arp'] = []

                  for arp_entry in arp_table:
                      if arp_entry['ip'] == peer:
                          bgp_neighbor_info[peer]['ip_arp'].append(f"{arp_entry['ip']}:{arp_entry['mac']}")

                      if filtering['alias']:
                        if arp_entry['interface'] == bgp_neighbor_info[peer]['interface']:
                          bgp_neighbor_info[peer]['if_arp'].append(f"{arp_entry['ip']}:{arp_entry['mac']}")

                  # for presentation purposes when using format.presentation method
                  if not bgp_neighbor_info[peer]['ip_arp']:
                    bgp_neighbor_info[peer]['ip_arp'] = ['-']
                  if filtering['alias']:
                    if not bgp_neighbor_info[peer]['if_arp']:
                      bgp_neighbor_info[peer]['if_arp'] = ['-']

                  # consolidate arp entries
                  bgp_neighbor_info[peer]['arp'] = bgp_neighbor_info[peer]['if_arp'] + bgp_neighbor_info[peer]['ip_arp']

              # interface status for both main and logical system
              if filtering['alias']:

                try:
                  interfaces = ipdict[host]['napalm'].get_interfaces()
                except:
                  interfaces = {} # if napalm fails

                for peer in bgp_neighbor_info:

                  bgp_neighbor_info[peer]['if_description'] = '-'
                  bgp_neighbor_info[peer]['if_oper_status'] = '- '
                  bgp_neighbor_info[peer]['if_admin_status'] = '-  '

                  # if the interface does not exist there is no intf info
                  if not bgp_neighbor_info[peer]['interface']:
                    bgp_neighbor_info[peer]['interface'] = '- '
                    continue

                  for interface in interfaces.keys():
                    if interface == bgp_neighbor_info[peer]['interface']:

                       op_state = interfaces[interface]['is_up']
                       if op_state==True:
                        op_state = 'Up'
                       else:
                        op_state = 'Down'

                       ad_state = interfaces[interface]['is_enabled']
                       if ad_state==True:
                        ad_state = 'Up'
                       else:
                        ad_state = 'Down'

                       bgp_neighbor_info[peer]['if_description'] = interfaces[interface]['description']
                       bgp_neighbor_info[peer]['if_oper_status'] = op_state
                       bgp_neighbor_info[peer]['if_admin_status'] = ad_state



        elif ipdict[host]['software'] == 'ios':

            bgp_txt_dict = ipdict[host]['napalm'].cli(['show bgp all neighbors'])
            bgp_txt_data = bgp_txt_dict['show bgp all neighbors']

            bgp_data = format.parseCiscoBGP(bgp_txt_data)

            bgp_neighbor_info = {}
            for peer in bgp_data:
              if filtering['state'] and bgp_data[peer]['state'].lower() == 'established':
                continue
              bgp_neighbor_info[peer] = bgp_data[peer]


            # ping the peers
            if filtering['loss']:

              for peer in bgp_neighbor_info:

                table = bgp_neighbor_info[peer]['vrf']

                ping_results = ipdict[host]['napalm'].ping(peer,vrf=table)
                try: 
                  packet_loss = ping_results['success']['packet_loss']
                  packet_loss = 'Loss %d%%'%(packet_loss*20) # napalm sends 5 packets multiply by 20 to get percentage

                except KeyError:
                    try: 
                        packet_loss = ping_results['error']
                        if packet_loss == 'Packet loss 100':
                          packet_loss='Loss 100%'
                        else:
                          packet_loss = ping_results['error'][0:9] # take only nine characters of the error statement
                    except:
                      packet_loss = ' '

                bgp_neighbor_info[peer]['ping'] = packet_loss


            # route entries for extracting outgoig interface
            if filtering['alias']:

              for peer in bgp_neighbor_info:

                table = bgp_neighbor_info[peer]['vrf']

                if not table:
                    if ':' in peer: # for ipv6
                      routes_txt_dict = ipdict[host]['napalm'].cli(['show ipv6 route '+peer])
                      routes_txt_data = routes_txt_dict['show ipv6 route '+peer]
                    else:
                      routes_txt_dict = ipdict[host]['napalm'].cli(['show ip route '+peer])
                      routes_txt_data = routes_txt_dict['show ip route '+peer]
                else:
                    if ':' in peer: # for ipv6
                      routes_txt_dict = ipdict[host]['napalm'].cli(['show ipv6 route vrf %s %s'%(table,peer)])
                      routes_txt_data = routes_txt_dict['show ipv6 route vrf %s %s'%(table,peer)]
                    else:
                      routes_txt_dict = ipdict[host]['napalm'].cli(['show ip route vrf %s %s'%(table,peer)])
                      routes_txt_data = routes_txt_dict['show ip route vrf %s %s'%(table,peer)]

                egress_interface = ''


                for line in routes_txt_data.split('\n'):
                    # if there is one route entry
                    if re.search(r'^  \*.*via (\S+)',line):
                        egress_interface = (re.findall(r'^  \*.*via (\S+)',line))[0]
                    # if there are multiple entries
                    elif re.search(r'via \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3},',line):
                        egress_interface = line.split()[-1]
                    # for ipv6
                    elif re.search(r':.*, ',line):
                        egress_interface = line.split()[-1]

               
                bgp_neighbor_info[peer]['interface'] = egress_interface


            # arp entries
            if filtering['arp']:

              for peer in bgp_neighbor_info:

                bgp_neighbor_info[peer]['ip_arp'] = []
                bgp_neighbor_info[peer]['if_arp'] = []

                table = bgp_neighbor_info[peer]['vrf']
                if filtering['alias']:
                  interface = bgp_neighbor_info[peer]['interface']

                if not table:
                  ip_arp_txt_dict = ipdict[host]['napalm'].cli(['show arp '+peer])
                  ip_arp_txt_data = ip_arp_txt_dict['show arp '+peer]
                  if filtering['alias']:
                    if_arp_txt_dict = ipdict[host]['napalm'].cli(['show arp '+interface])
                    if_arp_txt_data = if_arp_txt_dict['show arp '+interface]
                else:
                  ip_arp_txt_dict = ipdict[host]['napalm'].cli(['show arp vrf %s %s'%(table,peer)])
                  ip_arp_txt_data = ip_arp_txt_dict['show arp vrf %s %s'%(table,peer)]
                  if filtering['alias']:
                    if_arp_txt_dict = ipdict[host]['napalm'].cli(['show arp vrf %s %s'%(table,interface)])
                    if_arp_txt_data = if_arp_txt_dict['show arp vrf %s %s'%(table,interface)]
                


                arp_table = []
                for entry in ip_arp_txt_data.split('\n'):
                    if re.search(r'^Internet',entry):
                        arp_table.append({'ip':entry.split()[1],
                                          'mac':entry.split()[3],
                                          'interface':entry.split()[-1]
                                        })

                for arp_entry in arp_table:
                    if arp_entry['ip'] == peer:
                        bgp_neighbor_info[peer]['ip_arp'].append(f"{arp_entry['ip']}:{arp_entry['mac']}")
                # for presentation purposes when using format.presentation method
                if not bgp_neighbor_info[peer]['ip_arp']: bgp_neighbor_info[peer]['ip_arp'] = ['-']


                if filtering['alias']:
                  arp_table = []
                  for entry in if_arp_txt_data.split('\n'):
                      if re.search(r'^Internet',entry):
                          arp_table.append({'ip':entry.split()[1],
                                            'mac':entry.split()[3],
                                            'interface':entry.split()[-1]
                                          })
                  for arp_entry in arp_table:
                      if arp_entry['interface'] == bgp_neighbor_info[peer]['interface']:
                          bgp_neighbor_info[peer]['if_arp'].append(f"{arp_entry['ip']}:{arp_entry['mac']}")

                # for presentation purposes when using format.presentation method
                if filtering['alias']:
                  if not bgp_neighbor_info[peer]['if_arp']: bgp_neighbor_info[peer]['if_arp'] = ['-']
                # consolidate arp
                bgp_neighbor_info[peer]['arp'] = bgp_neighbor_info[peer]['if_arp'] + bgp_neighbor_info[peer]['ip_arp']



            # interface status
            if filtering['alias']:

              try: interfaces = ipdict[host]['napalm'].get_interfaces()
              except: interfaces = [] # if napalm fails

              for peer in bgp_neighbor_info:

                bgp_neighbor_info[peer]['if_description'] = '- '
                bgp_neighbor_info[peer]['if_oper_status'] = '- '
                bgp_neighbor_info[peer]['if_admin_status'] = '-  '


                # if the interface does not exist there is no intf info
                if not bgp_neighbor_info[peer]['interface']:
                  bgp_neighbor_info[peer]['interface'] = '- '
                  continue

                else:

                  for interface in interfaces.keys():
                    if interface == bgp_neighbor_info[peer]['interface']:

                       op_state = interfaces[interface]['is_up']
                       if op_state==True: op_state = 'Up'
                       else: op_state = 'Down'

                       ad_state = interfaces[interface]['is_enabled']
                       if ad_state==True: ad_state = 'Up'
                       else: ad_state = 'Down'

                       bgp_neighbor_info[peer]['if_description'] = interfaces[interface]['description']
                       bgp_neighbor_info[peer]['if_oper_status'] = op_state
                       bgp_neighbor_info[peer]['if_admin_status'] = ad_state


        else: return 

        #close the session
        ipdict[host]['napalm'].close()

        if monitor:
          context_output['_bgp_neigbor_dict_']['collectors'][host] = {}
          context_output['_bgp_neigbor_dict_']['collectors'][host]['name'] = f'{ipdict[host]["hostname"].replace("_"," ").upper()} {host}'
          context_output['_bgp_neigbor_dict_']['collectors'][host]['peers'] = bgp_neighbor_info
          context_output['_bgp_neigbor_dict_']['collectors'][host]['total-sessions'] = len(bgp_neighbor_info)

        else:
          summary = format.presentation(bgp_neighbor_info,filtering=filtering)
          with lock:
              try: context_output['_out_']+= '\n[%s %s]'%(host,ipdict[host]['hostname'])
              except: context_output['_out_']+= '[%s]'%host
              context_output['_out_']+= '\n'
              context_output['_out_']+= '\n'
              context_output['_out_']+= summary
              context_output['_out_']+= '\n'






class format:

    def parseCiscoBGP(raw_data):

        template = r'''Value peer (\S+)
Value peer_as (\d+)
Value vrf (\S+)
Value state (\S+)
Value time (\S+)
Value status (\S+)

Start
  ^BGP neighbor is ${peer},  (vrf ${vrf},  )?remote AS ${peer_as}
  ^ Administratively ${status}
  ^  BGP state = ${state}, (up|down) for ${time} -> Record
  ^  BGP state = ${state} -> Record'''


        tmp = tempfile.NamedTemporaryFile(delete=False)
        with open(tmp.name, 'w') as f:
           f.write(template)

        with open(tmp.name, 'r') as f:
            fsm = textfsm.TextFSM(f)
            fsm_results = fsm.ParseText(raw_data)
            parsed = [dict(zip(fsm.header, row)) for row in fsm_results]
            parsed = {row[0]:dict(zip(fsm.header, row)) for row in fsm_results}

        for peer in parsed:
            if not parsed[peer]['status']:
                parsed[peer]['status'] = 'Enabled'
            else: parsed[peer]['status'] = 'Shutdown'
          
        return parsed

    def presentation(bgpdict,filtering={'state': True}):

        output = ' PEER ID'.ljust(17)+'PEER AS'.ljust(10)+'STATE'.ljust(13)+'STATUS'.ljust(10)+'TIME'.ljust(15)+'PING'.ljust(11)
        output+= 'INTERFACE'.ljust(15)+'IF ADMIN'.ljust(9)+'IF STATE'.ljust(9)+'ARP\\r IF ARP'.ljust(34)+'IF ALIAS'
        output+= '\n'
        output+= ' ---------------'.ljust(17)+'-------'.ljust(10)+'-----------'.ljust(13)+'--------'.ljust(10)+'-------------'.ljust(15)
        output+= '---------'.ljust(11)
        output+= '-------------'.ljust(15)+'--------'.ljust(9)+'--------'.ljust(9)
        output+= '--------------------------------'.ljust(34)
        output+= '--------'
        output+= '\n'

        for peer in bgpdict:
            if filtering['state'] and bgpdict[peer]['state'].lower() == 'established': continue
            output+=' '
            output+=peer.ljust(17)+str(bgpdict[peer]['peer_as']).ljust(10)+bgpdict[peer]['state'].ljust(13)+bgpdict[peer]['status'].ljust(10)
            output+=bgpdict[peer]['time'].ljust(15)
            if filtering['loss']: output+=bgpdict[peer]['ping'].ljust(11)
            
            # for consistent presentation modify the interface name length (cisco)
            if filtering['alias']:
              egress_interface = bgpdict[peer]['interface']
              if len(egress_interface) > 14:
                  egress_interface = egress_interface.replace('thernet','')
                  egress_interface = egress_interface.replace('abit','')
                  bgpdict[peer]['interface'] = egress_interface

              output+=bgpdict[peer]['interface'].ljust(15)+bgpdict[peer]['if_admin_status'].ljust(9)+bgpdict[peer]['if_oper_status'].ljust(9)

            if filtering['arp']:
              for arp in bgpdict[peer]['ip_arp']:
                  # arp is a dict convert to string and remove brackets
                  arp = str(arp).replace("'","").replace("{","").replace("}","")
                  output+= arp.ljust(34)

            if filtering['alias']:
              output+= bgpdict[peer]['if_description']
              output+='\n'

              for arp in bgpdict[peer]['if_arp']:
                  # arp is a dict convert to string and remove brackets
                  arp = str(arp).replace("'","").replace("{","").replace("}","")
                  output+= ' '*109 # adjust the column
                  output+= arp
                  output+= '\n'
            output+= '\n'
            
        output+= '\n'
        output+= 'Total bgp sessions %d'%len(bgpdict)
        output+= '\n'

        return output




def cool_bgp_summary(ipdict,username,password,context_output,filtering={'state': False}, monitor=False):



    start_time = time.time()
    print(f'[{time.ctime()}] INFO: bgp_summary.py via function cool_bgp_summary says: started collecting bgp data')

    result = getBGPdata.kazi(ipdict,username,password,context_output,filtering=filtering, monitor=monitor)

    run_time = round(time.time()-start_time)
    print(f'[{time.ctime()}] INFO: bgp_summary.py via function cool_bgp_summary says: finished collecting bgp data')

    if monitor:
      result.update({'run_time': run_time})
      result.update({'errors': context_output["errors"].split('\n')})
      return result # neighbor dict

    else:
      result = result
      result += f'\n<span class="token function">Errors:\n-------'
      result += f'{context_output["errors"]}</span>'
      result += '\n'+ '[Finished in %s seconds]'%str(run_time)
      return result # text blob



