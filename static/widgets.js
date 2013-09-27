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
	    p_obj.append(img_obj); // add image
	    
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

	control_div.prepend(scroll_div); // because it's a recursive function, the topmost category will be added last (that's why .prepend)

	// return the first button of this scroll_div
	return first_obj;
}

function select_category(e){
	// this events is called on click and on keyboard press (arrow buttons)
	var this_item = $(this);
	var prev_item = $("div.category-button-selected");
	var item;
	
	if(prev_item.length == 0){
		// highlight this item and show its children
		this_item.addClass("category-button-selected");
		if(this_item.data().child){
			this_item.data().child.parent().slideDown(window.data.t);
		}
		// TODO: products
	}
	else{
		// there's already a button selected: 
		// unselect and hide everything until the current item matches this_item
		if(prev_item.data().level < this_item.data().level){
			// a subcategory has been selected, highlight the previous item with 'active' class and highlight this with 'selected'
			// and open subcategory div, if any
			prev_item.removeClass("category-button-selected");
			prev_item.addClass("category-button-active");
			
			this_item.addClass("category-button-selected");
		}
		else if(prev_item.data().level == this_item.data().level){
			// a 'neighbor' item selected
			prev_item.removeClass("category-button-selected category-button-active");
			// hide subcategories
			if(prev_item.data().child) prev_item.data().child.parent().hide();
			this_item.addClass("category-button-selected");
			// show this item's subcategory
			if(this_item.data().child) this_item.data().child.parent().slideDown(window.data.t);
		}
		else{
			// a parent is selected
			item = prev_item;
			while(item){
				if(item.data().category.id == this_item.data().category.id){
					item.addClass("category-button-selected");
					if(item.data().child){
						if(!item.data().child.parent().is("visible"))
							item.data().child.parent().slideDown(window.data.t);
					}
					break; // from here on paths are the same
				}
				else{
					item.removeClass("category-button-selected category-button-active");
					item.parent().hide();
					item = item.data().parent;
				}
			}
		}
	}
	window.focused_item = this_item;
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

			window.focused_item = prev_item;
			window.focused_item.click();
			break;
		case 38: // up
			prev_item = window.focused_item.data().parent;
			if(prev_item){
				window.focused_item.data().child = window.focused_item;
				
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