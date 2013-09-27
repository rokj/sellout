/* categories selector */
/* selecting categories:
 *   create a div for each (sub-)category
 *   data-* attributes: id (category id), level (0 - main category, higher values: subcategories)
 *   $.data(): path (list of all parent categories), category: all category's properties
 *   * selecting a category button (with mouse or keyboard):
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
	//  data-parent-id:<parent category id>

	// add a 'scrollyeah' div and insert a 'button' for each category in 'categories'
	var scroll_div = $("<div>", {"class":"scrollyeah category-select"});
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
	    else img_obj.attr("src", window.data['spacer']); // data is a global variable, set in terminal.html
	    p_obj.append(img_obj); // add image
	    
	    // add name to a new div
	    p_obj.append(cc.name);
	    
	    // append category's data
	    btn_div.data(cc);
	    
	    scroll_div.append(btn_div);
	    
	    // register events
	    btn_div.click(select_category);
	}

	control_div.prepend(scroll_div); // because it's a recursive function, the topmost category will be added last (that's why .prepend)

	// manually init scrollyeah
	_scrollyeah(scroll_div);
	return scroll_div;
}

function select_category(e){
	// the plan:
	// $(this) is the currently selected button
	// get the button's parent div
	// hide categories that are lower level than $(this)
	// show $(this)'s subcategories, if any)
	// highlight the path to this category
	var parent = $(this).parent().parent().parent(); // scrollyeah wraps the scrollyeah div in two more divs
	var level = parseInt(parent.attr("data-level")); // level of category of the current button
	var data = $(this).data();
	var show_div = $("div.category-select[data-parent-id='" + data.id.toString() + "']"); // child categories (this will be shown below the clicked button)
	
	// hide all categories with data-level>level except the child of the current parent
	function hide_subs(){
		if(parseInt($(this).attr("data-level")) > level){
			if(!show_div.data()) $(this).hide();
			else if($(this).data().parentId != show_div.data().parentId) $(this).hide();
		}
	}
	$("div.category-select").each(hide_subs);
	
	// un-highlight: remove all 'active' and 'selected' styles
	$("div.category-button-active, div.category-button-selected").removeClass("category-button-active category-button-selected");

	// highlight: everything on the path with 'active' style, the last with 'selected'
	var i;
	for(i = 0; i < data.path.length-1; i++){ // for each 'super'-category
		// find the div
		$("div.category-button[data-id='" + data.path[i].toString() + "']").addClass("category-button-active");
	}
	$("div.category-button[data-id='" + data.path[data.path.length-1].toString() + "']").addClass("category-button-selected");

	// show the current category's subcategory, but only if it is not yet visible
	if(!show_div.is("visible")) show_div.slideDown(window.data.t);
	
	// scroll the scrollyeah to show the selected button
	var container = $("#controls");
	var margin = parseInt($(this).css("margin-left"));
	var padding = parseInt($(this).css("padding-left"));

	var button_pos = $(this).offset(); // positions
	var parent_pos = container.offset();

	var button_width = $(this).width() + 2*margin + 2*padding;
	var parent_width = container.width();
	
	var new_pos;
	
	// when moving right
	if(button_pos.left + button_width > parent_pos.left + parent_width){
		// move this button to the left
		// if this is the last button in the div, move it so that it just touches the margin
		// if not, show a bit of the next button
		if($(this).is($(this).siblings(":last"))){
			alert("last");
			new_pos = parent_pos.left + parent_width - button_width - margin - padding; // this is the last button
		}
		else{
			alert("not last")
			new_pos = parent_pos.left + parent_width - button_width*3/2 - margin - padding; // there are more buttons on the right
		}
		$(".scrollyeah__shaft", parent).animate({left:new_pos - button_pos.left});
	}
}

function handle_keypress(e){
	var code = (e.keyCode ? e.keyCode : e.which);

	if(!window.focused_item){
		window.focused_item = $(".category-button").filter(":first"); // assign the first item (only in the beginning)
		// if nothing is selected, any key must select something, so override 'code'
		code = 39;
	}

	var prev_item, next_item;

	// left: 37 up: 38 right: 39 down: 40
	switch(code){
		case 37: // left
			// find the previous one
			prev_item = window.focused_item.prev(); 
			if(prev_item.length < 1){
				// there's no next item, roll over to the first one
				window.focused_item = $(".category-button", window.focused_item.parent()).filter(":last");
			}
			else window.focused_item = prev_item;
			window.focused_item.click();
			break;
		case 38: // up
			// find the currently selected button's parent and click() it
			// if it's the topmost button, do nothing
			// (three parents(): two of them are scrollyeah's wrap divs)
			prev_item = $("div.category-button[data-id='" + window.focused_item.parent().parent().parent().attr("data-parent-id") + "']");
			if(prev_item.length < 1) break;
			// store last selected button
			// TODO
			window.focused_item = prev_item;
			prev_item.click();
			break;
		case 39: // right
			// find the next one
			next_item = window.focused_item.next(); 
			if(next_item.length < 1){
				// there's no next item, roll over to the first one
				window.focused_item = $(".category-button", window.focused_item.parent()).filter(":first");
			}
			else window.focused_item = next_item;
			window.focused_item.click();
			break;
		case 40: // down
			// select the first subcategory of the selected one
			// if there is no more subcategories, jump to products
			// else, find the first subcategory
			if(window.focused_item.data().children.length > 0){
				next_item = $("div.category-select[data-parent-id='" + window.focused_item.data().id.toString() + "']");
				focused_item = $("div.category-button:first", next_item);
				focused_item.click();
			}
			else{
				// jump to products
				alert("Products!");
			}
			break;
		default: return;
	}
}