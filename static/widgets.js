/* draggable easing */
function custom_draggable(obj) {
	var params = {
		// Kudos:
		// http://stackoverflow.com/questions/6602568/jquery-ui-draggable-deaccelerate-on-stop
        helper: function(){
            return $('<div></div>').css('opacity',0);
        },
        drag: function(event, ui){
            var p = ui.helper.position();
            $(this).stop().animate(
            		{ left: p.left },
            		window.data.t_easing,
            		'easeOutSine',
            		function(){
        				// check if this has scrolled past the last button
            			first_button = $(".category-button", obj).filter(":first").data().first;
            			last_button = $(".category-button", obj).filter(":first").data().last;
            			container = $("div#controls");
            			
            			if(first_button.parent().outerWidth() > container.width()){
	            			if(first_button.offset().left > container.offset().left){
	            				first_button.parent().animate({left:0}, "fast");
	            			}
	            			else if(last_button.offset().left + last_button.outerWidth() < container.offset().left + container.width()){
	            				first_button.parent().animate({left:-last_button.position().left + container.width() - last_button.outerWidth()}, "fast");
	            			}
            			}

            		});
        },
        axis:"x"
    }

    obj.draggable(params);
}

/* categories selector */
function categories_selector(control_div, categories, level, parent_btn){
	// categories: a list of categories that will be added to parent
	// parent_btn: null if topmost, otherwise jquery object
	// level: integer
	
	// returns the first button of this selector div (jquery object)
	
	// control_div: main div that contains all controls
	// scroll_div: div that contains (sub-)categories and
	// btn_div: a single category button inside scroll_div
	
	// searching/locating category buttons and their containers:
	// button: 
	//	class:category-button
	//	data-id:<category id>
	//  data-parent-id:<parent category id>
	// category (the button container):
	//  class:category-select
	//  data-parent-id:<parent category id>
	
	// each category's data:
	// prev: 'button' of previous category (jquery object)
	// next: 'button' of next category
	// parent: parent button
	// child: handle to *div* that contains children
	// category: all category's data
	
	function add_category_button(cc, parent_div, prev){
		// parent_obj = button
		var btn_div, p_obj, img_obj, cc, first_btn;

		// cc - data for one category
		// create a custom button for category
	    btn_div = $("<div>", {"class":"category-button", "data-id":cc.id});
	    p_obj = $("<p>", {"class":"category-name"}); // a paragraph with the name
	    p_obj.append(cc.name);
	    btn_div.append(p_obj);
	    
	    // add an image, if it has one
	    var img_obj = $("<img>", {"class":"category-button-icon"});
	    if(cc.image) img_obj.attr("src", cc.image);
	    else img_obj.attr("src", window.data.spacer); // data is a global variable, set in terminal.html
	    p_obj.prepend(img_obj); // add image
	    
		// if this category contains subcategories, add them
		if(cc.children.length > 0)
			first_btn = categories_selector(control_div, cc.children, level+1, btn_div);
		else first_btn = null;

	    // append category's data
	    btn_div.data({
	    	category:cc,
	    	level:level,
	    	parent:parent_btn,
	    	child:first_btn, // the last selected child
	    	prev:prev,
    		next:null, // will be added later
    		first:null, // -||-
    		last:null // -||-
	    });
	    scroll_div.append(btn_div);

	    // register events
	    btn_div.click(select_category);
	    return btn_div;
	}
	
	// add a 'scroll' div and insert a 'button' for each category in 'categories'
	var scroll_div = $("<div>", {"class":"category-select"});
	// add attributes
	
	// hide if not a parent
	if(level > 0) scroll_div.hide();

	control_div.append(scroll_div);

	// append a 'button' (div) for each category
	var prev_obj = null, this_obj, first_obj = null, last_obj = null;
	for(var i = 0; i < categories.length; i++){
		this_obj = add_category_button(categories[i], scroll_div, prev_obj, prev_obj);
		
		// store the first and last objects
		if(i == 0) first_obj = this_obj;
		if(i == categories.length - 1) last_obj = this_obj;

		// set next object
		if(prev_obj) prev_obj.data().next = this_obj; // add 'next' to prev object, which is 'this' object
		prev_obj = this_obj;
	}

	// set first and last objects to all buttons
	this_obj = first_obj;
	while(this_obj != null){
		this_obj.data().first = first_obj;
		this_obj.data().last = last_obj;
		this_obj = this_obj.data().next;
	}
	
	// wrap another div around scroll_div for the scrolling effect
	scroll_div
		.wrap($("<div>", {"class":"category-scroll-wrap"}))
		.width(categories.length*parseInt(first_obj.css("max-width"))) // width is not important as long as it's not too narrow
		.wrap($("<div>", {"class":"scroll-wrap-outer"}));
	
	// draggable with easing function
	custom_draggable(scroll_div);

	// return the first button of this scroll_div
	return first_obj;
}

// on click and key press (called by handle_keypress if keyboard)
function select_category(e){
	// this events is called on click and on keyboard press (arrow buttons)
	var this_item = $(this);
	var prev_item = $("div.category-button-selected");
	var item;
	
	// a parent is selected
	// hide everything and show the whole path from parent to child
	$("#controls .category-select").hide();

	$(".category-button-selected").removeClass("category-button-selected ");
	$(".category-button-active").removeClass("category-button-active");

	// show everything on this_item's path
	item = this_item;
	while(item){
		item.parent().show();
		if(item.data().parent) item.data().parent.parent().show();
		// add classes
		if(item == this_item) item.addClass("category-button-selected");
		else item.addClass("category-button-active");
		item = item.data().parent;
	}
	// show the first subcategory
	if(this_item.data().child){
		this_item.data().child.parent().slideDown(window.data.t);
	}
	
	window.focused_item = this_item;
	
	// get the item into view
	// parent().parent():
	//    first parent: category-scroll (fixed width, contains buttons),
	//    second: category-scroll-wrap (wrapper for scrolling)
	var scroll_wrap = this_item.parent().parent();
	var button_div = this_item.parent();
	var container = $("#controls");

	var offset_button = this_item.offset(); // position of the button in document
	var offset_wrap = scroll_wrap.offset();
	var offset_div = button_div.offset();
	var offset_container = container.offset();

	var pos_button = this_item.position(); // position of the button in its parent div
	var pos_wrap = scroll_wrap.position();
	var pos_div = button_div.position();

	// scrolling left: if button.left is less than container.left, scroll it into view
	if(offset_button.left < offset_container.left){
		button_div.animate({left:-pos_button.left});
	}
	else{
		// scrolling right: if button.left + button.width > container.left + container.width, scroll it into view
		if(offset_button.left + this_item.outerWidth() > offset_container.left + container.width()){
			button_div.animate({left:-pos_button.left + container.width() - this_item.outerWidth()});
		}
	}
}

// only for keyboard navigation
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
			// get the previous one
			prev_item = window.focused_item.data().prev;
			if(!prev_item) prev_item = window.focused_item.data().last; // jump to the first item

			window.focused_item = prev_item;
			window.focused_item.click();
			break;
		case 38: // up
			prev_item = window.focused_item.data().parent;
			if(prev_item){
				prev_item.data().child = window.focused_item; // rememver the last selected child
				
				window.focused_item = prev_item;
				window.focused_item.click();
			}
			break;
		case 39: // right
			next_item = window.focused_item.data().next;
			if(!next_item) next_item = window.focused_item.data().first; // jump to the first item

			window.focused_item = next_item;
			window.focused_item.click();
			break;
		case 40: // down
			next_item = window.focused_item.data().child;
			if(next_item){
				window.focused_item = next_item; // select sub-item
				window.focused_item.click();
			}
			else{ // jump to products selector
				alert("products!");
			}
			break;
		default: return;
	}
}

/* products selector */


/* keyboard */
function show_product(){
	// assemble search criteria based on:
	//  - selected category
	//  - product code
	//  - shortcut
}