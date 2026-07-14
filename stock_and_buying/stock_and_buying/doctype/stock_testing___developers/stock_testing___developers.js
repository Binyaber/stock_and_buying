// Copyright (c) 2026, ahmad mohammad and contributors
// For license information, please see license.txt

frappe.ui.form.on("Stock Testing - developers", {
	master_data_1_upload(frm) {
		if (!frm.doc.item_groups_attach || !frm.doc.warehouse_attach || !frm.doc.item_attach) {
			frappe.msgprint(__("Please attach all 3 files (Item Groups, Warehouse, Item) first."));
			return;
		}

		frappe.confirm(
			"This will create Item Groups, Warehouses, Items, and opening-stock Stock Reconciliations from the attached files. Continue?",
			() => {
				frappe.call({
					method: "stock_and_buying.stock_and_buying.doctype.stock_testing___developers.stock_testing___developers.import_master_data_1",
					args: {
						item_groups_file: frm.doc.item_groups_attach,
						warehouse_file: frm.doc.warehouse_attach,
						item_file: frm.doc.item_attach,
					},
					freeze: true,
					freeze_message: __("Importing master data..."),
					callback: function (r) {
						if (!r.message) return;
						let d = r.message;

						if (!d.success) {
							frappe.msgprint({
								title: __("Import Failed"),
								indicator: "red",
								message: d.error || "Unknown error",
							});
							return;
						}

						function section(title, stage) {
							if (!stage) return "";
							let msg = `<b>${title}</b><br>`;
							msg += `Created: ${stage.created ? stage.created.length : 0} | `;
							msg += `Skipped: ${stage.skipped ? stage.skipped.length : 0} | `;
							msg += `Errors: ${stage.errors ? stage.errors.length : 0}<br>`;
							if (stage.errors && stage.errors.length) {
								msg += `<div style="max-height:150px;overflow:auto;background:#f8d7da;padding:8px;font-size:12px;">`;
								msg += stage.errors.join("<br>");
								msg += `</div>`;
							}
							return msg + "<br>";
						}

						let msg = "";
						msg += section("Item Groups", d.item_groups);
						msg += section("Warehouses", d.warehouses);
						msg += section("Items", d.items);

						if (d.items && d.items.missing_asset_categories && d.items.missing_asset_categories.length) {
							msg += `<b style="color:orange;">Missing Asset Categories (items created without them):</b><br>`;
							msg += d.items.missing_asset_categories.join(", ") + "<br><br>";
						}

						msg += `<b>Opening Stock (Stock Reconciliations)</b><br>`;
						msg += `Created: ${d.opening_stock.created.length}`;
						if (d.opening_stock.errors && d.opening_stock.errors.length) {
							msg += ` | Errors: ${d.opening_stock.errors.length}<br>`;
							msg += `<div style="max-height:150px;overflow:auto;background:#f8d7da;padding:8px;font-size:12px;">`;
							msg += d.opening_stock.errors.join("<br>");
							msg += `</div>`;
						} else {
							msg += "<br>";
						}

						frappe.msgprint({
							title: __("Master Data Import Complete"),
							indicator: "green",
							message: msg,
						});
					},
				});
			}
		);
	},
});
