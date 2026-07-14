# Copyright (c) 2026, ahmad mohammad and contributors
# For license information, please see license.txt

import os

import frappe
from frappe.utils import flt, today

COMPANY_NAME_MAP = {
	"BIN YABER DRIVING INSTITUTE": "Bin Yaber Driving Institute L.L.C",
	"TAJDEED VEHICLE TESTING CENTER": "Tajdeed Vehicle Testing Center L.L.C",
}

# Defaults used only to auto-create the 2 companies above if they don't exist yet.
# chart_of_accounts is left unset so Company falls back to the "Standard" template,
# which includes the "Temporary Opening" account opening-stock reconciliations need.
COMPANY_DEFAULTS = {
	"Bin Yaber Driving Institute L.L.C": {"abbr": "BYDI", "default_currency": "AED", "country": "United Arab Emirates"},
	"Tajdeed Vehicle Testing Center L.L.C": {"abbr": "T", "default_currency": "AED", "country": "United Arab Emirates"},
}


def _clean(value):
	if value is None:
		return None
	if isinstance(value, str):
		value = value.strip()
		return value or None
	return value


def _is_yes(value):
	value = _clean(value)
	return bool(value) and str(value).strip().upper() == "YES"


def _normalize_category(raw):
	raw = _clean(raw)
	if not raw:
		return None
	# Source file uses a non-breaking hyphen (U+2011) in "NON‑INVENTORY"
	raw = raw.replace("‑", "-")
	return raw.title()


def _resolve_file_path(file_url):
	"""Convert a Frappe file URL to an absolute filesystem path."""
	site_path = frappe.get_site_path()
	if file_url.startswith("/private/files/"):
		return os.path.join(site_path, "private", "files", os.path.basename(file_url))
	elif file_url.startswith("/files/"):
		return os.path.join(site_path, "public", "files", os.path.basename(file_url))
	return os.path.join(site_path, file_url.lstrip("/"))


def _read_excel(file_path):
	"""Return (headers, rows) for the first sheet, skipping fully-blank rows."""
	import openpyxl

	wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
	sheet = wb.worksheets[0]
	rows_iter = sheet.iter_rows(values_only=True)
	headers = list(next(rows_iter))
	rows = [r for r in rows_iter if any(v is not None for v in r)]
	wb.close()
	return headers, rows


def _detect_opening_stock_headers(headers):
	"""Map each 'Opening Stock\\n<Warehouse Name>' header to the warehouse name it refers to."""
	mapping = {}
	for h in headers:
		if not h:
			continue
		h_str = str(h)
		if h_str.upper().startswith("OPENING STOCK"):
			wh_part = h_str[len("Opening Stock") :].strip(" \n:-")
			if wh_part:
				mapping[h] = wh_part.strip().upper()
	return mapping


def ensure_custom_fields():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(
		{
			"Item": [
				{
					"fieldname": "custom_material_request_category",
					"label": "Material Request Category",
					"fieldtype": "Select",
					"options": "\nInventory\nNon-Inventory\nCapex\nService",
					"insert_after": "default_material_request_type",
				},
				{
					"fieldname": "custom_sap_item_code",
					"label": "SAP Item Code",
					"fieldtype": "Data",
					"insert_after": "item_code",
				},
			]
		}
	)


class MasterDataImporter:
	"""Imports Item Group, Warehouse and Item master data (plus opening stock)
	from the 3 attached Excel files, in the correct dependency order."""

	def __init__(self, item_groups_file, warehouse_file, item_file):
		self.item_groups_file = item_groups_file
		self.warehouse_file = warehouse_file
		self.item_file = item_file
		self.item_group_lookup = {}
		self.uom_cache = {}
		self.warehouse_leaf_map = {}

	def run(self):
		result = {"success": False}
		try:
			ensure_custom_fields()

			ig_path = _resolve_file_path(self.item_groups_file)
			wh_path = _resolve_file_path(self.warehouse_file)
			it_path = _resolve_file_path(self.item_file)

			result["companies"] = self.ensure_companies()
			result["asset_categories"] = self.ensure_asset_category()
			result["item_groups"] = self.import_item_groups(ig_path)
			result["warehouses"] = self.import_warehouses(wh_path)

			item_result = self.import_items(it_path)
			opening_stock_rows = item_result.pop("opening_stock_rows")
			result["items"] = item_result

			result["opening_stock"] = self.create_opening_stock_entries(opening_stock_rows)

			frappe.db.commit()
			result["success"] = True
		except Exception as e:
			frappe.db.rollback()
			frappe.log_error(f"Master Data Import Failed: {e}", "Master Data Import Error")
			result["error"] = str(e)

		return result

	def ensure_companies(self):
		"""Create the 2 companies used in COMPANY_NAME_MAP if they don't exist yet.
		Skips (no-op) any company that already exists, so this is safe to re-run."""
		created, skipped, errors = [], [], []

		for company_name, defaults in COMPANY_DEFAULTS.items():
			if frappe.db.exists("Company", company_name):
				skipped.append(company_name)
				continue
			try:
				doc = frappe.get_doc(
					{
						"doctype": "Company",
						"company_name": company_name,
						"abbr": defaults["abbr"],
						"default_currency": defaults["default_currency"],
						"country": defaults["country"],
					}
				)
				doc.insert(ignore_permissions=True)
				created.append(doc.name)
			except Exception as e:
				frappe.clear_messages()
				errors.append(f"{company_name}: {e}")

		return {"created": created, "skipped": skipped, "errors": errors}

	def ensure_asset_category(self):
		"""Create the "IT ASSET" Asset Category (used by the 6 Fixed Asset item rows)
		if it doesn't exist yet, using each company's own Standard Chart of Accounts
		defaults. Skips (no-op) if it already exists, so this is safe to re-run."""
		created, skipped, errors = [], [], []
		category_name = "IT ASSET"

		if frappe.db.exists("Asset Category", category_name):
			skipped.append(category_name)
			return {"created": created, "skipped": skipped, "errors": errors}

		try:
			accounts = []
			for company_name in COMPANY_DEFAULTS:
				if not frappe.db.exists("Company", company_name):
					errors.append(f"{category_name}: company '{company_name}' not found, skipped for that company")
					continue

				# Prefer "Electronic Equipments" (fits IT hardware/software) if this
				# company's Chart of Accounts has it; otherwise fall back to any
				# "Fixed Asset" type account rather than assuming a fixed name - the
				# Chart of Accounts template actually used may differ from "Standard".
				abbr = frappe.get_cached_value("Company", company_name, "abbr")
				preferred = f"Electronic Equipments - {abbr}"
				if frappe.db.exists("Account", preferred):
					fixed_asset_account = preferred
				else:
					fixed_asset_account = frappe.db.get_value(
						"Account",
						{"company": company_name, "account_type": "Fixed Asset", "is_group": 0},
						"name",
					)
				if not fixed_asset_account:
					errors.append(f"{category_name}: no 'Fixed Asset' type account found for company '{company_name}'")
					continue

				company_defaults = frappe.get_cached_value(
					"Company",
					company_name,
					[
						"accumulated_depreciation_account",
						"depreciation_expense_account",
						"capital_work_in_progress_account",
					],
					as_dict=True,
				)
				accounts.append(
					{
						"company_name": company_name,
						"fixed_asset_account": fixed_asset_account,
						"accumulated_depreciation_account": company_defaults.accumulated_depreciation_account,
						"depreciation_expense_account": company_defaults.depreciation_expense_account,
						"capital_work_in_progress_account": company_defaults.capital_work_in_progress_account,
					}
				)

			if not accounts:
				errors.append(f"{category_name}: no companies available to build accounts for")
			else:
				doc = frappe.get_doc(
					{
						"doctype": "Asset Category",
						"asset_category_name": category_name,
						"accounts": accounts,
					}
				)
				doc.insert(ignore_permissions=True)
				created.append(doc.name)
		except Exception as e:
			frappe.clear_messages()
			errors.append(f"{category_name}: {e}")

		return {"created": created, "skipped": skipped, "errors": errors}

	def ensure_root_item_group(self):
		"""ERPNext's "All Item Groups" root is normally created by the interactive
		Setup Wizard, not by app installation - so it may not exist on a fresh site
		set up purely by script. Create it if missing (mirrors install_fixtures.py)."""
		if frappe.db.exists("Item Group", "All Item Groups"):
			return
		frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": "All Item Groups",
				"is_group": 1,
				"parent_item_group": "",
			}
		).insert(ignore_permissions=True)

	def import_item_groups(self, file_path):
		created, skipped, errors = [], [], []
		self.ensure_root_item_group()
		self.item_group_lookup = {g.upper(): g for g in frappe.get_all("Item Group", pluck="name")}

		headers, rows = _read_excel(file_path)
		for raw_row in rows:
			row = dict(zip(headers, raw_row))
			name = _clean(row.get("Item Group Name"))
			if not name:
				continue

			key = name.upper()
			if key in self.item_group_lookup:
				skipped.append(name)
				continue

			try:
				parent_raw = _clean(row.get("Parent Item Group")) or "All Item Groups"
				parent_name = self.item_group_lookup.get(parent_raw.upper(), parent_raw)

				doc = frappe.get_doc(
					{
						"doctype": "Item Group",
						"item_group_name": name,
						"parent_item_group": parent_name,
						"is_group": 1 if _is_yes(row.get("Is Group")) else 0,
					}
				)
				doc.insert(ignore_permissions=True)
				self.item_group_lookup[key] = doc.name
				created.append(doc.name)
			except Exception as e:
				frappe.clear_messages()
				errors.append(f"{name}: {e}")

		return {"created": created, "skipped": skipped, "errors": errors}

	def _resolve_company(self, raw_company):
		"""Resolve a company name from the Excel file. Matches either directly
		against an existing Company's real name, or via the abbreviated
		COMPANY_NAME_MAP - the source file has used both forms at different times."""
		if not raw_company:
			return None
		key = raw_company.upper()
		if key in self._company_lookup:
			return self._company_lookup[key]
		mapped = COMPANY_NAME_MAP.get(key)
		if mapped and frappe.db.exists("Company", mapped):
			return mapped
		return None

	def import_warehouses(self, file_path):
		created, skipped, errors = [], [], []
		group_cache = {}  # (company, name.upper()) -> resolved warehouse name
		self._company_lookup = {c.upper(): c for c in frappe.get_all("Company", pluck="name")}

		headers, rows = _read_excel(file_path)
		for raw_row in rows:
			row = dict(zip(headers, raw_row))
			leaf_name = _clean(row.get("Warehouse Name"))
			if not leaf_name:
				continue

			raw_company = _clean(row.get("Company"))
			company = self._resolve_company(raw_company)
			if not company:
				errors.append(f"{leaf_name}: could not resolve company '{raw_company}'")
				continue

			abbr = frappe.get_cached_value("Company", company, "abbr")
			root = f"All Warehouses - {abbr}"
			if not frappe.db.exists("Warehouse", root):
				errors.append(f"{leaf_name}: expected root warehouse '{root}' not found for company {company}")
				continue

			try:
				parent = root
				for level_name in (_clean(row.get("Parent Warehouse")), _clean(row.get("Is Group Warehouse"))):
					if not level_name:
						continue
					cache_key = (company, level_name.upper())
					if cache_key in group_cache:
						parent = group_cache[cache_key]
						continue

					expected_name = f"{level_name} - {abbr}"
					if frappe.db.exists("Warehouse", expected_name):
						group_cache[cache_key] = expected_name
						parent = expected_name
						continue

					group_doc = frappe.get_doc(
						{
							"doctype": "Warehouse",
							"warehouse_name": level_name,
							"company": company,
							"parent_warehouse": parent,
							"is_group": 1,
						}
					)
					group_doc.insert(ignore_permissions=True)
					group_cache[cache_key] = group_doc.name
					parent = group_doc.name
					created.append(group_doc.name)

				leaf_expected = f"{leaf_name} - {abbr}"
				if frappe.db.exists("Warehouse", leaf_expected):
					skipped.append(leaf_expected)
					self.warehouse_leaf_map[leaf_name.upper()] = leaf_expected
					continue

				leaf_doc = frappe.get_doc(
					{
						"doctype": "Warehouse",
						"warehouse_name": leaf_name,
						"company": company,
						"parent_warehouse": parent,
						"is_group": 0,
					}
				)
				leaf_doc.insert(ignore_permissions=True)
				created.append(leaf_doc.name)
				self.warehouse_leaf_map[leaf_name.upper()] = leaf_doc.name
			except Exception as e:
				frappe.clear_messages()
				errors.append(f"{leaf_name}: {e}")

		return {"created": created, "skipped": skipped, "errors": errors}

	def _get_or_create_uom(self, raw_name):
		raw_name = _clean(raw_name)
		if not raw_name:
			return None
		key = raw_name.upper()
		if key in self.uom_cache:
			return self.uom_cache[key]

		doc = frappe.get_doc({"doctype": "UOM", "uom_name": raw_name.title()})
		doc.insert(ignore_permissions=True)
		self.uom_cache[key] = doc.name
		return doc.name

	def import_items(self, file_path):
		created, skipped, errors = [], [], []
		missing_asset_categories = set()
		opening_stock_rows = []
		ignored_opening_stock = []

		headers, rows = _read_excel(file_path)
		opening_stock_cols = _detect_opening_stock_headers(headers)

		self.item_group_lookup = {g.upper(): g for g in frappe.get_all("Item Group", pluck="name")}
		self.uom_cache = {u.upper(): u for u in frappe.get_all("UOM", pluck="name")}

		for raw_row in rows:
			row = dict(zip(headers, raw_row))

			sap_code = _clean(row.get("SAP Item Code"))
			recommending_code = _clean(row.get("Recommending Item Code"))
			item_code = recommending_code or sap_code
			if not item_code:
				continue

			if frappe.db.exists("Item", item_code):
				skipped.append(item_code)
				continue

			try:
				group_raw = _clean(row.get("Item Group"))
				item_group = self.item_group_lookup.get(group_raw.upper()) if group_raw else None
				if not item_group:
					raise ValueError(f"Item Group '{group_raw}' not found - import Item Groups first")

				is_fixed_asset = 1 if _is_yes(row.get("Is Fixed Asset")) else 0
				is_stock_item = 0 if is_fixed_asset else (1 if _is_yes(row.get("Maintain Stock")) else 0)

				default_uom_raw = _clean(row.get("Default Unit of Measure"))
				conv_uom_raw = _clean(row.get("UOM (UOMs)"))
				conv_factor_raw = row.get("Conversion Factor (UOMs)")

				uoms_table = []
				if conv_uom_raw and conv_factor_raw not in (None, ""):
					# Piece-level unit becomes the stock UOM; the "Default Unit of
					# Measure" column becomes an alternate purchase UOM with the
					# given conversion factor (e.g. 1 Box = 48 Nos).
					stock_uom = self._get_or_create_uom(conv_uom_raw)
					alt_uom = self._get_or_create_uom(default_uom_raw)
					if alt_uom and alt_uom != stock_uom:
						uoms_table.append({"uom": alt_uom, "conversion_factor": flt(conv_factor_raw)})
				else:
					stock_uom = self._get_or_create_uom(default_uom_raw)

				if not stock_uom:
					raise ValueError("No Default Unit of Measure given")

				asset_category = None
				if is_fixed_asset:
					cat_raw = _clean(row.get("Asset Category"))
					if cat_raw and frappe.db.exists("Asset Category", cat_raw):
						asset_category = cat_raw
					else:
						missing_asset_categories.add(cat_raw or "(blank)")

				item_name = _clean(row.get("Item Name")) or item_code

				item_doc = frappe.get_doc(
					{
						"doctype": "Item",
						"item_code": item_code,
						"item_name": item_name,
						"item_group": item_group,
						"stock_uom": stock_uom,
						"is_stock_item": is_stock_item,
						"is_fixed_asset": is_fixed_asset,
						"asset_category": asset_category,
						"valuation_rate": flt(row.get("Valuation Rate")) or 0,
						"description": _clean(row.get("Description")) or item_name,
						"custom_material_request_category": _normalize_category(
							row.get("Default Material Request Type")
						),
						"custom_sap_item_code": sap_code,
						"uoms": uoms_table,
					}
				)
				item_doc.insert(ignore_permissions=True)
				created.append(item_code)

				for header, warehouse_key in opening_stock_cols.items():
					qty = flt(row.get(header))
					if not qty:
						continue
					if not is_stock_item:
						# Contradiction in the source file: item is marked non-stock
						# (Maintain Stock = NO / Fixed Asset) but still has an opening
						# qty. Skip it rather than let it fail the whole warehouse's
						# Stock Reconciliation, and report it as a warning.
						ignored_opening_stock.append(f"{item_code} ({warehouse_key}): qty {qty}")
						continue
					opening_stock_rows.append(
						{
							"item_code": item_code,
							"warehouse_key": warehouse_key,
							"qty": qty,
							"valuation_rate": item_doc.valuation_rate,
						}
					)
			except Exception as e:
				frappe.clear_messages()
				errors.append(f"{item_code}: {e}")

		return {
			"created": created,
			"skipped": skipped,
			"errors": errors,
			"missing_asset_categories": sorted(missing_asset_categories),
			"ignored_opening_stock": ignored_opening_stock,
			"opening_stock_rows": opening_stock_rows,
		}

	def create_opening_stock_entries(self, opening_stock_rows):
		created, errors = [], []
		if not opening_stock_rows:
			return {"created": created, "errors": errors}

		by_warehouse = {}
		for r in opening_stock_rows:
			leaf_name = self.warehouse_leaf_map.get(r["warehouse_key"])
			if not leaf_name:
				errors.append(
					f"{r['item_code']}: warehouse '{r['warehouse_key']}' was not created/found, opening stock skipped"
				)
				continue
			by_warehouse.setdefault(leaf_name, []).append(r)

		for warehouse, item_rows in by_warehouse.items():
			company = frappe.db.get_value("Warehouse", warehouse, "company")
			try:
				# Opening Stock reconciliations must use a Balance Sheet (Temporary/
				# Asset) difference account, not the company's default P&L stock
				# adjustment account (which is what Stock Reconciliation would fall
				# back to if left blank).
				expense_account = frappe.db.get_value(
					"Account", {"is_group": 0, "company": company, "account_type": "Temporary"}, "name"
				)
				if not expense_account:
					raise ValueError(f"No 'Temporary' type Account found for company {company}")

				recon = frappe.get_doc(
					{
						"doctype": "Stock Reconciliation",
						"purpose": "Opening Stock",
						"company": company,
						"posting_date": today(),
						"expense_account": expense_account,
						"items": [
							{
								"item_code": r["item_code"],
								"warehouse": warehouse,
								"qty": r["qty"],
								"valuation_rate": r["valuation_rate"],
							}
							for r in item_rows
						],
					}
				)
				recon.insert(ignore_permissions=True)
				recon.submit()
				created.append(recon.name)
			except Exception as e:
				frappe.clear_messages()
				errors.append(f"{warehouse}: {e}")

		return {"created": created, "errors": errors}
