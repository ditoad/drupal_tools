from drupal_configuration import *
from drupal_browser import browser
from drupal_connection import DConn
from drupal_dashboard import *
from drupal_logger import log, Logger
import re
import pprint



class SKU2NodeID():
	"This class provides the attributes for finding the nodeID for a given SKU"

	def __init__(self, exception_logfile: str = ''):
		self._row_count: int = 0
		self._sku: str = ''
		self._nodeID: str = ''
		if(exception_logfile):
			self._exception_logger = Logger(name = "Exceptions", logfile = exception_logfile)
		else:
			self._exception_logger = log
		self._is_correct_product: bool = False
		self.PDB = None


	def get_node_id_for_sku(self, sku: str) -> str:
		self._sku: str = sku
		self._is_correct_product: bool = False
		if(type(self._sku) != str):
			self._sku = str(self._sku)
		self._filters = {
			"language": DC.get('server.default_language'),
			"sku": self._sku
		}
		self.PDB = ProductDashboard(filters = self._filters)
		self._row_count = self.PDB.get_row_count_total()
		if(self._row_count == 1):
			self._is_correct_product = True
			self.PDB.read_row_edit_links()
			self._nodeID = self.PDB.get_first_node_id_on_page()
			if(not self._nodeID):
				self._exception_logger.fatal(f"[SKU2NodeID.__init__()] Couldn't read node id despite having found one row for SKU {self._sku}")
			return self._nodeID
		elif(self._row_count == 0):
			self._exception_logger.error(f"[SKU2NodeID.__init__()] Didn't find any product for SKU {self._sku}")
		else:
			self._exception_logger.error(f"[SKU2NodeID.__init__()] Found a total of {self._row_count} products for SKU {self._sku} with node ids {self.PDB.get_node_ids_on_page()}")


	def get_node_id(self) -> str:
		return self._nodeID


	def is_correct_product(self) -> bool:
		return self._is_correct_product