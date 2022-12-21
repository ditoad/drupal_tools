from   drupal_browser       import browser
from   drupal_configuration import DC
from   drupal_logger        import log
from   os.path              import isfile, expanduser
import configparser
import getpass

DEFAULT_CREDENTIALS_DIRECTORY:str = "~/.drupal"
DEFAULT_CREDENTIALS_FILENAME:str = "credentials.ini"
DEFAULT_CREDENTIALS_GROUP:str = "default"

class DrupalConnection():
	"This class logs into the drupal instance. For the credentials, please create the ~/.drupal/credentials.ini file with a [default] section and username, password, basic_authentication_username and basic_authentication_password for logging into Drupal and a potential Basic Authentication."


	def __init__(
		self, 
		username: str = '', 
		password: str = '', 
		basic_authentication_username: str = '', 
		basic_authentication_password: str = '', 
		credentials_file: str = DEFAULT_CREDENTIALS_DIRECTORY + '/' + DEFAULT_CREDENTIALS_FILENAME, 
		credentials_group: str = DEFAULT_CREDENTIALS_GROUP
		):
		self._username: str = username
		self._password: str = password
		self._basic_authentication_username: str = basic_authentication_username
		self._basic_authentication_password: str = basic_authentication_password
		self._url: str = ''
		self._ini_url: str = ''
		self._ini_username: str = ''
		self._ini_password: str = ''
		self._ini_basic_authentication_username: str = ''
		self._ini_basic_authentication_password: str = ''
		self._credentials_file:str = credentials_file
		self._credentials_group:str = credentials_group
		self._login()


	def _login(self):
		self._read_credentials_file()
		if(not self._basic_authentication_username):
			self._find_basic_authentication_username()		
		if(not self._username):
			self._find_username()
		if(not self._password):
			self._find_password()
		if(not self._ini_url):
			self._url = DC.get('server.url')
		else:
			self._url = self._ini_url
		login_url_prefix = ''
		if(self._basic_authentication_username):
			login_url_prefix = self._basic_authentication_username + ':' + self._basic_authentication_password + '@'
		login_url = DC.get('server.proto') + login_url_prefix + self._url + DC.get('server.default_language_uri_prefix') + DC.get('server.login_uri')
		log.debug(f"[DrupalConnection._login()] Trying to login at server URL: {login_url}")
		browser.load_url(login_url)
		browser.interact(key = "login.username", value = self._username)
		browser.interact(key = "login.password", value = self._password)
		browser.interact(key = "login.submit")
		if(browser.has_element(key = "login.username")):
			log.fatal(f"[DrupalConnection._login()] Login into Drupal for user {self._username} failed. Wrong username and/or password. Aborting")
		log.info(f"[DrupalConnection._login()] Logged into Drupal server at {login_url}")


	def _find_basic_authentication_username(self):
		self._basic_authentication_username = self._ini_basic_authentication_username
		if(not self._basic_authentication_username):
			return
		if(not self._basic_authentication_password):
			self._basic_authentication_password = self._ini_basic_authentication_password
		if(not self._basic_authentication_password):
			self._basic_authentication_password = self._get_interactive_password(f"Enter basic authentication password for user '{self._basic_authentication_username}'")


	def _find_username(self):
		self._username = self._ini_username
		if(not self._username and JC):
			self._username = DC.get('server.username')
		if(not self._username):
			log.fatal(f"[DrupalConnection._find_username()] ailed to find a drupal username. It was not passed and is not present in either a DrupalConfig or an ini file", 3)


	def _find_password(self):
		self._password = self._ini_password
		if(not self._password):
			log.info(f"[DrupalConnection._find_password()] No password passed or found in ini file for user '{self._username}' to connect to Jira server '{self._server_url}'")
			self._password = self._get_interactive_password(f"Please enter a passwor for drupal user '{self._username}'")


	def _get_interactive_password(self, prompt: str = "Enter Password:"):
		password = None
		while(True):
			try:
				password = getpass.getpass(prompt)
				if(not password):
					continue
				return password
			except:
				log.error("[DrupalConnection._get_interactive_password()] Error during entry of password.")


	def _read_credentials_file(self):
		self._credentials_file = expanduser(self._credentials_file)
		if(not isfile(self._credentials_file)):
			log.debug(f"[DrupalConnection._read_credentials_file()] Couldn't find credentials file '{self._credentials_file}'")
			self._credentials_file = expanduser("~/" + DEFAULT_CREDENTIALS_FILENAME)
		else:
			log.debug(f"[DrupalConnection._read_credentials_file()] Found credential file '{self._credentials_file}'")			
		if(not isfile(self._credentials_file)):
			self._credentials_file = "./" + DEFAULT_CREDENTIALS_FILENAME
		if(not isfile(self._credentials_file)):
			self._credentials_file = None
			log.debug("[DrupalConnection._read_credentials_file()] Couldn't find a credential file")
			return
		config = configparser.ConfigParser()
		try:
			config.read(self._credentials_file)
			log.info(f"[DrupalConnection._read_credentials_file()] Read credential file '{self._credentials_file}'")
		except:
			log.fatal(f"[DrupalConnection._read_credentials_file()] Failed to read credentials file '{self._credentials_file}' despite its existance.", 1)
		log.debug(f"[DrupalConnection._read_credentials_file()] Trying to read credential file section '{self._credentials_group}'")		
		try:
			self._ini_url   = config.get(self._credentials_group, 'url')
			log.debug(f"[DrupalConnection._read_credentials_file()] Read url={self._ini_url} attribute from credential file section '{self._credentials_group}'")
		except:
			log.debug(f"[DrupalConnection._read_credentials_file()] No 'url' attribute in credential file section '{self._credentials_group}'")
		try:
			self._ini_username   = config.get(self._credentials_group, 'username')
			log.debug(f"[DrupalConnection._read_credentials_file()] Read username={self._ini_username} attribute from credential file section '{self._credentials_group}'")
		except:
			log.debug(f"[DrupalConnection._read_credentials_file()] No 'username' attribute in credential file section '{self._credentials_group}'")
		try:
			self._ini_password   = config.get(self._credentials_group, 'password')
			log.debug(f"[DrupalConnection._read_credentials_file()] Read password=******** attribute from credential file section '{self._credentials_group}'")
		except:
			log.debug(f"[DrupalConnection._read_credentials_file()] No 'password' attribute in credential file section '{self._credentials_group}'")
		try:
			self._ini_basic_authentication_username = config.get(self._credentials_group, 'basic_authentication_username')
			log.debug(f"[DrupalConnection._read_credentials_file()] Read basic_authentication_username={self._ini_basic_authentication_username} attribute from credential file section '{self._credentials_group}'")
		except:
			log.debug(f"[DrupalConnection._read_credentials_file()] No 'basic_authentication_username' attribute in credential file section '{self._credentials_group}'")
		try:
			self._ini_basic_authentication_password = config.get(self._credentials_group, 'basic_authentication_password')
			log.debug(f"[DrupalConnection._read_credentials_file()] Read basic_authentication_password={self._ini_basic_authentication_password} attribute from credential file section '{self._credentials_group}'")
		except:
			log.debug(f"[DrupalConnection._read_credentials_file()] No 'basic_authentication_password' attribute in credential file section '{self._credentials_group}'")


DConn = DrupalConnection()
