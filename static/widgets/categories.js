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
        btn.click(select_category);
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
function categories_selector(){
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

    // each button holds data() for its category

    // add parent references to all children and
    // create a dictionary of all categories by id for quick selection on product button click
    function add_parent(cat, parent_cat) {
        var i;
        for(i = 0; i < cat.length; i++) {
            if(parent_cat) cat[i].parent = parent_cat;
            if(cat[i].children.length > 0) add_parent(cat[i].children, cat[i]);

            window.data.categories_list[cat[i].id.toString()] = cat[i];
        }
    }
    add_parent(c, null);

    // draggable with easing function
    category_draggable(window.items.parents_div);
    category_draggable(window.items.children_div);

    // bind events to 'favorites' and 'home' buttons
    window.items.all_cat_button.click(categories_home);
    
    $("#category_button_favorites").click(function(){

    });

    // in the beginning, there was the first category selected
    categories_home();
}

function select_category(e, id) { // gets called on buttons that are in parents div
    // e - jQuery event
    // id - id of category to select (if none, take data from $(this).data() )
    var c;

    // get category details from parameter or $(this).data if no parameter was added
    if(id != null) c = window.data.categories_list[id.toString()];
    else c = $(this).data();

    var i, btn, siblings, d;
    var selected;
    var children = c.children;
    var parent = c.parent;
    
    // clear parents
    window.items.children_div.empty();
    window.items.parents_div.empty();
    
    // if this category has no children, just select it
    if(c.children.length < 1){
        // this category also has no parent, so its siblings are topmost categories
        if(!c.parent) siblings = window.data.categories;
        else siblings = c.parent.children;
        
        for(i = 0; i < siblings.length; i++){
            btn = create_button(siblings[i]);
            btn.click(select_category);
            
            // selected?
            if(siblings[i].id == c.id) selected = btn;
            
            window.items.children_div.append(btn);
        }
        
        // add parents to parents_div
        d = c.parent;
        i = 0;
        while(d){
            btn = create_button(d);
            btn.click(select_category);
            
            window.items.parents_div.prepend(btn);
            
            d = d.parent;
        }
    }
    else{
        // this category has children: add it and all its parents to parents_div
        d = c;
        i = 0;
        while(d){
            btn = create_button(d);
            btn.click(select_category);
            
            if(d.id == c.id) selected = btn;

            window.items.parents_div.prepend(btn);
            
            d = d.parent;
        }

        
        // add all its children to children_div
        for(i = 0; i < children.length; i++){
            btn = create_button(children[i]);
            btn.click(select_category);

            if(children[i].id == c.id) selected = btn;

            window.items.children_div.append(btn);
        }
    }
       
    if(selected) selected.addClass("category-button-selected");
    
    // the 'all' button is no more
    window.items.all_cat_button.removeClass("category-button-selected");
    
    // show products from this category, but only if the function wasn't called
    // on click of a product button (that is, id is not defined)
    if(!id) get_category_products(c.id);
}

function handle_keypress(e) {
    // keyboard commands:
    // - left, right: neighbors (leap to first if last and vv)
    // - up: go to parent category (click the parent button)
    // - down/enter: go to subcategory (click the current button)
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
