from windows.Settings import readsettings, savesettings
from windows.Devices import Devices, group_devices, raw, detail
from windows.Command import devices_to_list
from windows.Command import Command
from core.service_provision import provision_ipv4
from core.bgp_summary import cool_bgp_summary
from core.config_backup import config_backup
from core.link_state_snmp import formatOut
from core.link_state_snmp import link_state, id_to_name
from core.link_state_rpc import link_state_rpc_build
from core.locate_ip import locate_ip
from core.locate_name import locate_name
from core.locate_vlan import locate_vlan
from core.find_vlan_uno import find_vlan_uno
from core.find_vlan_duo import find_vlan_duo
from core.service_provision import CONFIGURE
from other.getDeviceData import verifyUser, Device, readfile, ip_to_name_as_key
from application.forms import UserRegistrationForm
from application.models import User, LogBook, log
from application import app, bcrypt, db
from flask import render_template, request, flash, redirect, url_for, session, jsonify, g
from flask_login import login_user, current_user, logout_user, login_required

import threading
import os
import ipaddress
import time
import pprint



@app.route("/register-user", methods=['GET', 'POST'])
def register_user():
	global settings

	if current_user.is_authenticated:
		return redirect(url_for('.index'))

	if type(settings) != dict :
				settings = readsettings()
				if type(settings) == str:
					data = {'settings': {},'devices': {}}
					flash(f'Settings missing. General settings are required for system to work.\
												   Please setup the system', 'danger')
					return render_template('home.html', showTab={'mainTab': 'settings'},
											data=data, user_id='default')

	form = UserRegistrationForm()
	if form.validate_on_submit():
		if verifyUser(form.username.data, form.password.data,
									server=settings['general-authentication-server']):
			hashed_passwd =  bcrypt.generate_password_hash(form.password.data).decode()
			user = User(username= form.username.data, email=form.email.data, password=hashed_passwd)
			db.session.add(user)
			db.session.commit()
			log(command='create: user-account', user_id=user.id)
			flash(f'Account created for <b>{form.username.data}</b>. \
					Please login', 'success')
			return redirect(url_for('.login'))
		else:
			flash(f'Credentials for user <b>{form.username.data}</b> \
					could not be verified by authentication server. \
					Confirm username and password', 'danger')
	return render_template('register.html', form = form)


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
	global settings, data, devinfo, devdata

	if current_user.is_authenticated:
		return redirect(url_for('.index'))

	if request.method == "GET":
		return render_template('login.html')

	elif request.method == "POST":

		session['password'] = request.form['pswrd']
		password = session['password']

		global context_output
		context_output[request.form['userid']] = {}

		session.pop(request.form['userid'], None) # drop existing session
		user = User.query.filter_by(username=request.form['userid']).first()

		if not user:
			flash(f'User {request.form["userid"]} does not exist', 'danger')
		elif bcrypt.check_password_hash(user.password, password):

			login_user(user, remember=False)

			if type(settings) != dict :
				settings = readsettings()
				if type(settings) == str:
					data = {'settings': {},'devices': {}}
					flash(f'Settings missing. General settings are required for system to work.\
												   Please setup the system', 'danger')
					return render_template('home.html', showTab={'mainTab': 'settings'},
											data=data, user_id=user.username)
			if not data['devices']:
				devices = Device(user.username, password, path=settings['general-database'])
				devinfo = devices.database()
				devdata = ip_to_name_as_key(devinfo)
				data = {
						'settings': settings,
						'devices': devdata,
						'device_refresh_time': device_refresh_time
						}
			print('\n====> Loaded devices | ip as key\n')
			pprint.pprint(devinfo)
			print('\n====> Loaded devices | hostname as key\n')
			pprint.pprint(devdata)
			print('\n====> data\n')
			pprint.pprint(data)
			next_page = request.args.get('next')
			log(command='login: web', user_id=user.id)
			return redirect(url_for('.index'))
		else:
			flash(f'Login failed. Please confirm the password', 'danger')
		return redirect(url_for('.login'))


@app.route('/logout')
@login_required
def logout():
	log(command='logout: web', user_id=current_user.id)
	logout_user()
	return redirect(url_for('.login'))


@app.route('/home', methods=['GET', 'POST'])
@login_required
def index():
	global  data
	return render_template('home.html', data=data, user_id=current_user.username)





@app.route("/save-settings", methods=['GET', 'POST'])
def save_settings():
	global data, showTab
	settings = dict(request.form)
	try:
		settings['api-netdot-url']
	except KeyError:
		settings['api-netdot-url'] = ''
	try:
		settings['api-orion-server']
	except KeyError:
		settings['api-orion-server'] = ''
	try:
		settings['api-orion-engine-id']
	except KeyError:
		settings['api-orion-engine-id'] = ''
	try:
		settings['api-oxidized']
	except KeyError:
		settings['api-oxidized'] = ''
	print('====> Updating settings')
	print(dict(settings))
	savesettings(dict(settings))

	data.update({'settings': settings})
	showTab='settings'
	if str(current_user) == 'None':
		log(command='update: settings', user_id=current_user.id)
	return redirect(url_for('.index', showTab=showTab))



@app.route("/devices/:remove-device", methods=['GET', 'POST'])
def remove_device():
	global data, devdata, devinfo

	device = request.form['hostname']
	ipaddr = data['devices'][device]['ip']

	path = data['settings']['general-database']
	devices = readfile(path=path) # dictionary of devices

	# find the logical systems and remove them by their hostnames with format hostname--logicalname
	if data['devices'][device]['logicalsystem']:
		for system in data['devices'][device]['logicalsystem'].keys():
			# pop the logical system by its name from the device dict
			hostname = device+'--'+system
			try:
				data['devices'].pop(hostname) # also affects devdata dictionary since data['devices'] = devdict
			except KeyError: # device is not synced thus the logical systems are not added to data['devices']
				continue
		for system in devinfo[ipaddr]['logicalsystem'].keys():
			# pop the logical system by its ip from the devinfo dict
			try:
				devinfo.pop(devinfo[ipaddr]['logicalsystem'][system]['ip'])
			except KeyError: # device is not synced thus the logical systems are not added to devinfo[ipaddr]['logicalsystem']
				continue
	data['devices'].pop(device)
	devinfo.pop(ipaddr)

	feedback = Devices.removeDevice(devices, ipaddr, path=path)

	if feedback == True:
		log(command=f'remove-device: {device}', user_id=current_user.id)
		info = {
				'status': 'success',
				'message': f'Device <b>{ device }</b> removed',
				'data': render_template('home.html',
										data=data,
										showTab={'mainTab':'devices','subTab':'remove'},
										alert={'status': 'success','message': f'Device <b>{ device }</b> removed'},
										user_id=current_user.username
										)
				}
	else:
		info = {
				'status': 'warning',
				'message': feedback,
				'data': False
				}

	return jsonify(info)


@app.route("/devices/:add-device", methods=['GET', 'POST'])
def add_device():
	global data, devdata, devinfo
	device_data = request.form
	taarifa = {}
	taarifa['software'] = device_data['software']
	taarifa['hostname'] = device_data['hostname']
	taarifa['ipv4'] = device_data['ipv4']
	taarifa['blocks'] = device_data['resident_block'].split(',')
	taarifa['systems'] = device_data['logical_system'].split(',')
	hostname = taarifa['hostname'].lower().replace(' ','_') # format hostname

	pprint.pprint(taarifa)
	path = data['settings']['general-database']
	ip_dict = readfile(path=path)

	if taarifa['ipv4'] in ip_dict.keys():
		info = {
				'status': 'danger',
				'message': f'Device <b>{ taarifa["hostname"] }</b> not added <b>{ taarifa["ipv4"] }</b> exists as <b>{ ip_dict[ taarifa["ipv4"] ]["hostname"] }</b>',
				'data': False
				}
		return jsonify(info)
	elif hostname in devdata.keys():
		info = {
				'status': 'danger',
				'message': f'Device <b>{ hostname }</b> exists with address <b>{ devdata[hostname]["ip"] }</b>',
				'data': False
				}
		return jsonify(info)

	feedback = Devices.addDevice(ip_dict, taarifa, path)

	if feedback == True:
		log(command=f'add-device: {hostname}', user_id=current_user.id)
		# return timeout as true to make the webpage run ajax function to collect all devices data
		info = {
				'status': 'dark',
				'message': f'Devices data is being refreshed',
				'data': True,
				'timeout': True
				}
		return jsonify(info)
	else:
		info = {
				'status': 'warning',
				'message': feedback,
				'data': False
				}

		return jsonify(info)


@app.route("/devices/:refresh-database/<refresh_ip>", methods=['GET', 'POST'])
def refresh_device_database(refresh_ip):
	global data, devdata, devinfo
	if not current_user.is_authenticated:
		info = {'status': 'danger',
				'message': f'User session timed out'}
		return jsonify(info)
	if type(data['settings']) != dict:
		info = {'status': 'danger',
				'message': f'Path to device database is not defined'}
		return jsonify(info)


	username = current_user.username
	password = session['password']
	if refresh_ip.lower() != 'all':
		print(f'INFO: app.py via function refresh_device_databas says: refreshing one device {refresh_ip}')
		devices_from_updated_file = Device(username,password,path=data['settings']['general-database']) # object for all the device dict including the added device
		all_devices = devices_from_updated_file.database()
		new_device = Device(username, password, dictdb={refresh_ip: all_devices[refresh_ip]})
		try:
			new_device_data = new_device.get_data() # dictionary with ip as key
			new_device_data[ refresh_ip ]['ip'] = refresh_ip
			devdata[new_device_data[ refresh_ip ]['hostname']] = new_device_data[ refresh_ip ]
			devinfo[ refresh_ip ] = new_device_data[ refresh_ip ]
			data['devices'] = devdata
			if devinfo[ refresh_ip ]['synced'] == False:
				raise Exception
			status = 'success'
			message = f'Device <b>{ devinfo[ refresh_ip ]["hostname"] }</b> data refreshed successfully'

		except:
			status = 'danger'
			message = f'Device <b>{ devinfo[ refresh_ip ]["hostname"] }</b> did not complete request. Confirm reachability or authentication'

		info = {
				'status': status,
				'message': message,
				'data': render_template('home.html',
										data=data,
										showTab={'mainTab':'devices','subTab':'table'},
										alert={'status': status,
											   'message': message},
										user_id=username)
				}
		log(command=f'refresh-device: {refresh_ip}', user_id=current_user.id)
		return jsonify(info)

	print(f'INFO: app.py via function refresh_device_databas says: refreshing all devices')
	process = threading.Thread( target=collectdevdata, args=(username, password,data['settings']) )
	process.start()
	process.join()

	data['devices'] = devdata

	info = {
			'status': 'dark',
			'message': f'All devices data refreshed successfully',
			'data': render_template('home.html',
									data=data,
									showTab={'mainTab':'devices'},
									alert={'status': 'success',
											'message': f'All devices data refreshed successfully'},
									user_id=username)
	}
	log(command=f'refresh-device: all', user_id=current_user.id)
	return jsonify(info)




@app.route("/vlanops/:find-one-vlan", methods=['GET', 'POST'])
@login_required
def vops_vlan_finder_uno():
	global data, devinfo
	username = current_user.username
	password = session['password']
	values = request.form

	print("\n\n===> Submitted values \n\n")
	pprint.pprint(values)

	global context_output
	random_id = os.urandom(8)
	context_output[username][random_id] = {}
	OUT = context_output[username][random_id]

	host = values['vlan-finder1-router']
	host = data['devices'][host]['ip']
	interface = values['vlan-finder1-interface']
	start = values['vlan-finder1-startvlan']
	end = values['vlan-finder1-endvlan']
	if not start or not end:
		search = 'list_all'
	else:
		search = values['vlan-finder1-searchtype']
	result = find_vlan_uno(username,password,host,devinfo,interface,OUT,
												 search=search,start=start,end=end)

	with open(f'application/templates/renders/{current_user.username}-text-output.html', 'w') as f:
		f.write(render_template('view-text-output.html', data = result))

	info = {
				'status': 'info',
				'message': 'Vlan info printed on new tab',
				'data': '/text-output'
	}
	log(command=f'find: one-vlan-id', user_id=current_user.id)
	return jsonify(info)



@app.route("/vlanops/:find-two-vlans", methods=['GET', 'POST'])
@login_required
def vops_vlan_finder_duo():
	global data, devinfo
	username = current_user.username
	password = session['password']
	values = request.form

	print("\n\n===> Submitted values \n\n")
	pprint.pprint(values)

	global context_output
	random_id = os.urandom(8)
	context_output[username][random_id] = {}
	OUT = context_output[username][random_id]


	host_a = values['vlans-finder-router1']
	host_a = data['devices'][host_a]['ip']
	if_a = values['vlans-finder-interface1']
	host_b = values['vlans-finder-router2']
	host_b = data['devices'][host_b]['ip']
	if_b = values['vlans-finder-interface2']
	start = values['vlan-finder2-startvlan']
	end = values['vlan-finder2-endvlan']
	if not start or not end:
		search = 'list_all'
	else:
		search = values['vlan-finder2-searchtype']

	result = find_vlan_duo(username, password, host_a, if_a, host_b, if_b, devinfo,
												 OUT, search=search, start=start, end=end)

	with open(f'application/templates/renders/{current_user.username}-text-output.html', 'w') as f:
		f.write(render_template('view-text-output.html', data = result))

	info = {
				'status': 'info',
				'message': 'Vlan info printed on new tab',
				'data': '/text-output'
	}
	log(command=f'find: two-vlan-id', user_id=current_user.id)
	return jsonify(info)



@app.route("/locate/:locate-item", methods=['GET', 'POST'])
@login_required
def locateops_locate_item():
	global data, devinfo
	username = current_user.username
	password = session['password']
	values = request.form
	lookup_type = values['lookup-type']
	lookup_value = values['locateops-locate-item']

	print("\n\n===> Submitted values \n\n")
	pprint.pprint(values)

	global context_output
	random_id = os.urandom(8)
	context_output[username][random_id] = {}
	OUT = context_output[username][random_id]

	if lookup_type == 'name' :
		result = locate_name(username, password, devinfo, lookup_value, OUT)
	elif lookup_type == 'vlan' :
		result = locate_vlan(username, password, devinfo, lookup_value, OUT)
	elif lookup_type == 'ipv4' :
		result = locate_ip(username, password, devinfo, lookup_value, OUT)

	with open(f'application/templates/renders/{current_user.username}-text-output.html', 'w') as f:
		f.write(render_template('view-text-output.html', data = result))

	info = {
				'status': 'info',
				'message': 'Results printed on new tab',
				'data': '/text-output'
	}
	log(command=f'locate: {lookup_type}', user_id=current_user.id)
	return jsonify(info)



@app.route("/:service-provision", methods=['GET', 'POST'])
@login_required
def service_provision():
	global data, devinfo
	username = current_user.username
	password = session['password']
	values = request.form

	global context_output
	random_id = os.urandom(8)
	context_output[username][random_id] = {}
	OUT = context_output[username][random_id]

	print("\n\n============== SUBMITTED FORM VLAUES ================\n\n")
	pprint.pprint(values)

	service_type = values['service-type'].lower()
	conf_data = {}
	netdotURL = data['settings']['api-netdot-url']
	orion_server = data['settings']['api-orion-server']
	engine_id = data['settings']['api-orion-engine-id']

	d = CONFIGURE(username, password, devinfo, OUT,
								netdotURL=netdotURL, orion_server=orion_server, engine_id=engine_id)

	host = data['devices'][values['provision-edge-router']]['ip']
	conf_data['PE'] = host
	try:
		logical_system = values['provision-logical-system']
	except KeyError:
		try:
			logical_system = data['devices'][values['provision-edge-router']]['systemname']
		except KeyError:
			logical_system = None
	conf_data['LS'] = logical_system
	bandwidth = values['provision-bandwidth']
	conf_data['BW'] = bandwidth
	interface = values['provision-interface']
	conf_data['IF'] = interface
	if values['provision-vlan-type'] == 'Auto':
		vlan = values['provision-auto-vlanid']
	elif values['provision-vlan-type'] == 'Manual':
		vlan = values['provision-manual-vlanid']
	conf_data['VL'] = vlan
	description = values['provision-description']
	conf_data['DS'] = description

	if service_type in ('internet', 'l3mpls'):
		conf_data['P4'] = values['provision-ipv4-input']
		conf_data['P6'] = values['provision-manual-ipv6']
		update_netdot = values['provision-update-netdot']
		conf_data['ND'] =  True if update_netdot == 'true' else False
		update_orion = values['provision-update-orion']
		conf_data['SO'] = True if update_orion == 'true' else False

		if service_type == 'l3mpls':
			vrf = values['provision-vrf']
			conf_data['VF'] = vrf
			result = d.l3mpls(devinfo, conf_data)

		elif service_type == 'internet':
			result = d.internet(devinfo, conf_data)


	elif service_type.lower() == 'l2mpls':
		host_2 = data['devices'][values['provision-edge-router-l2']]['ip']
		conf_data['PE2'] = host_2
		try:
			logical_system = values['provision-logical-system-l2']
		except KeyError:
			try:
				logical_system = data['devices'][values['provision-edge-router-l2']]['systemname']
			except KeyError:
				logical_system = None
		conf_data['LS2'] = logical_system
		bandwidth = values['provision-bandwidth-l2']
		conf_data['BW2'] = bandwidth
		interface = values['provision-interface-l2']
		conf_data['IF2'] = interface
		result = d.l2mpls(devinfo, conf_data)

	with open(f'application/templates/renders/{current_user.username}-text-output.html', 'w') as f:
		f.write(render_template('view-text-output.html', data = result['result']))

	info = {
				'status': result['prompt']['status'],
				'message': result['prompt']['message'],
				'data': '/text-output'
	}
	log(command=f'provision: {service_type}', user_id=current_user.id)
	return jsonify(info)



@app.route("/service-provision/:vlan-id", methods=['GET', 'POST'])
@login_required
def provision_vlan():
	global data, devinfo
	username = current_user.username
	password = session['password']
	values = request.form

	print("\n\n============== RECEIVED VALUES (AJAX) ================\n\n")
	pprint.pprint(dict(values))

	host = values['router']
	host = data['devices'][host]['ip']
	interface = values['interface']
	result = find_vlan_uno(username, password, host, devinfo, interface, context_output={})
	log(command=f'request: vlan-id', user_id=current_user.id)
	return jsonify(result)



@app.route("/service-provision/:vlan-ids", methods=['GET', 'POST'])
@login_required
def provision_vlans():
	global data, devinfo
	username = current_user.username
	password = session['password']
	values = request.form

	print("\n\n============== RECEIVED VALUES (AJAX) ================\n\n")
	pprint.pprint(dict(values))

	host_a = data['devices'][values['router_a']]['ip']
	intf_a = values['interface_a']
	host_b = data['devices'][values['router_b']]['ip']
	intf_b = values['interface_b']
	result = find_vlan_duo(username, password,host_a,intf_a, host_b,intf_b, devinfo,context_output={})
	log(command=f'request: vlan-ids', user_id=current_user.id)
	return jsonify(result)


@app.route("/service-provision/:ipv4", methods=['GET', 'POST'])
@login_required
def get_ipv4():
	global data, devinfo
	username = current_user.username
	password = session['password']
	values = request.form

	print("\n\n============== RECEIVED VALUES (AJAX) ================\n\n")
	pprint.pprint(dict(values))

	host = values['router']
	res_block = data['devices'][host]['residentblock']
	host = data['devices'][host]['ip']
	ipDict = devinfo
	netdotURL = data['settings']['api-netdot-url']
	result = provision_ipv4(username, password, devinfo, res_block, netdotURL)
	log(command=f'request: ipv4', user_id=current_user.id)
	return jsonify(result)



@app.route("/:command", methods=['GET', 'POST'])
@login_required
def command():
	global data, devinfo
	showTab = None
	username = current_user.username
	password = session['password']
	values = request.form

	print("\n\n============== SUBMITTED FORM VLAUES ================\n\n")
	pprint.pprint(values)

	global context_output
	random_id = os.urandom(8)
	context_output[username][random_id] = {}
	OUT = context_output[username][random_id]

	commands = values['command-command']
	if not commands.lower().startswith('link state'):
		devices = values['command-devices']
		if devices == 'devices [junos]':
			devices_list = devices_to_list(devinfo, 'junos')
		elif devices == 'devices [ios]':
			devices_list = devices_to_list(devinfo, 'ios')
		elif devices == 'devices [all]':
			devices_list  = list(devinfo.keys())
		elif devices.lower() in ('manual', 'upload file'):
			dev = values['command-device-manual']
			devices_list = [ d.strip() for d in dev.split(',') if d ]
		else:
			try:
				host_ip = str( ipaddress.ip_address(devices) )
				devices_list = [host_ip]
			except ValueError:
				host_ip = data['devices'][devices]['ip']
				devices_list = [host_ip]
	else:
		global final_devices_list, neighborship_dict, link_state_build_end_time

	if commands.lower() in ('upload file','manual'):
		commands_list = values['command-command-manual']
		commands_list = [ command.strip() for command in commands_list.split(',') if command ]
		d = Command(devinfo, username, password, commands_list, devices_list, OUT)
		result = d.execute()
		message = 'Command output printed on new tab'
		status = 'success'
		with open(f'application/templates/renders/{username}-text-output.html', 'w') as f:
			f.write(render_template('view-text-output.html', data = result))
		_data = '/text-output'

	elif commands.lower() == 'bgp summary':
		filtering = {}
		filtering['state'] = False if values['command-bgp-filter-state'] == 'true' else True
		filtering['arp'] = True if values['command-bgp-filter-arp'] == 'true' else False
		filtering['alias'] = True if values['command-bgp-filter-alias'] == 'true' else False
		filtering['loss'] = True if values['command-bgp-filter-loss'] == 'true' else False
		filtering['format'] = values['command-bgp-filter-format'].lower()

		_ipdict = {}
		for device in devices_list:
			try:
				if devinfo[device]['software']:
					_ipdict.update({device: devinfo[device]})
			except KeyError:
				continue #if device software is not known
		if not _ipdict:
			message = 'Device(s) not in database'
			status = 'warning'
			_data = False
		else:
			if filtering['format'] == 'ascii':
				result = cool_bgp_summary(_ipdict, username, password, OUT, filtering=filtering)
				with open(f'application/templates/renders/{username}-text-output.html', 'w') as f:
					f.write(render_template('view-text-output.html', data = result))
				_data = '/text-output'
			else:
				result = cool_bgp_summary(_ipdict, username, password, OUT, monitor=True,filtering=filtering)
				with open(f'application/templates/renders/{current_user.username}-bgp-summary-table-output.html', 'w') as f:
					f.write(render_template('html/bgp-neighbor-summary-table.html', data = result, filtering=filtering))
				_data = '/bgp-summary-table-output'
			if (type(result) == list and len(result.strip().split('\n')) <= 3) or (type(result) == dict and len(result) == 0):
				message = 'There was an error please check logs'
				status = 'danger'
			else:
				message = 'BGP summary info printed on new tab'
				status = 'info'





	elif commands.lower() == 'configuration backup':
		_ipdict = {}
		for device in devices_list:
			try:
				if devinfo[device]['software']:
					_ipdict.update({device: devinfo[device]['software']})
			except KeyError:
				continue #if device software is not known
		if not _ipdict:
			message = 'Device(s) not in database'
			status = 'warning'
			_data = False
		result = config_backup(username, password, _ipdict, OUT)
		message = 'Config summary printed on new tab'
		status = 'success'
		with open(f'application/templates/renders/{username}-text-output.html', 'w') as f:
			f.write(render_template('view-text-output.html',
															data = result['summary'],
															backup_conf_download = result['file_path'],
															user_id = username
															)
			)
		_data = '/text-output'

	elif commands.lower() == 'service audit':
		from core.get_intf_summary import get_intf_summary
		_ipdict = {}
		for device in devices_list:
			try:
				if devinfo[device]['software'] and not '--' in devinfo[device]['hostname']:
					_ipdict.update({device: devinfo[device]})
			except KeyError:
				continue #if device software is not known
		if not _ipdict:
			message = 'Device(s) not in database'
			status = 'warning'
			_data = False
		result = get_intf_summary(username, password, _ipdict, OUT)
		message = 'Service report printed on new tab'
		status = 'success'
		with open(f'application/templates/renders/{username}-audit-output.html', 'w') as f:
			f.write(render_template('view-service-audit.html',
															data = result['results'],
															errors = result['errors'],
															refresh_time = time.ctime()
															)
			)
		_data = '/service-audit-report'


	elif commands.lower() == 'link state by snmp':
		comm = values['command-link-state-community']
		name = values['command-link-state-device']
		ip = data['devices'][name]['ip']
		protocol = values['command-link-state-protocol']
		try:
			if neighborship_dict  and final_devices_list :
				print('INFO: test.py via function command says: link state data fetched from cache')
				message = 'Link state topology loaded from cache'
				status = 'info'
				_data = False
		except NameError:
			pass
		start_time = time.time()
		final_devices_list, neighborship_dict = link_state(ip,comm,protocol)
		id_name = id_to_name(final_devices_list)
		all_host_ids = {host_id for tuple_of_two_ids in neighborship_dict for host_id in tuple_of_two_ids}
		end_time = time.time()
		link_state_build_end_time = time.ctime()
		if final_devices_list and neighborship_dict:
			message = f'Link state topology build completed in {str(round(end_time - start_time,2))} seconds'
			status = 'success'
		else:
			message = 'Could not poll the device. Confirm reachability and(or) community string'
			status = 'danger'
		_data = render_template('home.html',
						data = data,
						showTab = showTab,
						alert = {'status': status, 'message': message},
						user_id = username)


	elif commands.lower() == 'link state by rpc':
		name = values['command-link-state-rpc-device']
		ip = data['devices'][name]['ip']
		protocol = values['command-link-state-rpc-protocol']
		start_time = time.time()
		graph_data = link_state_rpc_build(ip,username,password)
		graph_data = str(graph_data).replace("'",'"')
		with open(f'application/templates/renders/{current_user.username}-network-diagram.html', 'w') as f:
			f.write(render_template('view-network-diagram-full.html',graph=graph_data))

		end_time = time.time()
		if graph_data:
			message = f'Link state topology build completed in {str(round(end_time - start_time,2))} seconds'
			status = 'success'
		else:
			message = 'Could not poll the device. Confirm reachability and(or) community string'
			status = 'danger'
		_data = '/present-link-state-logical-view-full'

	info = {
			'status': status,
			'message': message,
			'data': _data
	}
	log(command=f'command: {commands}', user_id=current_user.id)
	return jsonify(info)


@app.route("/command/:refresh-bgp-monitor", methods=['GET', 'POST'])
def refresh_bgp_monitor():
	global devinfo
	username = current_user.username
	password = session['password']
	result = cool_bgp_summary(devinfo, username, password, context_output={}, monitor=True)
	data = render_template('html/bgp-neighbor-monitor-table.html', data=result)
	info = {'data': data}
	log(command=f'command: refresh-bgp-monitor', user_id=current_user.id)
	return jsonify(info)


@app.route("/bgp-monitor", methods=['GET', 'POST'])
@login_required
def bgp_monitor():
	global settings
	log(command=f'monitor: bgp', user_id=current_user.id)
	return render_template('view-bgp-neighbor-monitor.html',
												 timer=int(settings['bgp-neighbor-monitor-timer']))


@app.route("/command/:link-state-check-data", methods=['GET', 'POST'])
def check_link_state_data():
	global final_devices_list, neighborship_dict
	try:
		if final_devices_list and neighborship_dict:
			result = True
		else:
			result = False
	except NameError:
		result = False
	return jsonify(result)


@app.route("/command/:link-state-clear", methods=['GET', 'POST'])
def clear_link_state_data():
	global final_devices_list, neighborship_dict
	final_devices_list = []
	neighborship_dict = {}
	print('INFO: test.py via function clear_link_state_data says: link state data cleared')
	log(command=f'clear: link-state-db', user_id=current_user.id)
	return jsonify("")


@app.route("/command/:link-state-present/<presentation>", methods=['GET', 'POST'])
@login_required
def present_link_state_data(presentation):
	global neighborship_dict, final_devices_list
	print('INFO: test.py via function present_link_state_data says: link state data fetched from cache')
	if presentation.lower() == 'text':
		result = '/present-link-state-txt'
	elif presentation.lower() == 'csv':
		result = formatOut.present_link_state(final_devices_list, neighborship_dict, export="csv")
	elif presentation.lower() == 'gefx':
		result = formatOut.present_link_state(final_devices_list, neighborship_dict, export="gefx")
	elif presentation.lower() == 'diagram':
		result = '/present-link-state-logical-view'
	log(command=f'view: link-state-{presentation}', user_id=current_user.id)
	return jsonify(result)



@app.route("/present-link-state-txt", methods=['GET', 'POST'])
def present(prompt=None):
	global neighborship_dict, final_devices_list, link_state_build_end_time
	result = f'Refreshed: {link_state_build_end_time}\n\n'
	result += formatOut.present_link_state(final_devices_list, neighborship_dict)
	log(command=f'view: link-state-text', user_id=current_user.id)
	return render_template('view-text-output.html', data = result, prompt=prompt)


@app.route("/present-link-state-logical-view")
def logical_view():
	global neighborship_dict, final_devices_list
	device_list = final_devices_list
	device_dict = neighborship_dict
	all_host_ids = {host_id for tuple_of_two_ids in neighborship_dict for host_id in tuple_of_two_ids}
	from core.link_state_snmp import link_state, id_to_name
	polled_node_labels = id_to_name(device_list)
	all_node_labels = {}
	for host_id in all_host_ids:
		try:
			all_node_labels[host_id] = polled_node_labels[host_id]
		except KeyError:
			all_node_labels[host_id] = host_id
	rasimu = render_template('json/rasimu.json', device_list=all_node_labels, device_dict=device_dict)
	with open('application/static/miserables.json', 'w') as f:
		f.write(rasimu)
	log(command=f'view: link-state-diagram-snmp', user_id=current_user.id)
	return render_template('view-network-diagram.html')


@app.route("/present-link-state-logical-view-full")
def logical_full_view():
	return render_template(f'renders/{current_user.username}-network-diagram.html')

@app.route("/bgp-summary-table-output", methods=['GET', 'POST'])
def present_bgp_table_output():
	if not current_user.is_authenticated:
		redirect(url_for('.login'))
	return render_template(f'renders/{current_user.username}-bgp-summary-table-output.html')

@app.route("/text-output", methods=['GET', 'POST'])
def present_text_output():
	if not current_user.is_authenticated:
		redirect(url_for('.login'))
	return render_template(f'renders/{current_user.username}-text-output.html')


@app.route("/service-audit-report", methods=['GET', 'POST'])
def service_audit_report():
	if not current_user.is_authenticated:
		redirect(url_for('.login'))
	return render_template(f'renders/{current_user.username}-audit-output.html')



@app.route("/download/backup-config")
def download_config_backup (path = None):
	from flask import send_file
	if current_user.is_authenticated:
		username = current_user.username
		path = os.path.abspath(f'{username}_config_backup.zip')
		log(command=f'download: config-backup', user_id=current_user.id)
		return send_file(path)
	else:
		return redirect(url_for('.login'))

@app.route("/delete/backup-config", methods=['GET', 'POST'])
@login_required
def delete_config_backup (path = None):
	username = current_user.username
	if os.path.exists(f'{username}_config_backup.zip'):
		os.remove(f'{username}_config_backup.zip')
	return 'Generated zip deleted from the server'



@app.template_filter('toyaml')
def toyaml(d, indent=2, result=''):
	for key, value in d.items():
		result += " "*indent + str(key)
		if isinstance(value, dict):
			result = toyaml(value, indent+2, f'{result}:\n')
		elif isinstance(value, list):
			result += ": \n"
			for item in value:
				result += " "*(indent+2) + f'- {item}\n'
		else:
			result += f": {str(value)} \n"
	result += "\n"
	return result

app.jinja_env.filters['raw_view'] = raw
app.jinja_env.filters['summary_view'] = group_devices
app.jinja_env.filters['detail_view'] = detail




def collectdevdata(username,password,path):
	global devinfo, devdata, data

	print(f'{time.ctime()} INFO: app.py via function collectdevdata says: Loading of data from all devices started')
	devices = Device(username,password,path=path['general-database'])
	devinfo = devices.get_data() # ip is the key in this dict

	devlist = list(devinfo.keys())
	devdata = {} # hostname is the key in this dict
	for dev in devlist:
		name = devinfo[dev]['hostname']
		devdata[name] = {}
		for value in devinfo[dev].keys():
			if value != 'napalm': # skip the napalm drive as it causes error with jinja2
				devdata[name][value] = devinfo[dev][value]
			devdata[name]['ip'] = dev

	data['device_refresh_time'] = time.ctime()

	print(f'{time.ctime()} INFO: app.py via function collectdevdata says: Loading of data from all devices completed')
	return






if __name__ == "__main__":
	settings = readsettings()
	device_refresh_time = ''
	data = {'settings': {},'devices': {}}
	context_output = {}
	app.run(debug=True, port=5000)
