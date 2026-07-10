app_name = "stock_and_buying"
app_title = "Stock And Buying"
app_publisher = "ahmad mohammad"
app_description = "Stock and buying management for Binyaber"
app_email = "ahmad900mohammad@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "stock_and_buying",
# 		"logo": "/assets/stock_and_buying/logo.png",
# 		"title": "Stock And Buying",
# 		"route": "/stock_and_buying",
# 		"has_permission": "stock_and_buying.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/stock_and_buying/css/stock_and_buying.css"
# app_include_js = "/assets/stock_and_buying/js/stock_and_buying.js"

# include js, css files in header of web template
# web_include_css = "/assets/stock_and_buying/css/stock_and_buying.css"
# web_include_js = "/assets/stock_and_buying/js/stock_and_buying.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "stock_and_buying/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "stock_and_buying/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "stock_and_buying.utils.jinja_methods",
# 	"filters": "stock_and_buying.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "stock_and_buying.install.before_install"
# after_install = "stock_and_buying.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "stock_and_buying.uninstall.before_uninstall"
# after_uninstall = "stock_and_buying.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "stock_and_buying.utils.before_app_install"
# after_app_install = "stock_and_buying.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "stock_and_buying.utils.before_app_uninstall"
# after_app_uninstall = "stock_and_buying.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "stock_and_buying.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"stock_and_buying.tasks.all"
# 	],
# 	"daily": [
# 		"stock_and_buying.tasks.daily"
# 	],
# 	"hourly": [
# 		"stock_and_buying.tasks.hourly"
# 	],
# 	"weekly": [
# 		"stock_and_buying.tasks.weekly"
# 	],
# 	"monthly": [
# 		"stock_and_buying.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "stock_and_buying.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "stock_and_buying.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "stock_and_buying.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["stock_and_buying.utils.before_request"]
# after_request = ["stock_and_buying.utils.after_request"]

# Job Events
# ----------
# before_job = ["stock_and_buying.utils.before_job"]
# after_job = ["stock_and_buying.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"stock_and_buying.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

