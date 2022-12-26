from datetime import datetime
from drupal_logger import log
from drupal_browser import browser
from drupal_configuration import *
from drupal_connection import DConn
from selenium.webdriver.support.select import Select
import re
import pprint



class DrupalNode():
	"This is a super class that provides mutual attributes across normal nodes and media nodes. Content type specific attributes have to be implemented in inheriting classes."

	def __init__(self, nodeID: str, isMedia: bool = False):
		self._nodeID: str = nodeID
		self.isMedia: bool = isMedia
		self.meta: dict = {
			"node_type": "",
			"language": "",
			"last_saved": "",
			"author": "",
			"moderation_status": "",
			"description": ""
		}
		self.content: dict = {}
		self.translations: dict = {
			"by_language": {
				"status": {},
				"title": {}
			},
			"by_status":{}
		}
		if(not self.isMedia):
			self._read_node_meta_data()
			self._read_node_content()
			self._read_node_translations()
			DConn.load_node_edit_url(nodeID = self._nodeID)
		else:
			self._read_media_meta_data()
			# self._read_media_content()
			if(self.meta['node_type'] in [
				'document', 
				'embedded_video', 
				'image', 
				'pim_document', 
				'pim_image', 
				'pim_proof_of_performance', 
				'press_image',
				'private_document',
				'private_image'
				]
				):
				self._read_node_translations()


		# pprint.pprint(self.meta)
		# print("----------------------------")
		# pprint.pprint(self.content)
		# print("----------------------------")
		# pprint.pprint(self.translations)


	def _read_node_meta_data(self):
		"reads the node url in edit mode and extracts all meta data from the side bar"
		matches = None
		DConn.load_node_edit_url(nodeID = self._nodeID)
		# getting the sidebar with meta data
		sidebar = browser.get_element(key = 'nodes.meta_data.existence', strict = True)
		if(not sidebar):
			log.fatal(f"[DrupalNode._read_node_meta_data()] The node with ID {self._nodeID} doesn't have a meta data side bar.")
		self.meta['node_type'] = browser.get_value_of_attribute(key = 'server.content_type_body_class_attribute')
		matches = re.search(DC.get('server.content_type_body_classes_regexp'), self.meta['node_type'])
		if(matches):
			self.meta['node_type'] = matches.group(1)
		else:
			log.fatal(f"[DrupalNode._read_node_meta_data()] Couldn't identify node type in body class '{self.meta['node_type']}'")
		self.meta['language'] = DC.get('server.default_language')
		self.meta['last_saved'] = browser.get_value_of_attribute(element = sidebar, key = 'nodes.meta_data.last_saved')
		matches = re.search(DC.get('nodes.meta_data.last_saved.regexp'), self.meta['last_saved'])
		if(matches):
			self.meta['last_saved'] = matches.group(1)
		else:
			log.fatal(f"[DrupalNode._read_node_meta_data()] Couldn't find last saved in meta data of node {self._nodeID} in text '{self.meta['last_saved']}' with regular expresseion '{DC.get('nodes.meta_data.last_saved.regexp')}'")
		self.meta['last_saved'] = datetime.strptime(self.meta['last_saved'], DC.get('server.timestamp_input_format')).strftime(DC.get('server.timestamp_output_format'))
		self.meta['author'] = browser.get_value_of_attribute(element = sidebar, key = 'nodes.meta_data.author')
		matches = re.search(DC.get('nodes.meta_data.author.regexp'), self.meta['author'])
		if(matches):
			self.meta['author'] = matches.group(1)
		else:
			log.info(f"[DrupalNode._read_node_meta_data()] Couldn't find author in meta data of node {self._nodeID} in text '{self.meta['author']}' with regular expresseion '{DC.get('nodes.meta_data.author.regexp')}'. Assuming empty author.")
			self.meta['author'] = ''
		self.meta['moderation_status'] = browser.get_value_of_attribute(element = sidebar, key = 'nodes.meta_data.moderation_status')
		matches = re.search(DC.get('nodes.meta_data.moderation_status.regexp'), self.meta['moderation_status'])
		if(matches):
			self.meta['moderation_status'] = DC.get('server.moderation_status_display_names.' + matches.group(1))
		else:
			log.fatal(f"[DrupalNode._read_node_meta_data()] Couldn't find moderation status in meta data of node {self._nodeID} in text '{self.meta['moderation_status']}' with regular expresseion '{DC.get('nodes.meta_data.moderation_status.regexp')}'")
		self.meta['description'] = browser.get_value_of_attribute(element = sidebar, key = 'nodes.meta_data.description')


	def _read_node_content(self):
		"This attribute reads the mode type specific content fields"
		title = browser.get_value_of_attribute(key = 'nodes.content.title')
		self.content.update({'title': title})


	def _read_node_translations(self):
		if(self.isMedia):
			DConn.load_media_translation_url(nodeID = self._nodeID)
			rows = browser.get_elements(key = 'nodes.translations.rows')
		else:
			DConn.load_node_translation_url(nodeID = self._nodeID)
			rows = browser.get_elements(key = 'nodes.translations.rows')
		for element in rows:
			language_display_name = browser.get_value_of_attribute(element = element, key = 'nodes.translations.row_structure.language_display_name')
			if(not language_display_name in DC.get('server.language_display_names')):
				language_display_name = browser.get_value_of_attribute(element = element, key = 'nodes.translations.row_structure.language_display_name_strong')
			language = DC.get('server.language_display_names.' + language_display_name)
			# we do the next step in order to normalize the exception of en-int being displayed as `English international (Original language)` in translation overview tables :(
			language_display_name = DC.get('server.languages.' + language)
			title = browser.get_value_of_attribute(element = element, key = 'nodes.translations.row_structure.title')
			if(not title):
				title = ''
			translation_status = browser.get_value_of_attribute(element = element, key = 'nodes.translations.row_structure.translation_status')
			self.translations['by_language']['status'][language] = translation_status
			self.translations['by_language']['title'][language] = title
			if(not translation_status in self.translations['by_status']):
				self.translations['by_status'].update({translation_status: [language]})
			else:
				self.translations['by_status'][translation_status].append(language)


	def _read_media_meta_data(self):
		"Reads the media url in edit mode and extracts all meta data from the side bar. Unfortunately we have to jump through hoops to find out the exact media type first"
		matches = None
		DConn.load_media_edit_url(nodeID = self._nodeID)

		media_type = browser.get_value_of_attribute(key = 'server.media_type_identifier')
		if(media_type and media_type in DC.get('server.media_type_display_name')):
			media_type = DC.get('server.media_type_display_name.' + media_type)
		if(not media_type):
			for pim_type in DC.get('server.media_type_pim_identifiers').keys():
				is_pim_type = True
				for element in DC.get('server.media_type_pim_identifiers.' + pim_type):
					if(not browser.has_element(key = 'server.media_type_pim_identifiers.' + pim_type + '.' + element)):
						is_pim_type = False
				if(is_pim_type):
					media_type = pim_type
					break
		if(not media_type):
			log.fatal(f"[DrupalNode._read_media_meta_data()] Couldn't find ")
		self.meta['node_type'] = media_type

		print(f"Found node {self._nodeID} is of media type '{media_type}'")


class ContentNode(DrupalNode):
	"This class implements content node overarching attributes, that are not covered in the super class"
	def __init__(self, row_element = None, nodeID: str = None):
		self._row_element = row_element
		if(type(nodeID) != str): 
			nodeID = str(nodeID)
		if(not nodeID and not row_element):
			log.fatal("[DrupalNode.ContentNode.__init__()] Can't initialize class without either nodeID or row element")
		elif(nodeID):
			super().__init__(nodeID = nodeID, isMedia = False)


	def draft(self):
		self.set_moderation_status("draft")


	def unpublished(self):
		self.set_moderation_status("unpublished")


	def confidential(self):
		self.set_moderation_status("confidential")


	def confidential(self):
		self.set_moderation_status("confidential")


	def ready_for_review(self):
		self.set_moderation_status("ready_for_review")


	def published(self):
		self.set_moderation_status("published")


	def set_moderation_status(self, status: str = 'draft'):
		if(not status in DC.get('server.moderation_status')):
			log.fatal(f"[DrupalNode.set_moderation_status()] Passed moderation status '{status}' is not in the list of configured moderation status, which are: '{DC.get('server.moderation_status').keys()}'")
		sel = Select(browser.get_element(key = 'nodes.interactions.change_status', strict = True))
		sel.select_by_value(status)


	def save(self):
		browser.interact(key = 'nodes.interactions.save_node')
		DConn.load_node_edit_url(nodeID = self._nodeID)

		

class MediaNode(DrupalNode):
	"This class implements media nodes"
	def __init__(self, row_element = None, nodeID: str = None):
		self._row_element = row_element
		if(type(nodeID) != str): 
			nodeID = str(nodeID)
		if(not nodeID and not row_element):
			log.fatal("[DrupalNode.MediaNode.__init__()] Can't initialize class without either nodeID or row element")
		elif(nodeID):
			super().__init__(nodeID = nodeID, isMedia = True)



