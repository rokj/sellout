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
	
	function add_category_button(cc, parent_div, parent_btn, prev){
		var btn_div, p_obj, img_obj, cc, data, first_btn;

		// cc - data for one category
		// if this category contains subcategories, add them
		if(cc.children.length > 0)
			first_btn = categories_selector(control_div, cc.children, level+1, parent_btn);
		else first_btn = null;

		// create a custom button for category
	    btn_div = $("<div>", {"class":"category-button", "data-id":cc.id});
	    p_obj = $("<p>", {"class":"category-name"}); // a paragraph with the name
	    p_obj.append(cc.name);
	    btn_div.append(p_obj);
	    
	    // add an image, if it has one
	    var img_obj = $("<img>", {"class":"category-button-icon"});
	    if(cc.image) img_obj.attr("src", cc.image);
	    else img_obj.attr("src", window.data.spacer); // data is a global variable, set in terminal.html
	    p_obj.append(img_obj); // add image
	    
	    // append category's data
	    data = {
	    	category:cc,
	    	level:level,
	    	parent:parent_btn,
	    	child:first_btn, // the last selected child
	    	prev:prev,
    		next:null, // will be added later
    		first:null, // -||-
    		last:null // -||-
	    };
	    btn_div.data(data);
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

	// append a 'button' (div) for each category
	var prev_obj = null, this_obj, first_obj = null, last_obj = null;
	for(var i = 0; i < categories.length; i++){
		this_obj = add_category_button(categories[i], scroll_div, parent_btn, prev_obj);
		
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

	control_div.prepend(scroll_div); // because it's a recursive function, the topmost category will be added last (that's why .prepend)

	// return the first button of this scroll_div
	return first_obj;
}

function select_category(e){
	// the plan:
	// $(this) is the currently selected button
	// get the button's parent div
	// hide categories that are lower level than $(this)
	// show $(this)'s subcategories, if any)
	// highlight the path to this category
	var prev_item, this_item, item;
	
	// compare both paths and hide things that don't match
	prev_item = window.prev_focused_item;
	this_item = $(this);

	if(prev_item){
		if(this_item.data().level == prev_item.data().level){
			alert("same level");
			// a different category on the same level has been selected
			prev_item.removeClass("category-button-selected");
			// hide the previous 'subcategory' div and show the current one
			if(prev_item.data.child){
				prev_item.data().child.parent().slideUp(window.data.t);
				this_item.data().child.parent().slideDown(window.data.t);
			}
		}
		else if(this_item.data().level > prev_item.data().level){
			alert("dafak");
			// a subcategory of current category has been selected
			// change class of previous item
			prev_item.removeClass("category-button-selected");
			prev_item.addClass("category-button-active");
		}
		else{
			// one of parent (sub)categories has been selected
			// go through previously selected item's path and see where it matches with the current path
			item = prev_item;
			alert("bla")
			while(item){
				if(item == this_item) break;
				else{
					// un-highlight anything inside this div and hide it
					$(".category-button-selected, .category-button-active", item.parent()).hide();
				}
			}
			
		}
					/*item.removeClass("category-button-selected category-button-active");
					item = item.data().parent;
				}
			}
		}*/
	}
	item = this_item;
	while(item){
		// highlight: everything on the path with 'active' style, the last with 'selected'
		if(item == this_item) item.addClass("category-button-selected");
		else item.addClass("category-button-active");

		item.parent().show();
		item = item.data().parent;
	}
	
	/*
	$("div.category-select").each(hide_subs);
	

	var i;
	for(i = 0; i < data.category.path.length-1; i++){ // for each 'super'-category
		// find the div
		$("div.category-button[data-id='" + data.category.path[i].toString() + "']").addClass("category-button-active");
	}
	$("div.category-button[data-id='" + data.category.path[data.category.path.length-1].toString() + "']").addClass("category-button-selected");

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
	/*if(button_pos.left + button_width > parent_pos.left + parent_width){
		// move this button to the left
		// if this is the last button in the div, move it so that it just touches the margin
		// if not, show a bit of the next button
		if($(this).is($(this).siblings(":last"))){
			new_pos = parent_pos.left + parent_width - button_width - margin - padding; // this is the last button
		}
		else{
			new_pos = parent_pos.left + parent_width - button_width*3/2 - margin - padding; // there are more buttons on the right
		}
	}*/
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
			// get the previous one
			prev_item = window.focused_item.data().prev;
			if(!prev_item) prev_item = window.focused_item.data().last; // jump to the first item

			window.prev_focused_item = window.focused_item;
			window.focused_item = prev_item;
			window.focused_item.click();
			break;
		case 38: // up
			// find the currently selected button's parent and click() it
			// if it's the topmost button, do nothing
			// (three parents(): two of them are scrollyeah's wrap divs)
			//prev_item = $("div.category-button[data-id='" + window.focused_item.parent().attr("data-parent-id") + "']");
			//if(prev_item.length < 1) break;
			// store last selected button
			// TODO
			//window.focused_item = prev_item;
			//prev_item.click();
			
			// store this item to parent's child
			prev_item = window.focused_item.data().parent;
			alert(JSON.stringify(window.focused_item.data()));
			if(prev_item){
				window.focused_item.data().child = window.focused_item;
				
				window.prev_focused_item = window.focused_item;
				window.focused_item = prev_item;
				window.focused_item.click();
				alert("click")
			}
			break;
		case 39: // right
			next_item = window.focused_item.data().next;
			if(!next_item) next_item = window.focused_item.data().first; // jump to the first item

			window.prev_focused_item = window.focused_item;
			window.focused_item = next_item;
			window.focused_item.click();
			break;
		case 40: // down
			// select the first subcategory of the selected one
			// if there is no more subcategories, jump to products
			// else, find the first subcategory
			//if(window.focused_item.data().children.length > 0){
				//next_item = $("div.category-select[data-parent-id='" + window.focused_item.data().id.toString() + "']");
				//focused_item = $("div.category-button:first", next_item);
				//focused_item.click();
			//}
			//else{
				//// jump to products
				//alert("Products!");
			//}
			next_item = window.focused_item.data().child;
			if(next_item){
				window.prev_focused_item = window.focused_item;
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