/* categories selector */
/* selecting categories:
 *   create a div for each (sub-)category
 *   data-* attributes: id (category id), level (0 - main category, higher values: subcategories)
 *   $.data(): path (list of all parent categories), category: all category's properties
 *   
 * selecting a category button (with mouse or keyboard):
 *   fire a custom.select event
 *   from within the category button, hide-show-activate divs, according to ids in $.data().path
 */

function categories_selector(control_div, categories, level, parent_id){
	// control_div: main div that contains all controls
	// scroll_div: div that contains (sub-)categories and to which scrollyeah is 'applied'
	// btn_div: a single category button inside scroll_div
	
	// searching/locating category buttons and their containers:
	// button: 
	//	class:category-button
	//	data-id:<category id>
	//  data-parent-id:<parent category id>
	// category (the button container):
	//  class:category-select
	//  data-parent:

	// add a 'scrollyeah' div and insert a 'button' for each category in 'categories'
	var scroll_div = $("<div>", {"class":"scrollyeah"});
	// add attributes
	scroll_div.attr("data-level", level);
	scroll_div.attr("data-parent-id", parent_id.toString());
	
	// hide if not a parent
	if(level > 0) scroll_div.hide();

	// append a 'button' (div) for each category
	var btn_div, p_obj, img_obj, cc;
	for(var i = 0; i < categories.length; i++){
		cc = categories[i]; // current category (only a shortcut)
		// if this category contains subcategories, add them
		if(cc.children.length > 0) categories_selector(control_div, cc.children, level+1, cc.id);

		// create a custom button for category
		// it's a div; store this category's id to 
	    btn_div = $("<div>", {"class":"category-button", "data-id":cc.id});
	    
	    p_obj = $("<p>", {"class":"category-name"});
	    btn_div.append(p_obj);
	    
	    // add an image, if it has one
	    var img_obj = $("<img>", {"class":"category-button-icon"});
	    
	    if(cc.image) img_obj.attr("src", cc.image);
	    else img_obj.attr("src", data['spacer']); // data is a global variable, set in terminal.html
	    p_obj.append(img_obj); // add image
	    
	    // add name to a new div
	    p_obj.append(cc.name);
	    
	    scroll_div.append(btn_div);
	    
	    // register events
	    btn_div.click(select_category);
	}

	control_div.prepend(scroll_div); // because it's a recursive function, the topmost category will be added last (that's why .prepend)

	// manually init scrollyeah
	//_scrollyeah(category_div);
	return scroll_div;
}

function select_category(e){
	// the plan:
	// $(this) is the currently selected button
	// get the button's parent div
	// 
}

function handle_keypress(e){
	if(!focused_item){
		focused_item = $(".category-button").filter(":first"); // assign the first item (only in the beginning)
	}

	var code = (e.keyCode ? e.keyCode : e.which);

	// left: 37 up: 38 right: 39 down: 40
	switch(code){
		case 37: // left
			focused_item.trigger("deactivate.custom"); // deactivate the current button
			// find the previous one
			prev_item = focused_item.prev(); 
			if(prev_item.length < 1){
				// there's no next item, roll over to the first one
				focused_item = $(".category-button", focused_item.parent()).filter(":last");
			}
			else focused_item = prev_item;
			focused_item.trigger("activate.custom"); // activate it
			break;
		case 38: // up
			break;
		case 39: // right
			focused_item.trigger("deactivate.custom"); // deactivate the current button
			// find the next one
			next_item = focused_item.next(); 
			if(next_item.length < 1){
				// there's no next item, roll over to the first one
				focused_item = $(".category-button", focused_item.parent()).filter(":first");
			}
			else focused_item = next_item;
			focused_item.trigger("activate.custom"); // activate it
			break;
		case 40: // down
			break;
		default: return;
	}
}