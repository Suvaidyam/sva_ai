frappe.pages['wren-ai'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		single_column: true
	});
	let url = frappe.boot?.talk_to_data?.url;
	if (url) {
		// remove border from iframe
		$(`
			<iframe src="${url}" width="100%" style="height: 93vh; border: none;"></iframe>
		`).replaceAll(page.parent);
	}else{
		$(`
			<div class="alert alert-danger">
				No URL found
			</div>
		`).replaceAll(page.parent);
	}
}