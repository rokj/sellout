/* categories draggable with easing */
function category_draggable(obj) {
    var params = {
        // Kudos:
        // http://stackoverflow.com/questions/6602568/jquery-ui-draggable-deaccelerate-on-stop
        helper: function () {
            return $("<div>").css("opacity", 0);
        },
        drag: function (event, ui) {
            // the position of parent obviously has to be taken into account
            var pos = ui.helper.position().left - obj.parent().position().left;
            $(this).stop().animate({left: pos},
                window.data.t_easing,
                'easeOutCirc',
                function () {
                    // check if this has scrolled past the last
                    // (first) button
                    var first_button = $(".category-button", obj).filter(":first");
                    var last_button = $(".category-button", obj).filter(":last");
                    var container = obj.parent();

                    if(first_button.length < 1 || last_button.length < 1) return;

                    // if the whole scroller's width is less than
                    // container's, always slide it back to left border
                    if (first_button.position().left + last_button.position().left + last_button.outerWidth() < container.width()) {
                        first_button.parent().animate({left: 0}, "fast");
                    }
                    else {
                        if (first_button.offset().left > container.offset().left) {
                            first_button.parent().animate({left: 0}, "fast");
                        }
                        else if (last_button.offset().left + last_button.outerWidth() < container.offset().left + container.width()) {
                            first_button.parent().animate({left: -last_button.position().left + container.width() - last_button.outerWidth()}, "fast");
                        }
                    }
                });
        },
        axis: "x"
    };

    obj.draggable(params);
}

/* category buttons */
function create_button(cc) {
    // stuff to add:
    // a div
    var btn_div = $("<div>", {
    	"class" : "category-button",
    	"data-id" : cc.id
    });

    if (cc.children.length > 0)
    	btn_div.addClass("category-button-subcategories");
    
	// a paragraph with category name
	var p_obj = $("<p>", {"class" : "category-name"}); // a paragraph with the name
	p_obj.append(cc.name);
	btn_div.append(p_obj);
	// an image, if the category has one
	var img_obj = $("<img>", {"class" : "category-button-icon"});
	if (cc.image)
		img_obj.attr("src", cc.image);
	else
		img_obj.attr("src", window.data.spacer); // data is a global
                        						 // variable, set in
                        						 // terminal.html
	p_obj.prepend(img_obj); // add image
	// a subcategory image (only shown if in parents div)
	p_obj.prepend($("<img>", {src : window.data.subcategory,"class" : "subcategory"}));

    btn_div.data(cc);

    return btn_div;
}

function categories_home() {
    var c = window.data.categories;
    // remove stuff from parent and children div
    window.items.parents_div.empty();
    window.items.children_div.empty();
    window.items.products_list.empty();

    // create children
    for (i = 0; i < c.length; i++) {
    	btn = create_button(c[i]);
    	btn.click(select_child);
    	window.items.children_div.append(btn);
    }

    // add some class to the button
    window.items.all_cat_button.addClass("category-button-selected");
}

function scroll_into_view(btn) {
    var scroller = btn.parent();
    var frame = scroller.parent();

    // scrolling left: if button.left is less than container.left, scroll it into view
    if (btn.offset().left < frame.offset().left) {
    	scroller.animate({left : -btn.position().left});
    }
    else if(btn.offset().left + btn.outerWidth() > frame.offset().left + frame.width()) {
    	// scrolling right: if button.left + button.width > container.left + container.width, scroll it into view
    	scroller.animate({left:-btn.position().left + frame.width() - btn.outerWidth()});
    }
}

/* categories selector */
function categories_selector() {
    var c = window.data.categories;
    // there are two divs in terminal: #parents and #children;
    // parent shows:
    // - path to the current children, shown below, or nothing if in topmost
    // category
    // children shows:
    // - topmost categories if there's no parent selected
    // - after selecting parent, a button goes to #parent and all its children
    // are shown in children
    // add buttons for all categories to the children div

    // each button holds data() for its cate("#category_button_home")gory

    // add parent references to all children
    function add_parent(cat, parent_cat) {
	    var i;
	    for (i = 0; i < cat.length; i++) {
	        if (parent_cat) cat[i].parent = parent_cat;
	        if (cat[i].children.length > 0) add_parent(cat[i].children, cat[i]);
	    }
    }
    add_parent(c, null);

    // draggable with easing function
    category_draggable(window.items.parents_div);
    category_draggable(window.items.children_div);

    // bind events to 'favorites' and 'home' buttons
    $("#category_button_favorites").click(function() {

    });

    window.items.all_cat_button.click(categories_home);

    // show initial window
    categories_home();
}

function select_parent() {
    // gets called on buttons that are in parents div
    var c = $(this).data();
    var children = c.children;
    var i, btn;

    // we're not in 'all categories' anymore
    window.items.all_cat_button.removeClass("category-button-selected");

    // remove everything from children div and add current parent's children
    window.items.children_div.empty(); // WARNING: $(this) does not exist
                    // anymore

    for (i = 0; i < children.length; i++) {
	    btn = create_button(children[i]);
	    btn.click(select_child);
	    window.items.children_div.append(btn);
    }

    // remove everything from parents div and add parent>parent>parent...
    window.items.parents_div.empty();
    var item = c;
    var last_btn;
    i = 0;
    while (item) {
    	btn = create_button(item);
    	window.items.parents_div.prepend(btn.click(select_parent));

    	// the last button in parents_div is added first:
    	if (i == 0)
    		last_btn = btn;

    	item = item.parent;
    	i++;
    }

    last_btn.addClass("category-button-selected"); // add selected class
    get_category_products(last_btn.data().id);
    scroll_into_view(last_btn); // scroll it into view
    window.items.focused = last_btn;
}

function select_child() {
    // gets called on buttons that are in children div
    var c = $(this).data();
    var children = c.children;
    var i, btn;

    // we're not in 'all categories' anymore
    window.items.all_cat_button.removeClass("category-button-selected");

    if (c.children.length > 0) {
        // remove the last button's class
        window.items.parents_div.children().removeClass(
            "category-button-selected category-button-active");
    
        // add current button to parents div
        btn = $(this).clone(true) // clone won't clone data and events unless
            // called with clone(true)
            .unbind() // but we need to bind a different event to it
            .click(select_parent).addClass("category-button-selected");

        window.items.parents_div.append(btn);
        scroll_into_view(btn);
    
        // empty children div
        window.items.children_div.empty();
    
        // show current button's subcategories
        for (i = 0; i < children.length; i++) {
            btn = create_button(children[i]);
            btn.click(select_child);
            window.items.children_div.append(btn);
        }
    }
    else {
        btn = $(this);
        // unselect other buttons in this div
        window.items.children_div.children().removeClass(
            "category-button-selected");
        window.items.parents_div.children().filter(":last").removeClass(
            "category-button-selected").addClass("category-button-active");
    
        // select this button
        btn.addClass("category-button-selected");
        scroll_into_view(btn);
    }

    // get data for this category
    get_category_products(c.id);

    window.items.focused = btn;
}

function handle_keypress(e) {
    // keyboard commands:
    // - left, right: neighbors (leap to first if last and vv)
    // - up: go to parent category (click the parent button)
    // - down: go to subcategory (click the current button)
    // - num 0: go to products

    var code = (e.keyCode ? e.keyCode : e.which);

    if (!window.items.focused) {
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
        if (item.length < 1) { // there's no next item, select the last one
            item = window.items.focused.parent().children().filter(":last");
        }
        item.addClass("category-button-focused");
        window.items.focused = item;
        scroll_into_view(item);
        break;
    case 38: // up
        window.items.focused.removeClass("category-button-focused");
        if (window.items.parents_div.children().length <= 1) {
            // no parent buttons to click, click the "all" (home) button
            $("#category_button_home").click();
        }
        else {
            // show products
            get_category_products(window.items.focused.data().id);

            // click the item before the last parent
            item = window.items.parents_div.children().filter(":last").prev();
            item.click();
        }
        // focus the first child
        window.items.focused = window.items.children_div.children().filter(":first");
        window.items.focused.addClass("category-button-focused");
        break;
    case 39: // right
        // get the next item
        window.items.focused.removeClass("category-button-focused");
    
        item = window.items.focused.next();
        if (item.length < 1) { // there's no next item, select the last one
            item = window.items.focused.parent().children().filter(":first");
        }
        item.addClass("category-button-focused");
        window.items.focused = item;
        scroll_into_view(item);
        break;
    case 13: // enter: same as down, but also show products from the selected category
        case 40: // down
        window.items.focused.removeClass("category-button-focused");
        window.items.focused.click();

        item = window.items.children_div.children().filter(":first");
        item.addClass("category-button-focused");
        window.items.focused = item;
        break;
    default:
    return;
    }
}

function get_category_products(category_id) {
    criteria = {category_filter:category_id, general_filter : ''};

    // clear the products div
    window.items.products_list.empty();

    // show the 'loading' image
    waiting_img = $("<img>", {src:window.data.loading});
    window.items.products_list.append(waiting_img);

    // get products list
    send_data(window.data.search_products_url, criteria,
        window.data.csrf_token, function(recv_data) {
        	waiting_img.remove();
        	show_products(recv_data);
    });

}