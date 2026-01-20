import frappe


def get_context(context):
    # No login required
    context.no_cache = 1
