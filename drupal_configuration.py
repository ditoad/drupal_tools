from   jsonref   import JsonRef
from   drupal_logger import log
import json
import functools

DEFAULT_CONFIG_FILE = "drupal.config.json"

class DrupalConfig():
	"This class reads a drupal JSON configuration file and makes it's configuration data accessible in dot-notation. Otherwise one has to access the elements directly from the dictionary 'DC.config'"
	
	def __init__(self, config_file: str = DEFAULT_CONFIG_FILE):
		 self.config = None
		 self.__read_config(config_file)

	def __read_config(self, config_file: str = None):
		try:
			with open(config_file) as c_file:
				self.config = json.load(c_file)
			self.config = JsonRef.replace_refs(self.config)
			log.info(f"[DrupalConfig.__read_config()] Read drupal configuration file '{config_file}'")
			return True
		except:
			log.fatal(f"[DrupalConfig.__read_config()] Couldn't read drupal configuration file '{config_file}'", 1)
			return False

	def configuration_loaded(self):
		if(self.config):
			return True
		return False

	def set_config_file(self, config_file: str = None):
		self.config = None
		return self.__read_config(config_file)

	def get(self, dotted_key: str = ''):
		keys = dotted_key.split('.')
		return functools.reduce(lambda d, key: d.get(key) if d else None, keys, self.config)

DC = DrupalConfig()