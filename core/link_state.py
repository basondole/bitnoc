'''
Generate topology database for link  state protocol.
The topology database can then be used to generate network diagram.
Pre-requisites:
    - Link type should be point-to-point links
    - For juniper equipment JunOS 11.4R9 or later is required
    
NB: If pre-requisites are not met diagram data will still be useful but just not very accurate
'''

import pprint
import subprocess
import binascii
import sys
import networkx as nx
from pysnmp.entity.rfc3413.oneliner import cmdgen
import time
import threading
import queue
from ipaddress import ip_network



__author__ = "Paul S.I. Basondole"
__credits__ = "Mihai Catalin Teodosiu"
__version__ = "1.0.1"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"



def snmp_get(ip,comm,protocol):
    ''' Collect information from devices and return a dictionary of devices and their link state'''

    global devices_list, unquerried_neighbors

    nbridlist = []
    nbriplist = []
    _device = {}
    

    hostname_oid = '1.3.6.1.2.1.1.5'
    interface_oid = '1.3.6.1.2.1.31.1.1.1.1'

    if protocol == 'ospf':
        router_id_oid = ['1.3.6.1.2.1.14.1.1']
        neighbor_router_id_oid = ['1.3.6.1.2.1.14.10.1.3']
        neighbor_router_ip_oid = ['1.3.6.1.2.1.14.10.1.1']
        protocol_ifindex_oid = [] 

    if protocol == 'isis':
        ''' to match possible oids from
        juniper systemID, Cisco ciissysID and Juniper Ent systemID
        '''
        router_id_oid = ['1.3.6.1.2.1.138.1.1.1.3',
                         '1.3.6.1.4.1.4874.2.2.38.1.1.1.1.4',
                         '1.3.6.1.4.1.9.10.118.1.1.1.3']

        neighbor_router_id_oid = ['1.3.6.1.2.1.138.1.6.1.1.6',
                                  '1.3.6.1.4.1.9.10.118.1.6.1.1.6']

        neighbor_router_ip_oid = ['1.3.6.1.2.1.138.1.6.3.1.3',
                                  '1.3.6.1.4.1.9.10.118.1.6.3.1.3']

        protocol_ifindex_oid = ['1.3.6.1.2.1.138.1.3.2.1.2',
                                '1.3.6.1.4.1.9.10.118.1.3.2.1.2']


    #Creating command generator object
    cmdGen = cmdgen.CommandGenerator()
    
    '''
    Performing SNMP GETNEXT operations on the OIDs
    The basic syntax of nextCmd: nextCmd(authData, transportTarget, *varNames)
    The nextCmd method returns a tuple of (errorIndication, errorStatus, errorIndex, varBindTable)
    '''
    
    hostname = False
    errIndication,errStatus,errIndex, hostname = cmdGen.nextCmd(cmdgen.CommunityData(comm),
                                                                cmdgen.UdpTransportTarget((ip, 161)),                                                                  
                                                                hostname_oid)

    for item in hostname:
        for oid, host in item:
            _host = str(host)
            print('%s = %s' % (oid, host))


    # check if the hostname is already querried, if it is return
    for n in range(0, len(devices_list)):
        if devices_list[n]["Host"] == _host:
            print(_host, "SKIPPED ALREADY POLLED")
            return


    if protocol.lower() != 'ospf':

        interfaces = False
        errIndication,errStatus,errIndex, interfaces = cmdGen.nextCmd(cmdgen.CommunityData(comm),
                                                                      cmdgen.UdpTransportTarget((ip, 161)),                                                                  
                                                                      interface_oid)

        all_interfaces = {}
        for item in interfaces:
            for oid, iface in item:
                all_interfaces[str(oid)]=str(iface)




    hostId = False
    for oid in router_id_oid:
        errIndication,errStatus,errIndex, hostId = cmdGen.nextCmd(cmdgen.CommunityData(comm),
                                                                  cmdgen.UdpTransportTarget((ip, 161)),
                                                                  oid)
        if hostId: break



    for item in hostId:
        for oid, hostid in item:
            _host_id ='.'.join([str(octate) for octate in hostid])



    varBindNbrTable = False
    for oid in neighbor_router_id_oid:
        errIndication,errStatus,errIndex, varBindNbrTable = cmdGen.nextCmd(cmdgen.CommunityData(comm),
                                                                           cmdgen.UdpTransportTarget((ip, 161)),
                                                                           oid)
        if varBindNbrTable: break


    for varBindNbrTableRow in varBindNbrTable:
        for oid, nbrid in varBindNbrTableRow:

            nbr_r_id = '.'.join([str(octate) for octate in nbrid])
            nbridlist.append(nbr_r_id)

            

    varBindNbrIpTable = False
    for oid in neighbor_router_ip_oid:
        errorIndication, errorStatus, errorIndex, varBindNbrIpTable = cmdGen.nextCmd(cmdgen.CommunityData(comm),
                                                                                     cmdgen.UdpTransportTarget((ip, 161)),
                                                                                     oid)
        if varBindNbrIpTable: break
    

    for varBindNbrIpTableRow in varBindNbrIpTable:
        for oid, nbrip in varBindNbrIpTableRow:

            _ip = '.'.join([str(octate) for octate in nbrip])
            
            try:
               ip_network(_ip,strict=False) # check if the ip is a valid ipaddress
               nbriplist.append(_ip)

            except: continue


    if protocol.lower() != 'ospf':

        varIfIndex = False
        for oid in protocol_ifindex_oid:
            errIndication,errStatus,errIndex, varIfIndex = cmdGen.nextCmd(cmdgen.CommunityData(comm),
                                                                          cmdgen.UdpTransportTarget((ip, 161)),
                                                                          oid)
            if varIfIndex: break

        if varIfIndex:
            ifnames = []
            for item in varIfIndex:
                for oid, ifindex in item:
                    if str(all_interfaces[interface_oid+'.'+str(ifindex)]).lower().startswith('lo'):
                        continue
                    else: ifnames.append(all_interfaces[interface_oid+'.'+str(ifindex)])

            '''
            remove logical tunnel interfaces configured on the logical system side for junos
            this is to avoid polling the logical system if the adjacency is between logical and main system
            '''
            if ifnames:
                for x in range(len(ifnames)):
                    try:
                      if ifnames[x].split('.')[0] == ifnames[x+1].split('.')[0]:
                         if 'lt' in ifnames[x]: ifnames.pop(x+1)
                    except IndexError: pass



    #Adding data of the polled device in the _device dictionary
    _device["Host"] = _host
    _device["HostId"] = _host_id
    _device["NbrRtrId"] = nbridlist
    _device["NbrRtrIp"] = nbriplist
    if protocol.lower() != 'ospf': _device["Interface"] = ifnames


    for nid in _device["NbrRtrId"]:
        unquerried_neighbors.append(nid)
    
    devices_list.append(_device)

    return devices_list




def find_unqueried_neighbors(ip,comm,protocol,popup=False):
    ''' Uses the snmp_get function to querry found neighbors
    '''

    global devices_list, querried_neighbors, unquerried_neighbors, failed_neighbors
    
    querried_neighbors = list(set(querried_neighbors))
    
    # Neighbor Router IDs
    all_nbr_ids = []

    #print len(devices_list)
    for n in range(0, len(devices_list)):

        for nid in devices_list[n]["NbrRtrId"]:
        
            if nid == "0.0.0.0": pass
        
            else:
                if nid not in querried_neighbors: all_nbr_ids.append(nid)


                    
    all_nbr_ids = list(set(all_nbr_ids)) # remove duplicates


    print("Neighbors of the host, these neighbors need to be polled")
    print(all_nbr_ids)


    print("lenght of devices_list",len(devices_list))
    
    # Running the snmp_get() function for each unqueried neighbor
    for q in all_nbr_ids:
        for r in range(0, len(devices_list)):

            for index,s in enumerate(devices_list[r]["NbrRtrId"]):

                if q == s:

                    print('    found router-id that matches neighbor ID')

                    try: new_ip = devices_list[r]["NbrRtrIp"][index]
                    except IndexError: continue # if no corresponding neighbor ip address


                    print("    NEW_IP",new_ip,"POLLING")
                    try:
                        snmp_get(new_ip,comm,protocol)
                        querried_neighbors.append(s)
                        print("    ",q,r,s,new_ip, "DONE POLLING")
                    except Exception as e:
                       print(e)
                       querried_neighbors.append(s)
                       failed_neighbors.append(s)
                       print("    ",q,r,s,new_ip, "SKIPPED FAIL POLL")


    return all_nbr_ids



def neighborship(final_devices_list):
    '''
    Creating list of neighborships
    '''
    neighborship_dict = {}
    for each_dictionary in final_devices_list:
        for index, each_neighbor in enumerate(each_dictionary["NbrRtrId"]):
            each_tuple = (each_dictionary["HostId"], each_neighbor)
            neighborship_dict[each_tuple] = each_dictionary["NbrRtrIp"][index]
    return neighborship_dict



def id_to_name(final_devices_list):
    ''' The SNMP poll will return router id. This function maps the id to hostnames to be used for node labels
    '''
    id_host = {}
    for item in final_devices_list: id_host[item['HostId']] = item['Host']
    return id_host


def ip_to_name(final_devices_list,neighborship_dict):
    ''' Maps link IP address to the interface name to be used for link labels
    '''
    ip_iface = {}
    for item in final_devices_list:

        if len(item["NbrRtrId"]) > len(item['Interface']):
            # to compensate for non point-to-point links where one interface has many adjancencies
            assumed_interface = item['Interface'][0]
            item['Interface'] = [assumed_interface for x in range(len(item['NbrRtrId']))]

        for index, each_neighbor in enumerate(item["NbrRtrId"]):
            each_tuple = (each_neighbor,item["HostId"])
            ip_iface[each_tuple] = item['Interface'][index] + '\n'+ item["NbrRtrIp"][index]
            try: neighborship_dict[each_tuple]= item['Interface'][index] + '\n'+ neighborship_dict[each_tuple]
            except KeyError: pass
    
    return neighborship_dict




def build(ip,comm,protocol):
    ''' Collect devices data and build the neighbourship database
    '''
    global devices_list, querried_neighbors, unquerried_neighbors, failed_neighbors

    unquerried_neighbors = [] # we start with one unquerried router assumin the router id to be 0
    failed_neighbors = []

    try: devices_list = snmp_get(ip,comm,protocol)
    except: return [],{} # if polling of first device fails

    # before running the snmp get the number of unquerried neighbors should have been 1
    # which is the router we start to poll initially this is the base router
    # because we do not know the router id before polling we cant add the appropriate value
    # to the unquerried neighbors list, here we add it after we have got it from the first poll
    unquerried_neighbors.append(devices_list[0]["HostId"])

    querried_neighbors.append(devices_list[0]["HostId"])
    pprint.pprint(devices_list)


    if not devices_list[0]["NbrRtrIp"]: # if no neighbors have been detected
        return devices_list, {(devices_list[0]["HostId"],devices_list[0]["HostId"]): devices_list[0]["HostId"]}

    while len(set(unquerried_neighbors)) != len(set(querried_neighbors)):
        print('REMAINING: ',len(set(unquerried_neighbors))-1) # minus one because we have already polled the first router out of this loop
        all_nbr_ids = find_unqueried_neighbors(ip,comm,protocol)
        print('POLLED: ',len(set(querried_neighbors)))

    failed_neighbors = list(set(failed_neighbors))

    print('POLLING FAILED ON %d DEVICES'%len(failed_neighbors))

    final_devices_list = devices_list

    neighborship_dict = neighborship(final_devices_list)

    if protocol.lower() != 'ospf':
        neighborship_dict = ip_to_name(final_devices_list,neighborship_dict)

    return final_devices_list, neighborship_dict




def link_state(ip,comm,protocol):

    global devices_list, querried_neighbors

    devices_list = []
    querried_neighbors = []

    final_devices_list,neighborship_dict = build(ip,comm,protocol)

    if not final_devices_list:
        prompt = 'INFO: link_state.py via function link_state says:Could not poll the device. Confirm reachability and(or) community string'
        print(prompt)
        return [], []
    else:
        prompt='INFO: link_state.py via function link_state says: Loading of network completed'
        print(prompt)

    print('DEV LIST',final_devices_list)
    print('DEV DICT',neighborship_dict)

    return final_devices_list,neighborship_dict







class formatOut:


     def exportcsv(final_devices_list):
                
          csv_file = ("Hostname" + ";" + "RouterID" + ";" + "NeighborRouterID" + ";" + "NeighborIP" + ";" + "Interface")
          csv_file += ("\n")

          for each_dict in final_devices_list:
              csv_file += str(each_dict["Host"])  + ";"
              csv_file += str(each_dict["HostId"]) + ";" 
              csv_file += (', '.join(each_dict["NbrRtrId"])) + ";" 
              csv_file += (', '.join(each_dict["NbrRtrIp"])) + ";" 
              csv_file += (', '.join(each_dict["Interface"]))
              csv_file += ("\n")
          return csv_file



     def exportgefx(final_devices_list,neighborship_dict):

          G = nx.Graph()
          G.add_edges_from(neighborship_dict.keys())
          
          #loop through and add label for edges
          for edge in neighborship_dict.keys(): 
            G.edges[edge]['label'] = neighborship_dict[edge]

          nodes =id_to_name(final_devices_list)
  
          #loop through and add label attribute for nodes
          for node in nodes.keys(): 
            G.add_node(node)
            G.node[node]['label'] = nodes[node]
            
          s = '\n'.join([line for line in nx.generate_gexf(G)])

          return s



     def raw(final_devices_list,time_count):

        output = ''
        for each_dict in final_devices_list:
            output+=("Hostname: %s\n" % each_dict["Host"])
            output+=("RID: %s\n" % each_dict["HostId"])
            output+=("Neighbors by ID: %s\n" % ', '.join(each_dict["NbrRtrId"]))
            output+=("Neighbors by IP: %s\n" % ', '.join(each_dict["NbrRtrIp"]))
            output+=("Interraces: %s\n" % ', '.join(each_dict["Interface"]))
            output+=("\n")
            output+=("\n")
        output+=("Total number of devices: %d"%(len(final_devices_list)))
        output+=("\n")
        output+=("\n")
        
        return output


     def present_link_state(final_devices_list, neighborship_dict, export="text", time_count=0):

            choice = export.lower()

            if choice == 'text':
                return formatOut.raw(final_devices_list, time_count)
                 

            elif choice == 'csv':
                return formatOut.exportcsv(final_devices_list)

            elif choice == 'gefx':
                return formatOut.exportgefx(final_devices_list, neighborship_dict)
