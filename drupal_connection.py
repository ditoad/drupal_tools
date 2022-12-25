from drupal_browser import browser
from drupal_configuration import DC
from drupal_logger import log
# from os.path import isfile, expanduser
# import configparser
import getpass



class DrupalConnection():
	"This class logs into the drupal instance. For the credentials, please create the ~/.drupal/credentials.ini file with a [default] section and username, password, basic_authentication_username and basic_authentication_password for logging into Drupal and a potential Basic Authentication."


	def __init__(
		self, 
		url: str = '',
		username: str = '', 
		password: str = '', 
		basic_authentication_username: str = '', 
		basic_authentication_password: str = '', 
		):
		self._url: str = url
		self._username: str = username
		self._password: str = password
		self._basic_authentication_username: str = basic_authentication_username
		self._basic_authentication_password: str = basic_authentication_password
		self._login()
		self._base_url: str = DC.get('server.proto') + self._url + DC.get('server.default_language_uri_prefix')

	def get_server_base_url(self):
		return self._base_url


	def load_node_edit_url(self, nodeID: str = None) -> bool:
		if(not nodeID):
			log.fatal(f"[DrupalConnection.load_node_edit_url()] Callimg attribute withoug nodeID not possible")
		if(type(nodeID) != str):
			nodeID = str(nodeID)
		return browser.load_url(self._base_url + DC.get('server.node_edit_prefix') + nodeID + DC.get('server.node_edit_postfix'))


	def load_node_translation_url(self, nodeID: str = None) -> bool:
		if(not nodeID):
			log.fatal(f"[DrupalConnection.load_node_translation_url()] Calling attribute withoug nodeID not possible")
		if(type(nodeID) != str):
			nodeID = str(nodeID)
		return browser.load_url(self._base_url + DC.get('server.node_edit_prefix') + nodeID + DC.get('server.node_translations_postfix'))


	def load_media_edit_url(self, nodeID: str = None) -> bool:
		if(not nodeID):
			log.fatal(f"[DrupalConnection.load_media_edit_url()] Calling attribute withoug nodeID not possible")
		if(type(nodeID) != str):
			nodeID = str(nodeID)
		return browser.load_url(self._base_url + DC.get('server.media_edit_prefix') + nodeID + DC.get('server.media_edit_postfix'))


	def load_media_translation_url(self, nodeID: str = None):
		if(not nodeID):
			log.fatal(f"[DrupalConnection.load_media_translation_url()] Calling attribute withoug nodeID not possible")
		if(type(nodeID) != str):
			nodeID = str(nodeID)
		return browser.load_url(self._base_url + DC.get('server.media_edit_prefix') + nodeID + DC.get('server.media_translations_postfix'))


	def _login(self):
		if(not self._url and browser.ini_data['url']):
			self._url = browser.ini_data['url']
		elif(not self._url and 'url' in DC.get('server')):
			self._url = DC.get('server.url')
		if(not self._username):
			self._find_username()
		if(not self._password):
			self._find_password()
		if(not self._basic_authentication_username):
			self._find_basic_authentication_username()		
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
		if('basic_authentication_username' in browser.ini_data):
			self._basic_authentication_username = browser.ini_data['basic_authentication_username']
		if(not self._basic_authentication_username):
			return
		if(not self._basic_authentication_password and 'basic_authentication_password' in browser.ini_data):
			self._basic_authentication_password = browser.ini_data['basic_authentication_password']
		if(not self._basic_authentication_password):
			self._basic_authentication_password = self._get_interactive_password(f"Enter basic authentication password for user '{self._basic_authentication_username}'")


	def _find_username(self):
		if('username' in browser.ini_data):
			self._username = browser.ini_data['username']
		if(not self._username and DC):
			self._username = DC.get('server.username')
		if(not self._username):
			log.fatal(f"[DrupalConnection._find_username()] failed to find a drupal username. It was not passed and is not present in either a DrupalConfig or an ini file", 3)


	def _find_password(self):
		if('password' in browser.ini_data):
			self._password = browser.ini_data['password']
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



DConn = DrupalConnection()
