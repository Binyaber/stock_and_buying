# Copyright (c) 2026, ahmad mohammad and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StockTestingdevelopers(Document):
	pass


@frappe.whitelist()
def import_master_data_1(item_groups_file, warehouse_file, item_file):
	frappe.only_for("System Manager")
	from stock_and_buying.master_data_import import MasterDataImporter

	return MasterDataImporter(item_groups_file, warehouse_file, item_file).run()
