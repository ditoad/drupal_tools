from drupal_logger import log
from drupal_browser import browser
from drupal_configuration import *
import re

class DrupalNode():
	"This is a super class that provides mutual attributes across all node types. Content type specific attributes have to be implemented in inheriting classes."