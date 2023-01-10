from drupal_configuration import DrupalConfig, DC
from drupal_logger import log
from os.path import isfile, expanduser, join
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager 
import configparser
import os.path
import re
import urllib.parse
DEFAULT_CREDENTIALS_DIRECTORY:str = "~/.drupal"
DEFAULT_CREDENTIALS_FILENAME:str = "credentials.ini"
DEFAULT_CREDENTIALS_GROUP:str = "default"



class Browser():
	"The Browser class represents a class that loads pages via its get() attribute and that can retrieve values from elements and set values in elements"


	def __init__(self, credentials_file:str = expanduser(os.path.join(DEFAULT_CREDENTIALS_DIRECTORY, DEFAULT_CREDENTIALS_FILENAME)), credentials_group: str = DEFAULT_CREDENTIALS_GROUP):
		self._credentials_file = credentials_file
		self._credentials_group = credentials_group
		self._language: str = None
		# as defined in DC.get('server.views') []
		self._view: str = None
		self._url = ''
		self.ini_data = {}
		self._read_credentials_file()
		options = Options();
		for option in DC.get('selenium.options'):
			options.add_argument(option)
		self._browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)


	def load_url(self, url: str, view: str, lang: str):
		"Method that retrieves an URL in the browser"
		if(not view in DC.get('server.views')):
			log.fatal(f"[Browser.load_url] The passed view '{view}' is not in the configured views '{DC.get('server.views')}'")
		if(not lang in DC.get('server.languages')):
			log.fatal(f"[Browser.load_url] The passed language '{lang}' is not in the configured views '{DC.get('server.languages').keys()}'")
		self._url = url
		self._view = view
		self._language = lang
		try:
			log.debug(f"[Browser.load_url()] Trying to load url {self._url}.")
			self._browser.get(self._url)
		except Exception as e:
			log.error(f"[drupal_browser.load_url()] Error while trying to load URL '{self._url}': {e}")
			return False
		return True

	def get_language(self) -> str:
		return self._language


	def get_url(self) -> str:
		return self._url


	def get_view(self) -> str:
		return self._view


	def url_encode_string(self, string: str = '') -> str:
		return urllib.parse.quote_plus(string, safe=';/?:@&=+$,')


	def interact(self, key: str = None, value: str = None):
		"interact() is an attribute that finds a single element or elements (i.e. a bunch of checkboxes or radio buttons) and interacts (clicks or enters values) as specified in the defining drupal.config.json file."
		elements = []
		interaction: str = ''
		elements, interaction = self._find_elements(key = key)
		for element in elements:
			try:
				if(interaction == "send_keys"):
					element.send_keys(value)
				elif(interaction == "click"):
					element.click()
			except Exception as e:
				log.fatal(f"[drupal_browser.interact()] Error @url\n{self._url}\nwhile trying to interact with element '{element}' with DOM \n>---\n{element.get_attribute('outerHTML')}'\n>---\nError:\n>---\n{e}\n>---\n")


	def get_element_count(self, element = None, key: str = '') -> int:
		elements = []
		interaction: str = ''
		elements, interaction = self._find_elements(element = element, key = key)
		return len(elements)


	def get_element(self, element = None, key: str = '', strict: bool = False):
		elements = self.get_elements(element = element, key = key)
		if(not elements):
			return None
		if(strict and len(elements) > 1):
			log.error(f"[drupal_browser.get_element()] Strictly one element is enforced. But found {len(elements)} elements for key '{key}' in element. Returning first element for the method='{DC.get(key + '.method')}' and value='{DC.get(key + '.value')}' from with in the element: \n---\n{element}\n---")
		return elements[0]


	def get_elements(self, element = None, key: str = ''):
		elements = []
		interaction: str = ''
		elements, interaction = self._find_elements(element = element, key = key)
		return elements


	def get_value_of_attribute(self, element = None, key: str = '', attr: str = '') -> str:
		if(element and key == ''):
			try:
				print(f"Here with {element}")
				return element.get_attribute(attr)
			except Exception as e:
				log.error(f"[drupal_browser.get_value_of_attribute()] Element '{element.get_attribute('outerHTML')}' doesn't have a {attr} attribute. Error: '{e}'")
		elem = self._find_element(element = element, key = key)
		return_value: str = ''
		if(elem == None):
			return None
		if(not attr and 'attribute' in DC.get(key)):
			attr = DC.get(key + '.attribute')
		try:
			if(attr == "text"):
				return_value = elem.text
			else:
				return_value = elem.get_attribute(attr)
		except Exception as e:
			log.info(f"[drupal_browser.get_value_of_attribute()] Key '{key}' doesn't have a '{attr}' attribute in element '{elem.get_attribute('outerHTML')}'.")
			return ''
		if(not 'regexp' in DC.get(key)):
			return return_value
		matches = re.search(DC.get(key + '.regexp'), return_value)
		if(matches):
			return matches.group(1)
		else:
			log.info(f"[Browser.get_value_of_attribute()] Couldn't find regexp '{DC.get(key + '.regexp')}'in '{return_value}'")
			return return_value



	def has_element(self, element = None, key: str = '') -> bool:
		if(self.get_element_count(element = element, key = key) > 0):
			return True
		return False


	def has_elements(self, element = None, key: str = '') -> bool:
		if(self.get_element_count(element = element, key = key) > 1):
			return True
		return False


	def _find_element(self, element = None, key: str = '') -> str:
		"Tries to find exactly one element for a given key with the specified methods. Otherwise throws errors and returns nothing."
		elements = []
		interaction: str = ''
		elements, interaction = self._find_elements(element = element, key = key)
		if(len(elements) == 0):
			log.info(f"[drupal_browser._find_element()] Didn't find any elements for key '{key}' with method '{DC.get(key + '.method')}' and value '{DC.get(key + '.value')}'")
			return
		elif(len(elements) > 1):
			log.error(f"[drupal_browser._find_element()] Found more than 1 element for key '{key}' with method '{DC.get(key + '.method')}' and value '{DC.get(key + '.value')}'")
			return
		return elements[0]


	def _get_find_element_by_method(self, key: str = None):
		"This attribute returns the "
		if(not DC.get(key + '.method')):
			log.error(f"[drupal_browser._get_find_element_by_method()] Couldn't find 'method' attribute in key '{key}'. Available keys are {DC.get(key).keys()}")
			return
		if(DC.get(key + '.method') == "By.CLASS_NAME"):
			method = By.CLASS_NAME
		elif(DC.get(key + '.method') == "By.CSS_SELECTOR"):
			method = By.CSS_SELECTOR
		elif(DC.get(key + '.method') == "By.ID"):
			method = By.ID
		elif(DC.get(key + '.method') == "By.LINK_TEXT"):
			method = By.LINK_TEXT
		elif(DC.get(key + '.method') == "By.NAME"):
			method = By.NAME
		elif(DC.get(key + '.method') == "By.PARTIAL_LINK_TEXT"):
			method = By.PARTIAL_LINK_TEXT
		elif(DC.get(key + '.method') == "By.TAG_NAME"):
			method = By.TAG_NAME
		elif(DC.get(key + '.method') == "By.XPATH"):
			method = By.XPATH
		else:
			log.error(f"[drupal_browser._get_find_element_by_method()] Couldn't identify 'method' attribute in key '{key}'")
			return
		return method


	def _find_elements(self, element = None, key: str = ''):
		"attriute that returns an array of elements with one or multiple elements as well as the configured interaction. This method is applied recursively"
		elements = []
		interaction: str = ''
		method = self._get_find_element_by_method(key = key)
		log.debug(f"[Browser._find_elements()] Trying to find elements with method '{method}' for start key '{DC.get(key + '.value')}'")
		try:
			if(not element):
				elements = self._browser.find_elements(method, DC.get(key + '.value'))
			else:
				elements = element.find_elements(method, DC.get(key + '.value'))
		except Exception as e:
			log.error(f"[drupal_browser._find_elements()] Trying to find elements in key '{key}' with method '{method}' and value '{DC.get(key + '.value')}' led to the following exception: {e}")
			return [], ''
		if(len(elements) == 0):
			log.debug(f"[Browser._find_elements()] Didn't find any elements")
			return [], ''
		if(DC.get(key + '.index') != None):
			copy = []
			copy.append(elements[DC.get(key + '.index')])
			elements = copy
			copy = None
		# now that we got the elements, we have to check if we need to recurse
		if(DC.get(key + ".interaction")):
			log.debug(f"[Browser._find_elements()] Found a total of {len(elements)} elements with interaction.")
			return elements, DC.get(key + '.interaction')
		# This is the section, where we have to go into recursion
		elif(DC.get(key + '.find_elements')):
			elements_copy = elements
			elements = []
			for elem in elements_copy:
				log.debug(f"[Browser._find_elements()] Recursing with key '{DC.get(key + '.find_elements.value')}'.")
				recursive_elements, interaction = self._find_elements(element = elem, key = key + '.find_elements')
				elements.extend(recursive_elements)
			
			return elements, interaction
		# this is the case for 
		else:
			log.debug(f"[Browser._find_elements()] Found a total of {len(elements)} elements.")
			return elements, ''


	def _read_credentials_file(self):
		"This attribute reads the credentials.ini file and "
		if(not isfile(self._credentials_file)):
			log.debug(f"[Browser._read_credentials_file()] Couldn't find credentials file '{self._credentials_file}'")
			self._credentials_file = expanduser(os.path.join("~", DEFAULT_CREDENTIALS_FILENAME))
		else:
			log.debug(f"[Browser._read_credentials_file()] Found credential file '{self._credentials_file}'")			
		if(not isfile(self._credentials_file)):
			self._credentials_file =  os.path.join(".", DEFAULT_CREDENTIALS_FILENAME)
		if(not isfile(self._credentials_file)):
			log.debug("[Browser._read_credentials_file()] Couldn't find a credential file")
			return
		config = configparser.ConfigParser()
		try:
			config.read(self._credentials_file)
			log.info(f"[Browser._read_credentials_file()] Read credential file '{self._credentials_file}'")
		except:
			log.fatal(f"[Browser._read_credentials_file()] Failed to read credentials file '{self._credentials_file}' despite its existence.", 1)
		log.debug(f"[Browser._read_credentials_file()] Trying to read credential file section '{self._credentials_file}'")		
		try:
			self.ini_data['url'] = config.get(self._credentials_group, 'url')
			log.debug(f"[Browser._read_credentials_file()] Read url={self.ini_data['url']} attribute from credential file section '{self._credentials_group}'")
		except:
			log.debug(f"[Browser._read_credentials_file()] No 'url' attribute in credential file section '{self._credentials_group}'")
		try:
			self.ini_data['username'] = config.get(self._credentials_group, 'username')
			log.debug(f"[Browser._read_credentials_file()] Read username={self.ini_data['username']} attribute from credential file section '{self._credentials_group}'")
		except:
			log.debug(f"[Browser._read_credentials_file()] No 'username' attribute in credential file section '{self._credentials_group}'")
		try:
			self.ini_data['password'] = config.get(self._credentials_group, 'password')
			log.debug(f"[Browser._read_credentials_file()] Read password=******** attribute from credential file section '{self._credentials_group}'")
		except:
			log.debug(f"[Browser._read_credentials_file()] No 'password' attribute in credential file section '{self._credentials_group}'")
		try:
			self.ini_data['basic_authentication_username'] = config.get(self._credentials_group, 'basic_authentication_username')
			log.debug(f"[Browser._read_credentials_file()] Read basic_authentication_username={self.ini_data['basic_authentication_username']} attribute from credential file section '{self._credentials_group}'")
		except:
			log.debug(f"[Browser._read_credentials_file()] No 'basic_authentication_username' attribute in credential file section '{self._credentials_group}'")
		try:
			self.ini_data['basic_authentication_password'] = config.get(self._credentials_group, 'basic_authentication_password')
			log.debug(f"[Browser._read_credentials_file()] Read basic_authentication_password={self.ini_data['basic_authentication_password']} attribute from credential file section '{self._credentials_group}'")
		except:
			log.debug(f"[Browser._read_credentials_file()] No 'basic_authentication_password' attribute in credential file section '{self._credentials_group}'")



	def close(self):
		self._browser.close()

browser = Browser()
