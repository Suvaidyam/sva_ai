import frappe
def boot_session(bootinfo):
    print("\n\n\n\n","bootinfo","\n\n\n\n")
    try:
        doc = frappe.get_single("Talk To Data")
        if doc:
            bootinfo.talk_to_data = doc.as_dict()
            print("\n\n\n\n",bootinfo.talk_to_data,"\n\n\n\n")
    except Exception as e:
        frappe.log_error(f"Error in boot_session: {e}")
        pass