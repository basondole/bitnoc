import json
import struct
import socket
import io
from jnpr.junos import Device
from lxml import etree
from string import Template

def connect_get_data(host, user, password, port=22):
  dev = Device(host=host, user=user, port=port, password=password)
  dev.open()
  dev.timeout = 60
  result = dev.rpc.get_isis_database_information(normalize=True, detail=True)
  dev.close()
  return result

def parse_result(result):
  graph={'nodes': [], 'links': []}
  for entry in result.xpath("isis-database[level='2']/isis-database-entry"):
    lspid = entry.findtext("lsp-id")
    node=lspid[:-3]
    if not node.endswith(".00"):
      node="_"+node;
    if not node in graph['nodes']:
      graph['nodes'].append(node)
    for neighbor in entry.xpath("isis-neighbor"):
      neighborid = neighbor.findtext("is-neighbor-id")
      metric = neighbor.findtext("metric")
      topology = neighbor.findtext("isis-topology-id")
      if not topology or topology=="IPV4 Unicast":
        if not neighborid.endswith(".00"):
          neighborid="_"+neighborid;
        if not neighborid in graph['nodes']:
          graph['nodes'].append(neighborid)
        graph['links'].append([node, neighborid, metric])
  return graph


def generate_data_sets(graph,result):
    # DEV DICT {('0.0.0.0.0.1', '0.0.16.99.99.99'): 'Fa0/0\n192.168.56.63', ('0.0.16.99.99.99', '0.0.0.0.0.1'): 'na\n10.10.1.36'}
    # graph['links'] LIST [['_TERACO-MX80.05', 'WTL-MSA-Telephone-BDR.00', '0'],['_TERACO-MX80.05', 'TERACO-MX80.00', '0']]
    #
    # DEV LIST [{'Host': 'big', 'HostId': '0.0.0.0.0.1', 'NbrRtrId': ['0.0.16.99.99.99'], 'NbrRtrIp': ['192.168.56.63'], 'Interface': ['na']}, {'Host': 'pycon-ios.local', 'HostId': '0.0.16.99.99.99', 'NbrRtrId': ['0.0.0.0.0.1'], 'NbrRtrIp': ['10.10.1.36', '192.168.56.36', '192.168.137.36'], 'Interface': ['Fa0/0', 'Fa0/1.100', 'Fa0/1.600']}]

    neighbourship_dict = {}
    for link in graph['links']:
        if link[0].startswith('_') or link[1].startswith('_'):
            continue
        neighbourship_dict.update({(link[0],link[1]):link[2]})
        # replaces ifnames with metric
    final_devices_list = []
    for entry in result.xpath("isis-database[level='2']/isis-database-entry"):
        lspid = entry.findtext("lsp-id")
        node=lspid[:-3]
        if not node.endswith(".00"):
          continue
        else:
            HostId = node
        NbrRtrId = []
        NbrMetric = []
        for neighbor in entry.xpath("isis-neighbor"):
          neighborid = neighbor.findtext("is-neighbor-id")
          metric = neighbor.findtext("metric")
          topology = neighbor.findtext("isis-topology-id")
          if not topology or topology=="IPV4 Unicast":
            # if not neighborid.endswith(".00"):
            #   continue
            NbrRtrId.append(neighborid)
            NbrMetric.append(metric)
        final_devices_list.append({'Host':HostId, 'HostId':HostId, 'NbrRtrId': list(set(NbrRtrId)), 'NbrRtrIp': ['' for  item in list(set(NbrRtrId))], 'Interface': NbrMetric})
    return final_devices_list, neighbourship_dict



def link_state_rpc_build(host, user, password):
    result = connect_get_data(host, user, password)
    graph = parse_result(result)
    return graph
