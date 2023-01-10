from drupal_logger import log
from drupal_browser import browser
from drupal_configuration import *
from drupal_connection import DConn
import re

TRUE_STRINGS = ["1", "t", "y", "true", "True", "TRUE", "yes", "Yes", "YES", "on", "On", "ON", "active", "Active", "ACTIVE", "published", "Published", "PUBLISHED"]
FALSE_STRINGS = ["0", "2", "f", "n", "false", "False", "FALSE", "no", "No", "NO", "off", "Off", "OFF", "inactive", "Inactive", "INACTIVE", "unpublished", "Unpublished", "UNPUBLISHED"]

class DrupalDashboard():
	"Functional super class of drupal dashboard that needs to get implemented by concrete dashboard classes. All centralizable functions are implemented in here. Only dashboard specific methods remain with their dashboard classes or get overwritten by them"


	def __init__(self, dashboard_key: str, filters: dict = None):
		"The init method can't be called with pagination page, since we don't even know yet if there are any pages."
		self._dashboard_key: str = dashboard_key
		self._filters: dict = filters
		self._baseurl = DConn.get_server_base_url()
		self._baseurl = self._baseurl + DC.get(self._dashboard_key + '.uri')
		self._view
		self._reset()
		if(self._filters):
			self.set_filters()
		else:
			self.load()
		# We always load the first page (0). If there is more than one page, we already have the number of rows per page. And if not, it is the only page and we already know the total number of rows for the current filter settings
		self._rows_per_page = self._row_count_on_current_page
		# if we only have one page, we already know the total row count
		if(self._max_pages == 0):
			self._row_count_total = self._row_count_on_current_page


	def _reset(self):
		"This attribute declares and resets the remaining class attributes"
		self._max_pages: int = -1
		self._page: int = 0
		self._pagination_url_parameter: str = ''
		self._pagination_url_postfix: str = ''
		self._parameters: str = ''
		self._row_count_on_current_page: int = 0
		self._row_count_total: int = -1
		self._row_elements_on_page = []
		self._node_ids_on_page = []
		self._row_edit_links_on_page = []
		self._rows_per_page = 0
		self._url: str = ''


	def get_first_node_id_on_page(self):
		if(len(self._node_ids_on_page) > 0):
			return self._node_ids_on_page[0]
		else:
			return
		

	def get_max_pages(self):
		if(self._max_pages >= 0):
			return self._max_pages
		log.fatal(f"[DrupalDashboard.get_max_pages()] Pagination hasn't been analyzed yet. Can't return a valid value for `self._max_pages`.")


	def get_node_ids_on_page(self):
		return self._node_ids_on_page


	def get_page(self):
		return self._page


	def get_current_page_row_count(self):
		return self._row_count_on_current_page


	def get_row_count_total(self) -> int:
		if(self._row_count_total >= 0):
			return self._row_count_total
		# if we have multiple pages, we have to check on the last page and jump back
		current_page = self._page
		self.load_page(page = self._max_pages)
		last_page_count = self._row_count_on_current_page
		log.debug(f"[DrupalDashboard.get_row_count_total()] Found {last_page_count} rows on the last page and a total of {self._max_pages} with {self._rows_per_page} except the last one")
		self._row_count_total = self._max_pages * self._rows_per_page + last_page_count
		# self.load_page(current_page)
		return self._row_count_total


	def get_rows_per_page(self):
		return self._rows_per_page


	def load(self):
		"This attribute initializes a freshly loaded dashboard with its + current filters"
		self._url: str = ''
		self._row_count_on_current_page: int = 0
		self._row_elements_on_page = []
		self._set_pagination()
		self._assemble_url()
		log.debug(f"[DrupalDashboard.load()] Loading {self._dashboard_key} from {self._url}")
		browser.load_url(url = self._url, lang = DC.get('server.default_language'), view = self._view)
		self._count_rows_on_current_page()
		if(self._max_pages == -1):
			self._get_max_pages()


	def load_page(self, page: int = 0):
		"This attribute method loads a pagination page, if the dashboard has been loaded and the pagination page exists."
		log.debug(f"[DrupalDashboard.load_page()] Trying to load pagination page {page} of {self._max_pages} pages")
		if(page <= self._max_pages):
			self._page = page
			self.load()
		elif(page > self._max_pages):
			log.fatal(f"[DrupalDashboard.load_page()] Attempted to load a page out of bounds. Attempted page was {page} and there are only {self._max_pages} pages available")
		else:
			log.fatal(f"[DrupalDashboard.load_page()] Attempted to load the dashboard on page {page} without previously loading the dashboard with the current filter set.")


	def read_row_edit_links(self):
		"This attribute iterates over each row element on the page, tries to find the edit link of the row, stores it and then extracts the node IDs and appends them to the node id array self._node_ids_on_page"
		self._row_edit_links_on_page = []
		self._node_ids_on_page = []
		for row in self._row_elements_on_page:
			node_id = ''
			href = ''
			try:
				href = browser.get_value_of_attribute(element = row, key = self._dashboard_key + '.row_edit_links')
			except Exception as e:
				log.fatal(f"[DrupalDashboard.read_row_edit_links()] Couldn't find edit link in row {row.get_attribute('outerHTML')}")
			log.debug(f"Found row with href='{href}'")
			self._row_edit_links_on_page.append(href)
			log.debug(f"Trying the regexp '{self._dashboard_key + '.row_edit_links.manual_regexp'}'")
			matches = re.search(DC.get(self._dashboard_key + '.row_edit_links.manual_regexp'), href)
			if(matches):
				node_id = int(matches.group(1))
				self._node_ids_on_page.append(node_id)
				log.debug(f"-> Found Edit link: '{href}' with ID {node_id}")
			else:
				log.fatal(f"[DrupalDashboard.read_row_edit_links()] Couldn't find a node ID in edit link '{href}' with regexp '{DC.get(self._dashboard_key + '.row_edit_links.manual_regexp')}'")


	def set_filters(self, filters: dict = None):
		self._reset()
		if(filters):
			self._filters = filters
		if(not self._filters):
			log.debug("[set_filters] self._filters not set. No filters present. Returning without further action.")
			return
		for key in DC.get(self._dashboard_key + '.filters').keys():
			param: str = ''
			log.debug(f"[DrupalDashboard.set_filters()] Looking into filter key '{key}'")
			if(key in self._filters):
				param = self._get_parameter_for_filter(key, self._filters[key])
			elif(DC.get(self._dashboard_key + '.filters.' + key + '.show_unselected')):
				param = DC.get(self._dashboard_key + '.filters.' + key + '.name') + '='+ DC.get(self._dashboard_key + '.filters.' + key + '.default')
			if(not param):
				continue
			if(self._parameters):
				self._parameters += '&'
			self._parameters += param
		log.debug(f"[DrupalDashboard.set_filters()] Found url-parameters '{self._parameters}'")
		# every time we set filters, we have to set the pagination as well, because it might have gotten over written by the parameters. And then the URL has to be (re-) assembled as well.
		self.load()


	def _assemble_url(self):
		"(Re-) assembles the url of the dashboard."
		self._url: str = self._baseurl + self._pagination_url_postfix
		if(self._parameters):
			self._url += '?' + self._parameters
			if(self._pagination_url_parameter):
				self._url += '&' + self._pagination_url_parameter
		elif(self._pagination_url_parameter):
			self._url += '?' + self._pagination_url_parameter


	def _count_rows_on_current_page(self):
		self._row_elements_on_page = browser._find_elements(key = self._dashboard_key + ".row_count")[0]
		self._row_count_on_current_page = len(self._row_elements_on_page)
		log.debug(f"[DrupalDashboard._count_rows_on_current_page()] Found a total of {self._row_count_on_current_page} rows on page {self._page}")


	def _get_max_pages(self):
		href = browser.get_value_of_attribute(key = self._dashboard_key + ".pagination.last_page")
		# if we don't find the configured element, we'll receive an empty string, which indicates, that we don't have a pagination at all. 
		if(not href):
			self._max_pages = 0
			log.debug(f"[DrupalDashboard._get_max_pages()] No href found for  {self._max_pages} -> found in href='{href}'")
			return
		self._max_pages = self._get_pagination_from_url(href)
		log.debug(f"[DrupalDashboard._get_max_pages()] Max pages {self._max_pages} -> found in href='{href}'")


	def _get_pagination_from_url(self, url) -> int:
		"this agttribute takes an url and tries to extract the pagination count based on the configuration for pagination in the specified dashboard"
		page:int = 0
		if(DC.get(self._dashboard_key + '.pagination.type') == "url-postfix"):
			matches = re.search("^.*\/(\d+)", url)
			if(matches):
				page = int(matches.group(1))
		elif(DC.get(self._dashboard_key + '.pagination.type') == "url-parameter"):
			matches = re.search(f"^.*\?.*{DC.get(self._dashboard_key + '.pagination.name')}=(\d+)", url)
			if(matches):
				page = int(matches.group(1))
		else:
			log.fatal(f"[DrupalDashboard._get_pagination_from_url()] There is a configuration error in the key '{self._dashboard_key + '.pagination.type'}'. This type is not allowed")
		log.debug(f"[DrupalDashboard._get_pagination_from_url()] Found pagination page={page} in url='{url}'")
		return page


	def _get_parameter_for_filter(self, filter, value) -> str:
		param: str = ''
		key = DC.get(self._dashboard_key + '.filters.' + filter + '.name')
		data_type: str = DC.get(self._dashboard_key + '.filters.' + filter + '.type')
		log.debug(f"[DrupalDashboard._get_parameter_for_filter()] Filter='{filter}' -> key='{key}', data type='{data_type}' and passed value='{value}'")
		value_list = []
		if(type(value) is list):
			value_list = value
		else:
			value_list.append(value)
		if(len(value_list) > 1):
			key += "%5B%5D"
		for val in value_list:
			value = ''
			if(data_type == "string"):
				value = browser.url_encode_string(val)
				# param = key + '=' + browser.url_encode_string(value)
			elif(data_type == "language"):
				if(not val in DC.get('server.languages')):
					log.fatal(f"[DrupalDashboard._get_parameter_for_filter()] Couldn't find language '{val}' in drupal configuration. Valid languages are '{DC.get('server.languages')}'")
				value = val
			elif(data_type == "content_type"):
				if(not val in DC.get('server.content_types')):
					log.fatal(f"[DrupalDashboard._get_parameter_for_filter()] Couldn't find content 	type '{val}' in drupal configuration. Valid content_types are '{DC.get('	server.content_types')}'")
				value = val
			elif(data_type == "moderation_status"):
				if(val in DC.get('server.moderation_status').keys()):
					value = DC.get('server.moderation_status.' + val)
				else:
					log.fatal(f"[DrupalDashboard._get_parameter_for_filter()] Couldn't find moderation 	state '{val}' in drupal configuration. Valid moderation states are {DC.get('server.moderation_status').keys()}")
			elif(data_type == "num_bool"):
				# for some odd reason, someone decided to define "unpublished" as 2
				if(type(val) == bool):
					if(val):
						value = '1'
					else:
						value = '2'
				elif(type(val) == int):
					if(val == 1):
						value = '1'
					elif(val == 0 or val == 2):
						value = '2'
					else:
						log.fatal(f"[DrupalDashboard._get_parameter_for_filter()] num_bool values passed integers must be in the following list (0=false, 1=true, 2=false). The passed value is '{val}'.")

				elif(type(val) == str):
					if(val in TRUE_STRINGS):
						value = '1'
					elif(val in FALSE_STRINGS):
						value = '2'
					else:
						log.fatal(f"[DrupalDashboard._get_parameter_for_filter()] num_bool values must be 	passed as booleans, integers (0=false, 1=true) or strings ({TRUE_STRINGS}, {FALSE_STRINGS}). The passed value '{val}' is invalid.")
				else:
					log.fatal(f"[DrupalDashboard._get_parameter_for_filter()] num_bool values must be 	passed as booleans, integers (0=false, 1=true) or strings (TRUE_STRINGS, 	FALSE_STRINGS). The passed value '{val}' is invalid.")

			elif(data_type == "media_type"):
				if(not val in DC.get('server.media_types')):
					log.fatal(f"[DrupalDashboard._get_parameter_for_filter()] Value for filter 'media_type'='{val} is not in the allowed list of '{DC.get('server.media_types')}'.")
				value = val
			elif(data_type == "legal_date_limit"):
				if(not val in DC.get('server.legal_date_limits').keys()):
					log.fatal(f"[DrupalDashboard._get_parameter_for_filter()] Value for filter 'legal_date_limit'='{val}' is not in the allowed list of '{DC.get('server.legal_date_limits').keys()}'.")
				value = str(DC.get('server.legal_date_limits.' + val))
			elif(data_type == "media_language"):
				if(not val in DC.get('server.media_languages').keys()):
					log.fatal(f"[DrupalDashboard._get_parameter_for_filter()] Value for filter 'media_language'='{val} is not in the allowed list of '{DC.get('server.media_languages').keys()}'.")
				value = str(DC.get('server.media_languages.' + val))
			if(param):
				param += "&"
			param += key + '=' + value
		log.debug(f"[DrupalDashboard._get_parameter_for_filter()] Extracted filter '{filter}' parameter='{param}'")
		return param


	def _set_pagination(self):
		"This method sets the pagination as url-extension or url-parameter depending on the dashboard's configuration"
		self._pagination_url_postfix = ''
		self._pagination_url_parameter = ''
		if(not DC.get(self._dashboard_key + '.pagination.parametrize_first_page') and self._page == 0):
			return
		if(DC.get(self._dashboard_key + '.pagination.type') == "url-postfix"):
			self._pagination_url_postfix = '/' + str(self._page)
			log.debug(f"[DrupalDashboard._set_pagination()] Setting pagination up as url postfix {self._pagination_url_postfix}")
		elif(DC.get(self._dashboard_key + '.pagination.type') == "url-parameter"):
			param = DC.get(self._dashboard_key + '.pagination.name') + '=' + str(self._page)
			log.debug(f"[DrupalDashboard._set_pagination()] Setting pagination up as url parameter {param}")
			self._pagination_url_parameter = param
		else:
			log.fatal(f"[DrupalDashboard._set_pagination()] Couldn't find a valid pagination type for '{self._dashboard_key}'")
		return



class ContentDashboard(DrupalDashboard):
	"Implementation of the content dashboard based on the super class DrupalDashboard. Content dashboard specific methods are implemented or overwritten here."
	def __init__(self, filters: dict = None):
		self._view = 'dashboard_content_overview'
		super().__init__(dashboard_key = 'dashboards.content_dashboard', filters = filters)


	# def load(self):
	# 	super().load()
		# super()._read_row_node_ids()



class FilesDashboard(DrupalDashboard):
	"Implementation of the content dashboard based on the super class DrupalDashboard. Content dashboard specific methods are implemented or overwritten here."
	def __init__(self, filters: dict = None):
		self._view = 'dashboard_files'
		super().__init__(dashboard_key = 'dashboards.files_dashboard', filters = filters)



class MediaDashboard(DrupalDashboard):
	"Implementation of the content dashboard based on the super class DrupalDashboard. Content dashboard specific methods are implemented or overwritten here."
	def __init__(self, filters: dict = None):
		self._view = 'dashboard_media'
		super().__init__(dashboard_key = 'dashboards.media_dashboard', filters = filters)


	# def load(self):
	# 	super().load()
		# super().read_row_edit_links()



class ProductDashboard(DrupalDashboard):
	"Implementation of the product dashboard based on the super class DrupalDashboard. Product dashboard specific methods are implemented or overwritten here."
	def __init__(self, filters: dict = None):
		self._view = 'dashboard_products'
		super().__init__(dashboard_key = 'dashboards.product_dashboard', filters = filters)


	# def load(self):
	# 	super().load()
		# super().read_row_edit_links()
