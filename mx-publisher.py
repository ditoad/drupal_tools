#!/usr/local/bin/python3
from drupal_logger import Logger
from drupal_node import *
from SKU2NodeID import SKU2NodeID


SKU_file = "./mexico_sku_list.txt"
output_file = "SKUs_and_nodeIDs.txt"
default_locale = 'en-int'
source_locale = 'es-ES'
source_language = 'es'
target_locale = 'es-MX'
SKUs = []
# SKUs = [10302, 10370]
SKU_2_NodeID = {}
NodeID_2_SKU = {}
sku_line_count = 0
extractor = None
logfile = "logs/sku2nodeid.log"
exception_logfile = "logs/sku2nodeid_eror.log"

logger = Logger(name = "application logger", logfile = logfile, reset = False)

error_logger = Logger(name = "application error logger", logfile = exception_logfile)

logger.info(f"\n\n\n---------------------------")
logger.info(f"Starting to identify node IDs for the SKUs in '{SKU_file}'")

try: 
	iFile = open(SKU_file, "r")
	oFile = open(output_file, "w")
except Exception as e:
	error_logger.fatal(f"Couldn't open SKU file '{SKU_file}'. Error message: {e}")

while True:
	sku_line_count += 1
	sku = iFile.readline().strip()
	if(not sku):
		break
	SKUs.append(sku)

logger.info(f"Read a total of {sku_line_count} SKUs")

extractor = SKU2NodeID(exception_logfile = exception_logfile)

for sku in SKUs:
	nodeID = extractor.get_node_id_for_sku(sku = sku)
	if(not nodeID):
		error_logger.error(f"Couldn't find node ID for SKU {sku}")
		continue
	try:
		oFile.write(f"sku={sku} nodeID={nodeID}\n")
	except Exception as e:
		error_logger.fatal(f"Couldn't write 'sku={sku} nodeID={nodeID}' into output file '{output_file}'")
	logger.info(f"Found node ID {nodeID} for SKU {sku}")

	SKU_2_NodeID[sku] = nodeID
	NodeID_2_SKU[nodeID] = sku

	CN = None
	CN = ContentNode(nodeID = nodeID)

	en_int_moderation_status = None
	es_translation_status = None
	es_ES_translation_status = None
	es_MX_translation_status = None


	en_int_moderation_status = CN.get_moderation_status()
	es_translation_status = CN.get_translation_status(lang = source_language)
	es_ES_translation_status = CN.get_translation_status(lang = source_locale)
	es_MX_translation_status = CN.get_translation_status(lang = target_locale)

	print(f"\nNode: {nodeID}")
	print("--------------")
	print(f"{default_locale}: {en_int_moderation_status}")
	print(f"{source_language}: {es_translation_status}")
	print(f"{source_locale}: {es_ES_translation_status}")
	print(f"{target_locale}: {es_MX_translation_status}")


	if(es_MX_translation_status == 'not_translated'):
		error_logger.error(f"SKU {sku}: not translated for '{target_locale}'. Moderation status en-int: '{en_int_moderation_status}' -- moderation status es: '{es_translation_status}' -- moderation status es-ES: '{es_ES_translation_status}' -- ")
		continue

	# else we can just publish the existing, but not yet published, es-MX version
	elif(es_MX_translation_status != 'published'):
		CN.set_translation_moderation_status(lang = target_locale, status = 'published')
		CN.save()
		logger.info(f"SKU {sku}: published pre-existing translation for '{target_locale}'")

	elif(es_MX_translation_status == 'published'):
		logger.info(f"SKU {sku}: already published in '{target_locale}'. Nothing to do")

oFile.close()
