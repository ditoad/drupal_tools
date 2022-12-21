import logging
import sys

DEFAULT_LOG_FORMAT = "%(asctime)s — %(levelname)s — %(message)s"

class Logger():
	"This class is wrapping the python logging functionality into a super simple class. Called with 'verbose = True' it prints out into the console. With a passed logfile it writes all log levels from 'Logger.debug(msg)', 'Logger.info(msg)', 'Logger.warn(msg)', 'Logger.error(msg)' up to 'Logger.critical(msg)' and ultimately to 'Logger.fatal(msg)'"

	def __init__(self, name: str = __name__, logfile: str = None, verbose: bool  = False, reset: bool = False, propagate: bool = False):
		self._name = name
		self._logger = logging.getLogger(self._name)
		self._logger.setLevel(logging.INFO)
		self._logger.propagate = propagate
		self._logfile_handler = None
		self._console_handler = None
		self._logfile = logfile

		if(logfile != None):
			self.set_logfile(logfile, reset)

		if(verbose):
			self.verbose(verbose)

	def get_name(self):
		return self._name

	def set_debug(self):
		self._logger.setLevel(logging.DEBUG)

	def set_info(self):
		self._logger.setLevel(logging.INFO)

	def set_warn(self):
		self._logger.setLevel(logging.WARN)

	def set_error(self):
		self._logger.setLevel(logging.ERROR)

	def set_critical(self):
		self._logger.setLevel(logging.CRITICAL)

	def set_logfile(self, logfile: str, reset: bool = False, format: str = "%(asctime)s — %(levelname)s — %(message)s"):
		self._logfile = logfile
		if(reset):
			try:
				self._logfile_handler = logging.FileHandler(logfile, mode='w')
			except:
				print(f"Failed to create logfile '{logfile}'. Maybe the directory doesn't exit or you don't have sufficient rights.")
				sys.exit(1)
		else:
			try:
				self._logfile_handler = logging.FileHandler(logfile)
			except:
				print(f"Failed to create logfile '{logfile}'. Maybe the directory doesn't exit or you don't have sufficient rights.")
				sys.exit(1)
		self._logfile_handler.setFormatter(logging.Formatter(format))
		self.__reset_handlers()

	def remove_logfile(self):
		self._logfile_handler = None
		self.__reset_handlers()

	def get_logfile(self):
		return self._logfile

	def verbose(self, verbose: bool = False):
		if( self._console_handler != None and verbose == False ):
			self._console_handler = None
		elif( self._console_handler == None and verbose == True ):
			self._console_handler = logging.StreamHandler(sys.stdout)
			self._console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
		self.__reset_handlers()

	def propagate(self, propagate: bool = False):
		self._logger.propagate = propagate

	def debug(self, msg: str):
		self._logger.debug(msg)

	def info(self, msg: str):
		self._logger.info(msg)

	def warning(self, msg: str):
		self._logger.warning(msg)

	def error(self, msg: str):
		self._logger.error(msg)

	def critical(self, msg: str):
		self._logger.critical(msg)

	def fatal(self, msg: str, exit_code: int = 1):
		self.verbose(True)
		self._logger.fatal(msg)
		sys.exit(exit_code)

	def __reset_handlers(self):
		self._logger.handlers.clear()
		if( self._logfile_handler != None ):
			self._logger.addHandler( self._logfile_handler )
		if( self._console_handler != None ):
			self._logger.addHandler( self._console_handler )


log = Logger(name = 'DrupalLogger', logfile = "logs/test.log")
log.set_debug()
