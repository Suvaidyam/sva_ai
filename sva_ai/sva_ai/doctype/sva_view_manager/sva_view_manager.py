# Copyright (c) 2025, Suvaidyam and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.safe_exec import read_sql
import json
import re

class SVAViewManager(Document):
	@staticmethod
	def get_schedule_expression(freq):
		match freq:
			case "30 Minutes": return "EVERY 30 MINUTE"
			case "1 Hour": return "EVERY 1 HOUR"
			case "3 Hour": return "EVERY 3 HOUR"
			case "8 Hour": return "EVERY 8 HOUR"
			case "12 Hour": return "EVERY 12 HOUR"
			case "1 Day": return "EVERY 1 DAY"
			case "Weekly": return "EVERY 1 WEEK"
			case "Monthly (start)": return "EVERY 1 MONTH STARTS"
			case "Monthly (end)": return "EVERY 1 MONTH ENDS"
			case _: return "EVERY 1 HOUR"

	def slugify_table_name(text):
		if not text:
			frappe.throw("Table name cannot be empty or None.")
		text = text.lower().strip()
		text = re.sub(r'[^\w\s-]', '', text)
		text = re.sub(r'[\s]+', '_', text)
		return text
	
	def run(self):
		try:
			frappe.local.debug_log = []
			result = read_sql(self.sql, as_dict=1)
			self.set("output", frappe.as_json(result))
		except Exception:
			self.set("output", frappe.get_traceback())
		frappe.db.commit()

	def validate(self):
		if not self.sql:
			frappe.throw("SQL query is required")
		if not self.name:
			frappe.throw("Name is required")
		
	def create_or_update_view(self):
		table_name = SVAViewManager.slugify_table_name(self.name)
		if not table_name:
			frappe.throw("Invalid table name")

		try:
			if self.view_type == "Materialized View":
				tbl = f"svaMatView_{table_name}"
				event_name = f"refresh_{tbl}"

				frappe.db.sql_ddl(f"DROP TABLE IF EXISTS {tbl}")
				frappe.db.sql_ddl(f"CREATE TABLE {tbl} AS {self.sql}")
				frappe.db.sql_ddl(f"DROP EVENT IF EXISTS {event_name}")

				# Create event - no BEGIN...END block needed for single statements
				schedule = SVAViewManager.get_schedule_expression(self.refresh_frequency or "1 Hour")
				event_sql = f"""
					CREATE EVENT {event_name}
					ON SCHEDULE {schedule}
					DO
					BEGIN
						INSERT INTO `tabSVA View Log` (`remarks`) VALUES ('START:{event_name}');
						DELETE FROM {tbl};
						INSERT INTO {tbl} {self.sql.rstrip().rstrip(';')};
						INSERT INTO `tabSVA View Log` (`remarks`) VALUES ('END:{event_name}');
					END
				"""
				frappe.db.sql_ddl(event_sql)

			else:
				# Logical view
				view_sql = f"CREATE OR REPLACE VIEW svaView_{table_name} AS {self.sql}"
				frappe.db.sql_ddl(view_sql)

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Error creating view")
			frappe.throw(f"Error creating view: {e}")

	
	def after_insert(self):
		self.create_or_update_view()
		
	def on_update (self):
		self.create_or_update_view()

	def on_trash(self):
		table_name = SVAViewManager.slugify_table_name(self.name)
		if table_name:
			sql = f"""
				DROP VIEW IF EXISTS {table_name}
			"""
			try:
				frappe.db.commit()
				frappe.db.sql_ddl(sql)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "Error dropping view")
				frappe.throw(f"Error dropping view: {e}")


@frappe.whitelist()
def execute_code(doc):
	console = frappe.get_doc(json.loads(doc))
	console.run()
	return console.as_dict()


def clean_sql(sql: str) -> str:
    return sql.rstrip().rstrip(';')

@frappe.whitelist()
def get_sql_columns(doc_name):
	if not doc_name:
			frappe.throw("Document name is required")

	doc = frappe.get_doc('SVA View Manager', doc_name)
	sql = doc.sql.strip().rstrip(';')
	wrapped_query = f"SELECT * FROM ({sql}) AS temp LIMIT 0"
	frappe.db.sql(wrapped_query)

	# Extract column names
	columns_list = [desc[0] for desc in frappe.db._cursor.description]
	doc.set("column", [])
	for col in columns_list:
			doc.append("column", {
				"fieldname": col,
				"fieldtype": "Data",
				"label": col
			})

	doc.save(ignore_permissions=True,update_modified=False)
	return f"{len(columns_list)} columns updated."

