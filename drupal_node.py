from datetime import datetime
from drupal_logger import log
from drupal_browser import browser
from drupal_configuration import *
from drupal_connection import DConn
from selenium.webdriver.support.select import Select
import pprint


# To Dos: Add the view name and language to the BROWSER


class DrupalNode():
	"This is a super class that provides mutual attributes across normal nodes and media nodes. Content type specific attributes have to be implemented in inheriting classes."


	# To be implemented - adding a new node to Drupal. Currently there is no need for automatically adding nodes (yet)
	# def __init__(self, node_type: str)


	# This init attribute method loads existing nodes and initializes all meta data
	def __init__(self, nodeID: str, isMedia: bool = False):
		self._nodeID: str = nodeID
		self.isMedia: bool = isMedia
		self.meta: dict = {
			"node_type": "",
			"language": "",
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
			# self.pprint_meta()
			self._read_node_content()
			if(self.meta['node_type'] in DC.get('server.translatable_content_types')
				):
				self._read_node_translations()
			DConn.load_node_edit_url(nodeID = self._nodeID)
		else:
			self._read_media_meta_data()
			# self._read_media_content()
			if(self.meta['node_type'] in DC.get('server.translatable_content_types')
				):
				self._read_node_translations()


	def add_translation(self, target_lang: str, src_lang: str = 'en-int', moderation_status: str = 'draft'):
		"this method creates a translation of the node in a passed language (if it doesn't already exist) based on a passed language, language/country version"
		if(not self.is_translatable()):
			log.fatal(f"[DrupalNode.add_translation()] The node's ({self._nodeID}) content type '{self.meta['node_type']}' is not translatable. Translatable content and media types are: {DC.get('server.translatable_content_types')}")
		if(not self.check_languages([target_lang, src_lang])):
			log.fatal(f"[DrupalNode.add_translation()] Target '{target_lang}' or source language '{src_lang}' is not available in the configured languages, which are '{DC.get('server.languages')}'")
		if(not self.is_translated(lang = src_lang)):
			log.error(f"Translation status for source language '{src_lang}' is '{self.get_translation_status(lang = src_lang)}'. It has to be present and '{DC.get('nodes.translations.no_translation_status')}' in order to be able to add a new translation.")
			return
		if(not self.get_translation_status(lang = target_lang) or self.is_translated(lang = target_lang)):
			log.error(f"Translation status for target language '{target_lang}' is '{self.get_translation_status(lang = target_lang)}'. It has to be present and '{DC.get('nodes.translations.no_translation_status')}' in order to be able to add a new translation. You can set the moderation status of a previously translated node, but you can't add an already present translation.")
			return
		if(not self.isMedia and not moderation_status in DC.get('server.moderation_status')):
			log.fatal(f"[DrupalNode.translate()] Moderation status '{moderation_status}' is not in the configured list of moderation status '{DC.get('server.moderation_status').keys()}'")
		translation_url: str = DConn.get_server_url() + '/' + target_lang
		if(not self.isMedia):
			translation_url = translation_url + DC.get('server.node_add_translation_prefix') + self._nodeID + DC.get('server.node_add_translation_postfix')
		else:
			translation_url = translation_url + DC.get('server.media_add_translation_prefix') + self._nodeID + DC.get('server.media_add_translation_postfix')
		translation_url = translation_url + src_lang + '/' + target_lang
		browser.load_url(url = translation_url, lang = target_lang, view = 'node_add_translation')
		self._language = target_lang
		if(not self.isMedia):
			self.set_moderation_status(status = moderation_status)
		else:
			# media is only either 'published' or 'Not translated'. There is no moderation status.
			moderation_status = 'published'
		self.translations['by_language']['status'][target_lang] = moderation_status
		self.translations['by_language']['title'][target_lang] = self.translations['by_language']['title'][src_lang]
		if(moderation_status in self.translations['by_status']):
			self.translations['by_status'][moderation_status].append(target_lang)
		else:
			self.translations['by_status'][moderation_status] = [target_lang]
		if(self.isMedia):
			browser.interact(key = 'nodes.interactions.save_media')
		else:
			browser.interact(key = 'nodes.interactions.save_node')


	def delete_translation(self, lang: str) -> bool:
		"This attribute deletes the passed target language's translation (if present). The target language can not be the server's default language, because that deletes the node with all its translations at once. Use delete_node() for that."
		if(lang == DC.get('default_language')):
			log.fatal(f"[DrupalNode.delete_translation()] Attempted deletion of the server's default language '{lang}' not possible, because it would delete all other translations along with it. Use delete_node() atribute instead")
		if(not self.is_translated(lang = lang)):
			log.error(f"[DrupalNode.delete_translation()] No translation in '{lang}' found for deletion,")
			return False

		deletion_url: str = DConn.get_server_url() + '/' + lang

		if(not self.isMedia):
			deletion_url = deletion_url + DC.get('server.node_delete_translation_prefix') + self._nodeID + DC.get('server.node_delete_translation_postfix')
		else:
			deletion_url = deletion_url + DC.get('server.media_delete_translation_prefix') + self._nodeID + DC.get('server.media_delete_translation_postfix')
		browser.load_url(url = deletion_url, view = 'node_delete_translation', lang = lang)
		if(self.isMedia):
			browser.interact(key = 'nodes.interactions.delete_media')
		else:
			browser.interact(key = 'nodes.interactions.delete_node')
		moderation_status = self.translations['by_language']['status'][lang]
		self.translations['by_language']['status'][lang] = DC.get('nodes.translations.no_translation_status')
		self.translations['by_language']['title'][lang] = ''
		self.translations['by_status'][moderation_status].pop(self.translations['by_status'][moderation_status].index(lang))


	def check_languages(self, languages = []) -> bool:
		"Returns True if the languages are configured"
		for lang in languages:
			if(not self.check_language(lang)):
				return False
		return True


	def check_language(self, lang: str) -> bool:
		"Returns True if the language is configured"
		if(lang in DC.get('server.languages')):
			return True
		return False


	def is_translatable(self) -> bool:
		"Checks if the node's content type is translatable"
		if(not self.meta['node_type'] in DC.get('server.translatable_content_types')
				):
			return False
		return True


	def is_translated(self, lang: str) -> bool:
		"checks if a given language has a translation"
		translation_status = self.get_translation_status(lang = lang)
		if(not translation_status or translation_status == DC.get('nodes.translations.no_translation_status')):
			return False
		return True


	def is_translated_and_published(self, lang: str) -> bool:
		translation_status = self.get_translation_status(lang = lang)
		if(not translation_status or translation_status != DC.get('server.moderation_status_display_names.Published')):
			return False
		return True


	def get_moderation_status(self) -> str:
		if(self.isMedia):
			log.error(f"[DrupalNode.get_moderation_status()] is not applicable to media nodes. Node '{self._nodeID}' is a media node. Returning empty string.")
			return ''
		return self.meta['moderation_status']


	def get_translation_status(self, lang: str) -> str:
		"returns the translation status"
		if(not lang in self.translations['by_language']['status']):
			return ''
		return self.translations['by_language']['status'][lang]


	def pprint(self):
		self.pprint_meta()
		self.pprint_translations()


	def pprint_meta(self):
		print(f"\nMeta data for node {self._nodeID}")
		print("--------------------------")
		pprint.pprint(self.meta)


	def pprint_translations(self):
		print(f"\nTranslation data for node {self._nodeID}")
		print("--------------------------------")
		pprint.pprint(self.translations)


	def load_edit_page(self):
		if(self.isMedia):
			DConn.load_media_edit_url(nodeID = self._nodeID)
		else:
			DConn.load_node_edit_url(nodeID = self._nodeID)


	def load_translations_overview_page(self):
		if(self.isMedia):
			DConn.load_media_translation_url(nodeID = self._nodeID)
		else:
			DConn.load_node_translations_overview_url(nodeID = self._nodeID)

	
	def load_translation_edit_page(self, lang: str = None):
		if(not lang):
			log.fatal(f"[DrupalNode.load_translation_edit_page()] No language passed for loading translation page for Drupal node id {self._nodeID}")
		if(not self.check_language(lang = lang)):
			log.fatal(f"[DrupalNode.load_translation_edit_page()] Language '{lang}' is not available in the configured languages of this Drupal server.")
		if(not self.is_translated(lang = lang)):
			log.fatal(f"[DrupalNode.load_translation_edit_page()] Drupal node id {self._nodeID} is not translated in passed language '{lang}'")
		DConn.load_node_edit_url(nodeID = self._nodeID, lang = lang)


	def _read_node_meta_data(self):
		"reads the node url in edit mode and extracts all meta data from the side bar"
		self.load_edit_page()
		# getting the sidebar with meta data for speeding up extraction of data (smaller DOM to look into)
		sidebar = browser.get_element(key = 'nodes.meta_data.existence', strict = True)
		if(not sidebar):
			log.fatal(f"[DrupalNode._read_node_meta_data()] The node with ID {self._nodeID} doesn't have a meta data side bar.")
		self.meta['node_type'] = browser.get_value_of_attribute(key = 'server.content_type_body_class_attribute')
		self.meta['language'] = DC.get('server.default_language')
		self.meta.update({'last_modified': browser.get_value_of_attribute(element = sidebar, key = 'nodes.meta_data.last_modified')})
		self.meta['last_modified'] = datetime.strptime(self.meta['last_modified'], DC.get('server.timestamp_input_format')).strftime(DC.get('server.timestamp_output_format'))
		self.meta.update({'author': browser.get_value_of_attribute(element = sidebar, key = 'nodes.meta_data.author')})
		self.meta.update({'moderation_status': browser.get_value_of_attribute(element = sidebar, key = 'nodes.meta_data.moderation_status')})
		self.meta.update({'description': browser.get_value_of_attribute(element = sidebar, key = 'nodes.meta_data.description')})


	def _read_node_content(self):
		"This attribute reads the mode type specific content fields"
		title = browser.get_value_of_attribute(key = 'nodes.content.title')
		self.content.update({'title': title})


	def _read_node_translations(self):
		self.load_translations_overview_page()
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
			translation_status = DC.get('server.moderation_status_display_names.' + translation_status)
			self.translations['by_language']['status'][language] = translation_status
			self.translations['by_language']['title'][language] = title
			if(not translation_status in self.translations['by_status']):
				self.translations['by_status'].update({translation_status: [language]})
			else:
				self.translations['by_status'][translation_status].append(language)


	def _read_media_meta_data(self):
		"Reads the media url in edit mode and extracts all meta data from the side bar. Unfortunately we have to jump through hoops to find out the exact media type first"
		self.load_edit_page()
		media_type = browser.get_value_of_attribute(key = 'server.media_type_identifier')
		print(f"Found media_type {media_type}")
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
			log.fatal(f"[DrupalNode._read_media_meta_data()] Couldn't find a media type '{media_type}'")
		self.meta['node_type'] = media_type
		self.meta['language'] = DC.get('server.default_language')
		self.meta.update({'author': browser.get_value_of_attribute(key = 'nodes.meta_data.authored_by')})
		date = browser.get_value_of_attribute(key = 'nodes.meta_data.authored_date') + '_' + browser.get_value_of_attribute(key = 'nodes.meta_data.authored_time')
		self.meta.update({'last_modified': date})
		self.meta.update({'file_size': browser.get_value_of_attribute(key = 'nodes.meta_data.file_size')})
		self.meta.update({'file_url': browser.get_value_of_attribute(key = 'nodes.meta_data.file_url')})
		self.meta.update({'file_url_alias': browser.get_value_of_attribute(key = 'nodes.meta_data.file_url_alias')})



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
		self.meta.update({'moderation_status': status})


	def set_translation_moderation_status(self, lang: str = None, status: str = 'draft'):
		if(not lang):
			log.fatal(f"[DrupalNode.set_translation_moderation_status()] No language passed for setting translation status for Drupal node id {self._nodeID}")
		if(not status in DC.get('server.moderation_status')):
			log.fatal(f"[DrupalNode.set_translation_moderation_status()] Passed moderation status '{status}' is not in the list of configured moderation status, which are: '{DC.get('server.moderation_status').keys()}'")
		sel = Select(browser.get_element(key = 'nodes.interactions.change_status', strict = True))
		sel.select_by_value(status)


	def save(self):
		browser.interact(key = 'nodes.interactions.save_node')
		self.load_edit_page()



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



