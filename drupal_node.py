from drupal_logger import log
from drupal_browser import browser
from drupal_configuration import *
from drupal_connection import DConn
import re

class DrupalNode():
	"This is a super class that provides mutual attributes across normal nodes and media nodes. Content type specific attributes have to be implemented in inheriting classes."

	def __init__(self, nodeID: str, isMedia: bool = False):
		self._nodeID: str = nodeID
		self.isMedia: bool = isMedia
		self.meta: dict = {
			"last_saved": "",
			"author": "",
			"publication_status": "",
			"moderation_status": "",
			"description": "",
			"robots": [],
			"referer_policy": "",
			"sitemaps": {},
			# translations are done
			"translations": {
				"status": {},
				"title": {}
			},
			"translation_status": {}
		}
		if(not self.isMedia):
			self._read_node_meta_data()
			self._read_node_translations()
		else:
			self._read_media_meta_data()


	def _read_node_meta_data(self):
		"reads the node url in edit mode and extracts all meta data from the side bar"
		DConn.load_node_edit_url(nodeID = self._nodeID)


	def _read_node_translations(self):
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
			self.meta['translations']['status'][language] = translation_status
			if(not translation_status in self.meta['translation_status']):
				self.meta['translation_status'][translation_status] = [language]
			else:
				self.meta['translation_status'][translation_status].append(language)
			self.meta['translations']['title'][language] = title
		print(self.meta)

	def _read_media_meta_data(self):
		"reads the media url in edit mode and extracts all meta data from the side bar"
		print(f"Reading media node {self._nodeID} meta data")







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



