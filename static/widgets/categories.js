/* categories draggable with easing */
function category_draggable(obj) {
    var params = {
        // Kudos:
        // http://stackoverflow.com/questions/6602568/jquery-ui-draggable-deaccelerate-on-stop
        helper: function(){
        	return $("<div>").css("opacity",0);
        },
        drag: function(event, ui){
        	// the position of parent obviously has to be taken into account
            var pos = ui.helper.position().left - obj.parent().position().left;
            $(this).stop().animate(
		        { left: pos },
		        window.data.t_easing,
		        'easeOutSine',
		        function(){
		            // check if this has scrolled past the last (first) button
		            var first_button = $(".category-button", obj).filter(":first");
		            var last_button = $(".category-button", obj).filter(":last");
		            var container = obj.parent();
		            
		            // if the whole scroller's width is less than container's, always slide it back to left border
		            if(first_button.position().left + last_button.position().left + last_button.outerWidth() < container.width()){
		                first_button.parent().animate({left:0}, "fast");
		            }
		            else{
			            if(first_button.offset().left > container.offset().left){
			                first_button.parent().animate({left:0}, "fast");
			            }
			            else if(last_button.offset().left + last_button.outerWidth() < container.offset().left + container.width()){
			                first_button.parent().animate({left:-last_button.position().left + container.width() - last_button.outerWidth()}, "fast");
			            }
		            }
		        }
		    );
        },
        axis:"x"
    }

    obj.draggable(params);
}

/* category buttons */
function create_button(cc){
    // stuff to add:
    // a div
    var btn_div = $("<div>", {"class":"category-button", "data-id":cc.id});
    if(cc.children.length > 0) btn_div.addClass("category-button-subcategories");
    // a paragraph with category name
    var p_obj = $("<p>", {"class":"category-name"}); // a paragraph with the name
    p_obj.append(cc.name);
    btn_div.append(p_obj);
    // an image, if the category has one 
    var img_obj = $("<img>", {"class":"category-button-icon"});
    if(cc.image) img_obj.attr("src", cc.image);
    else img_obj.attr("src", window.data.spacer); // data is a global variable, set in terminal.html
    p_obj.prepend(img_obj); // add image
    
    btn_div.data(cc);
    
    return btn_div;
}

function categories_home(){
	var c = window.data.categories;
	// remove stuff from parent and children div
	window.items.parents_div.empty();
	window.items.children_div.empty();
	
	// create children
    for(i = 0; i < c.length; i++){
		btn = create_button(c[i]);
		btn.click(select_child);
		window.items.children_div.append(btn);
	}
}

function scroll_into_view(btn){
	var scroller = btn.parent();
	var frame = scroller.parent();
	
    // scrolling left: if button.left is less than container.left, scroll it into view
    if(btn.offset().left < frame.offset().left){
        scroller.animate({left:-btn.position().left});
    }
    else if(btn.offset().left + btn.outerWidth() > frame.offset().left + frame.width()){
    	// scrolling right: if button.left + button.width > container.left + container.width, scroll it into view
        scroller.animate({left:-btn.position().left + frame.width() - btn.outerWidth()});
    }
}

/* categories selector */
function categories_selector(){
    var c = window.data.categories;
    // there are two divs in terminal: #parents and #children;
    // parent shows:
    //  - path to the current children, shown below, or nothing if in topmost category
    // children shows:
    //  - topmost categories if there's no parent selected
    //  - after selecting parent, a button goes to #parent and all its children are shown in children
    // add buttons for all categories to the children div
    
    // each button holds data() for its category
    
    // add parent references to all children
    function add_parent(cat, parent_cat){
    	var i;
    	for(i = 0; i < cat.length; i++){
    		if(parent_cat) cat[i].parent = parent_cat;
    		if(cat[i].children.length > 0) add_parent(cat[i].children, cat[i]);
    	}
    }
    add_parent(c, null);
    
    // draggable with easing function
    category_draggable(window.items.parents_div);
    category_draggable(window.items.children_div);
    
    // bind events to 'favorites' and 'home' buttons
    $("#category_button_favorites").click(function(){
    	
    });

    $("#category_button_home").click(categories_home);
    
    // show initial window
    categories_home();
}

function select_parent(){
	// gets called on buttons that are in parents div
	var c = $(this).data();
	var children = c.children;
	var i, btn;
	
	// remove everything from children div and add current parent's children
	window.items.children_div.empty(); // WARNING: $(this) does not exist anymore
	
	for(i = 0; i < children.length; i++){
		btn = create_button(children[i]);
		btn.click(select_child);
		window.items.children_div.append(btn);
	}
	
	// remove everything from parents div and add parent>parent>parent...
	window.items.parents_div.empty();
	var item = c;
	var last_btn;
	i = 0;
	while(item){
		btn = create_button(item);
		window.items.parents_div.prepend(
			btn.click(select_parent));
		
		// the last button in parents_div is added first:
		if(i == 0) last_btn = btn;

		item = item.parent;
		i++;
	}
	
	last_btn.addClass("category-button-selected"); // add selected class
	scroll_into_view(btn); // scroll it into view
	window.items.focused = last_btn;
	
}

function select_child(){
	// gets called on buttons that are in children div
	var c = $(this).data();
	var children = c.children;
	var i, btn;

	if(c.children.length > 0){
		// remove the last button's class
		window.items.parents_div.children().removeClass("category-button-selected category-button-active");

		// add current button to parents div
		btn = $(this).clone(true)   // clone won't clone data and events unless called with clone(true)
			.unbind()			   // but we need to bind a different event to it
			.click(select_parent)
			.addClass("category-button-selected")
			
		window.items.parents_div.append(btn);

		// empty children div
		window.items.children_div.empty();
		
		// show current button's subcategories
		for(i = 0; i < children.length; i++){
			btn = create_button(children[i]);
			btn.click(select_child);
			window.items.children_div.append(btn);
		}
	}
	else{
		btn = $(this);
		// unselect other buttons in this div
		window.items.children_div.children().removeClass("category-button-selected");
		window.items.parents_div.children().filter(":last").removeClass("category-button-selected").addClass("category-button-active");
		
		// select this button
		btn.addClass("category-button-selected");
		
		// change parent button's class to 'active'
	}
	scroll_into_view(btn);
	window.items.focused = btn;
}

function handle_keypress(e){
	// keyboard commands:
	// - left, right: neighbors (leap to first if last and vv)
	// - up: select last parent in parents_div
	// - down:
	//   - if in children div: select subcategory
	//   - if in parents div: go to last selected category in children div
	// - num 0: go to products
	
	var code = (e.keyCode ? e.keyCode : e.which);

	if(!window.items.focused){
		window.items.focused = $(".category-button", window.items.children_div).filter(":last"); // assign the first item (only in the beginning)
		// if nothing is selected, any key must select something, so override 'code'
		code = 39;
	}

	var item;

	// left: 37 up: 38 right: 39 down: 40
	switch(code){
		case 37: // left
			// get the previous item
			window.items.focused.removeClass("category-button-focused");
			
			item = window.items.focused.prev();
			if(item.length < 1){ // there's no next item, select the last one
				item = window.items.focused.parent().children().filter(":last");
			}
			item.addClass("category-button-focused");
			window.items.focused = item;
			scroll_into_view(item);
			break;
		case 38: // up
			window.items.focused.removeClass("category-button-focused");
			// get the last button in parents_div and click it
			window.items.parents_div.children().filter(":last").click().fuckyeah();
			break;
		case 39: // right
			// get the next item
			window.items.focused.removeClass("category-button-focused");
			
			item = window.items.focused.next();
			if(item.length < 1){ // there's no next item, select the last one
				item = window.items.focused.parent().children().filter(":first");
			}
			item.addClass("category-button-focused");
			window.items.focused = item;
			scroll_into_view(item);
			break;
		case 40: // down
			window.items.focused.click();
			break;
		default: return;
	}
}
