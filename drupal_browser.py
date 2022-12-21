from drupal_logger import log
from drupal_configuration import DrupalConfig, DC
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
import urllib.parse

class Browser():
	"The Browser class represents a class that loads pages via its get() attribute and that can retrieve values from elements and set values in elements"


	def __init__(self):
		self._url_home = DC.get('server.proto') + DC.get('server.url') + DC.get('server.default_language_uri_prefix')
		self._url = ''
		self._languages = DC.get('server.languages')
		options = Options();
		for option in DC.get('selenium.options'):
			options.add_argument(option)
		self._browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)


	def load_url(self, url: str):
		"Method that retrieves an URL in the browser"
		try:
			self._browser.get(url)
		except Exception as e:
			log.error(f"[drupal_browser.load_url()] Error while trying to load URL '{url}': {e}")
		self._url = url


	def get_url(self) -> str:
		return self._url


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
		if(strict and len(elements) > 1):
			log.error(f"[drupal_browser.get_element()] Found {len(elements)} elements for key '{key}' and element {element}")
		return elements[0]


	def get_elements(self, element = None, key: str = ''):
		elements = []
		interaction: str = ''
		elements, interaction = self._find_elements(element = element, key = key)
		return elements


	def get_value_of_attribute(self, element = None, key: str = '', attr: str = '') -> str:
		if(element and key == ''):
			try:
				return element.get_attribute(attr)
			except Exception as e:
				log.error(f"[drupal_browser.get_value_of_attribute()] Element '{element.get_attribute('outerHTML')}' doesn't have a {attr} attribute.")
		elem = self._find_element(element = element, key = key)
		if(elem == None):
			return
		try:
			return elem.get_attribute(attr)
		except Exception as e:
			log.error(f"[drupal_browser.get_value_of_attribute()] Element {element.get_attribute('outerHTML')} for key '{key}' doesn't have a {attr} attribute.")


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
			log.error(f"[drupal_browser._get_find_element_by_method()] Couldn't find 'method' attribute in key '{key}'")
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


	def close(self):
		self._browser.close()

browser = Browser()
