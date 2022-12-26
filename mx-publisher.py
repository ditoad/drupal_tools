#!/usr/local/bin/python3

from drupal_logger import Logger
from SKU2NodeID import SKU2NodeID

SKU_file = "./mexico_sku_list.txt"
output_file = "SKUs_and_nodeIDs.txt"
SKUs = []
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
	error_logger.fatal(f"[mx-publisher] Couldn't open SKU file '{SKU_file}'. Error message: {e}")

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
	SKU_2_NodeID[sku] = nodeID
	NodeID_2_SKU[nodeID] = sku

	try:
		oFile.write(f"sku={sku} nodeID={nodeID}\n")
	except Exception as e:
		error_logger.fatal(f"Couldn't write 'sku={sku} nodeID={nodeID}' into output file '{output_file}'")
	logger.info(f"Found node ID {nodeID} for SKU {sku}")
oFile.close()