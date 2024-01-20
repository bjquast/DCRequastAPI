import pudb

from dwb_authentication.DWB_Servers import DWB_Servers
from dwb_authentication.security import SecurityPolicy

class UserLogin():
	def __init__(self, request):
		self.request = request
		
		self.uid = None
		self.roles = []
		self.users_projects = []
		self.users_project_ids = []
		
		self.missing_params = []
		self.messages = []
		



	def get_login_params(self):
		self.missing_params = []
		
		username = self.request.POST.get('username', '')
		password = self.request.POST.get('password', '')
		
		db_accronym = self.request.POST.get('db_accronym', '')
		
		loginparams = {}
		
		loginparams = {
			'username': username,
			'password': password,
			'db_accronym': db_accronym,
		}
		
		for key in loginparams:
			if loginparams[key] is None or loginparams[key] == '':
				self.missing_params.append(key)
				if key == 'db_accronym':
					self.messages.append('Login is not possible, please select database')
				else:
					self.messages.append('Login is not possible, please enter {0}'.format(key))
		
		if len(self.missing_params) > 0:
			loginparams = {}
		
		else:
			# check password against haveibeenpawned to check if it is a 'well known' password
			secure_password = self.password_not_pawned(password)
			if secure_password is False:
				loginparams = {}
				
		return loginparams


	'''
	check against https://haveibeenpwned.com disallow pawned passwords
	code from:
	https://pwcheck.gwdg.de/api.html
	with usage of haveibeenpwned.com API
	https://haveibeenpwned.com/API/v2#SearchingPwnedPasswordsByRange
	'''
	def password_not_pawned(self, password):
		
		import hashlib, urllib.request
		
		pwhash = hashlib.sha1(password.encode('utf8')).hexdigest().upper()
		prefix = pwhash[:5]
		suffix = pwhash[5:]
		
		unknown_password = False
		
		url = "https://api.pwnedpasswords.com/range/" + prefix
		with urllib.request.urlopen(url) as response:
			unknown_password = True
			for line in response.read().splitlines():
				line = line.decode('ASCII')
				if line.startswith(suffix):
					self.messages.append('Your password is insecure. Please change the password immediately')
					return False
		
		return unknown_password


	def authenticate_user(self):
		loginparams = self.get_login_params()
		if len(loginparams) < 3:
			return None
		
		dwb_servers = DWB_Servers()
		server = dwb_servers.get_dwb_con_by_accronym(loginparams['db_accronym'])
		
		security = SecurityPolicy()
		token = security.validate_credentials(server = server['server'], port = server['port'], database = server['database'], driver = server['driver'], username = loginparams['username'], password = loginparams['password'])
		
		if token is not None:
			self.request.session['token'] = token
			
			self.uid = self.request.authenticated_userid
			self.roles = self.request.identity['dwb_roles']
			self.users_projects = self.request.identity['projects']
			self.users_project_ids = [project[0] for project in self.users_projects]
		
		else:
			self.messages.append('Login failed, please check your credentials')
		
		#headers = remember(self.request, login)
		return token


	def log_out_user(self):
		security = SecurityPolicy()
		security.de_authenticate(self.request)
		self.request.session['token'] = None
		
		self.uid = self.request.authenticated_userid
		self.roles = self.request.identity['dwb_roles']
		self.users_projects = self.request.identity['projects']
		self.users_project_ids = [project[0] for project in self.users_projects]
		
		return


	def get_messages(self):
		return self.messages


	def get_identity(self):
		return self.uid, self.roles, self.users_projects, self.users_project_ids
