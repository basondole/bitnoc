
import threading
import datetime
import time
import paramiko
import re
import sys
import os
import zipfile
from napalm import (junos,
					ios)



def config_backup(username,password,db, context_output):

	try:
		if not os.path.exists(f'{username}_config_backup'):
			os.makedirs(f'{username}_config_backup')
	except:
		print(f'{time.ctime()} INFO: config_backup.py via function config_backup says: You do not have permission to create a folder in this directory')
		return False

	result = doit(username,password,db,context_output)

	return result



def getconf(ip,username,password,_db,failed,data,lock,context_output):
	print(_db)
	if _db[ip] == 'junos':
		dev = junos.JunOSDriver(ip, username, password)
	elif _db[ip] == 'ios':
		dev = ios.IOSDriver(ip, username, password)

	try:
		dev.open()
		print(f'{time.ctime()} INFO: config_backup.py via function getconf says: opened napalm session {ip}')
		try:
			facts = dev.get_facts()
			print(f'{time.ctime()} INFO: config_backup.py via function getconf says: collected facts via napalm {ip}')
		except Exception as e:
			print(f'{time.ctime()} INFO: config_backup.py via function getconf says: {type(e)} {e} for {ip}')
		config = dev.get_config()
		dev.close()
	except Exception as e:
		print(f'{time.ctime()} INFO: config_backup.py via function getconf says: napalm exception {type(e)} {e} {ip}')
		failed.append({ip:[_db[ip],e]})
		return

	try:
		facts
	except:
		print(f'{time.ctime()} INFO: config_backup.py via function getconf says: getting facts via paramiko {ip}')
		if _db[ip] == 'junos':
			sshClient = paramiko.SSHClient()
			sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			try:
				sshClient.connect(ip, username=username, password=password,
								timeout=10,allow_agent=False,look_for_keys=False)
				secureCli = sshClient.invoke_shell()
				secureCli.send('set cli screen-length 0\n')
				secureCli.send('set cli screen-width 0\n')
				time.sleep(5)
				secureCli.recv(65535)
				secureCli.send('\n')
				time.sleep(.5)
				sshClient.close()
				hostname = secureCli.recv(65535).decode()
				facts = {}
				facts['hostname'] = hostname.strip().split('@')[1].split('>')[0]

				facts['vendor'] = 'Juniper'
				facts['model'] = '-'
				facts['serial_number'] = '-'
				facts['os_version'] = '-'
				facts['uptime'] = '-'

			except Exception as _:
				print(f'{time.ctime()} INFO: config_backup.py via function getconf says: failed to get facts via paramiko {_} {ip}')
				failed.append({ip:[_db[ip],_]})
				return


	conf_exist = True


	if not config['running'].strip():

		if _db[ip] == 'junos': # for junos ['os_version'] < 11
			try:
				sshClient = paramiko.SSHClient()
				sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
				sshClient.connect(ip, username=username, password=password,
								timeout=10,allow_agent=False,look_for_keys=False)
				secureCli = sshClient.invoke_shell()
				secureCli.send('set cli screen-length 0\n')
				secureCli.send('set cli screen-width 0\n')
				time.sleep(5)
				secureCli.recv(65535)
				secureCli.send('show configuration\n')
				time.sleep(30)
				sshClient.close()

				console_output = ''

				while True:
					try: cli_output = secureCli.recv(65535).decode()
					except:
						failed.append({ip:[_db[ip],'BROKEN CONFIG']})
						return
					if not cli_output: break
					for line in cli_output:
						console_output+=str(line)

				conf = console_output.split('\n')
				conf.pop(0)
				conf.pop(-1)
				config = {'startup':'','running':'','candidate':''}
				config['running'] = ''.join(conf)

			except:
				conf_exist = False


	if not config['startup'].strip() and not config['running'].strip() and not config['candidate'].strip():
		failed.append({ip:[_db[ip],'NO CONF']})
		conf_exist = False


	if conf_exist:
		with lock:
			print(f'{time.ctime()} INFO: config_backup.py via function getconf says: Completed collecting config from {ip.ljust(15)} [{facts["hostname"]}]')

			data[facts['hostname']] = {'ip':ip,
									   'vendor':facts['vendor'],
									   'model':facts['model'],
									   'serial':facts['serial_number'],
									   'software':facts['os_version'],
									   'uptime':facts['uptime']}

			if _db[ip] == 'ios':
				_remove = re.search(r'\((\S+)\)',data[facts['hostname']]['software']).group(0)
				_vers = data[facts['hostname']]['software'].replace(_remove,'').replace('Version','')
				data[facts['hostname']]['software'] = _vers.replace('  ','')[:_vers.rfind(',')].replace(',','')

		saa = datetime.datetime.now().isoformat().replace(':','-')[:-10]
		with open(f'{username}_config_backup/{ip}_{facts["hostname"]}_{saa}','w') as _:
			for line in config['running'].split('\n'):
				try: _.write('%s\n'%line)
				except Exception as e:
					with lock:
						print('\n')
						print('INFO: config_backup.py via function getconf says:')
						print('  %s [%s]\n%s'%(ip,facts['hostname'],e))
						print('  Found a line that has a non standard unicode character (non printable)')
						print('  The offending character will be replaced by a character code instead')
						print('  -%s' %line)
						print('  +%s' %line.encode('unicode-escape').decode('utf-8'))
						print('\n')
					_.write('%s\n' %line.encode('unicode-escape').decode('utf-8'))



def doit(username,password,_db,context_output):

	data = {}
	failed = []

	anza = time.time()
	msg = ''

	threads = []
	lock = threading.Lock()

	for ip in _db:
		t = threading.Thread(target=getconf, args=(ip,username,password,_db,failed,data,lock,context_output))
		t.start()
		threads.append(t)

	for t in threads: t.join()

	context_output['_failed_con_'] = []
	context_output['_failed_conf_'] = []

	for item in failed:
		# item is a dict
		key = list(item.keys())[0]
		value = item[key]

		if value[1]=='NO CONF':
			context_output['_failed_conf_'].append(item)
		elif value[1]=='BROKEN CONFIG':
			context_output['_failed_conf_'].append(item)
		else:
			context_output['_failed_con_'].append(item)

	if context_output['_failed_con_']:
		msg+= '<span style="color: #ff5656;""> FAILED CONNECTIONS'
		msg+= '\n'
		msg+=(' +-----+----------------------+%s+'%('-'*101))
		msg+= '\n'
		msg+=(' | %s| %s| %s|'%('No'.ljust(4),'DEVICE IP'.ljust(21),'ERROR'.ljust(100)))
		msg+= '\n'
		msg+=(' +-----+----------------------+%s+'%('-'*101))

		dev_no = 1
		for device in context_output['_failed_con_']:
			for ip,error in device.items():
				msg+=('\n')
				msg+=(' | %s| %s| %s|'%(str(dev_no).ljust(4),ip.ljust(21),str(error).ljust(100)))
				msg+= '\n'
				msg+=(' +-----+----------------------+%s+'%('-'*101))
				dev_no+=1
		msg+= '</span>\n\n'


	if context_output['_failed_conf_']:
		msg+= '<span class="token function"> FAILED CONFIG ACQUISITION'
		msg+= '\n'
		msg+=(' +-----+----------------------+%s+'%('-'*101))
		msg+= '\n'
		msg+=(' | %s| %s| %s|'%('No'.ljust(4),'DEVICE IP'.ljust(21),'ERROR'.ljust(100)))
		msg+= '\n'
		msg+=(' +-----+----------------------+%s+'%('-'*101))

		dev_no = 1
		for device in context_output['_failed_conf_']:
			for ip,error in device.items():
				msg+=('\n')
				msg+=(' | %s| %s| %s|'%(str(dev_no).ljust(4),ip.ljust(21),str(error).ljust(100)))
				msg+= '\n'
				msg+=(' +-----+----------------------+%s+'%('-'*101))
				dev_no+=1
		msg += '</span>\n\n'


	if (len(_db)-len(failed)) > 0:

		msg+= '<span style="color: #56ffa5;"> COMPLETED'
		msg+= '\n'
		msg+=(' +----------------------+-----------------')
		msg+=('+------------+-----------------')
		msg+=('+---------------+-----------------------------')
		msg+=('+------------+')
		msg+=('\n')
		msg+=(' | %s| %s'%('HOSTNAME'.ljust(21),'DEVICE IP'.ljust(16)))
		msg+=('| %s| %s'%('VENDOR'.ljust(11),'MODEL'.ljust(16)))
		msg+=('| %s| %s'%('SERIAL'.ljust(14),'SOFTWARE'.ljust(28)[:28]))
		msg+=('| %s|'%('UPTIME (s)'.ljust(11)))
		msg+=('\n')
		msg+=(' +----------------------+-----------------')
		msg+=('+------------+-----------------')
		msg+=('+---------------+-----------------------------')
		msg+=('+------------+')

		for device in sorted(data.keys()):

			msg+=('\n')
			msg+=(' | %s| %s'%(device.ljust(21),data[device]['ip'].ljust(16)))
			msg+=('| %s| %s'%(data[device]['vendor'].ljust(11),data[device]['model'].ljust(16)))
			msg+=('| %s| %s'%(data[device]['serial'].ljust(14),data[device]['software'].ljust(28)[:28]))
			msg+=('| %s|'%(str(data[device]['uptime']).ljust(11)))
			msg+=('\n')
			msg+=(' +----------------------+-----------------')
			msg+=('+------------+-----------------')
			msg+=('+---------------+-----------------------------')
			msg+=('+------------+')

		msg += '</span>'

	result = 'Collected config files: %d/%d'%((len(_db)-len(failed)),len(_db))

	msg+='\n'
	msg+='\n'
	msg+= ' SUMMARY'
	msg+= '\n'
	msg+= ' -------'
	msg+= '\n'
	msg+= ' Failed connections: %d'%len(context_output['_failed_con_'])
	msg+= '\n'
	msg+= " {}\n\n {}".format(result,'[Finished in %ds] ' %(time.time() - anza))

	def zipdir(path, ziph):
		# ziph is zipfile handle
		for root, dirs, files in os.walk(path):
			for file in files:
				ziph.write(os.path.join(root, file))

	zipf = zipfile.ZipFile(f'{username}_config_backup.zip', 'w', zipfile.ZIP_DEFLATED)
	zipdir(f'{username}_config_backup/', zipf)
	zipf.close()

	# delete the directory and its contents
	import shutil
	shutil.rmtree(f'{username}_config_backup') 

	return {'summary': msg, 'file_path': os.path.abspath(f'{username}_config_backup.zip')}