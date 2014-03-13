/* categories:
 *  there are two divs in terminal: #parents and #children;
 *    parent shows:
 *      - path to the current children, shown below, or nothing if in topmost category
 *    children shows:
 *      - topmost categories if there's no parent selected
 *      - after selecting parent, a button goes to #parent and all its children are shown in children
 */
Categories = function(g){
    var p = this;

    p.g = g;

    p.categories = []; // will hold Category() objects
    p.categories_by_id = {}; // will hold pairs id:{category reference} for faster searching
    p.current_category = null;

    p.items = {
        parents: $("#parents"), // parent categories
        children: $("#children"), // children categories
        home_button: $("#category_button_home"),
        favorites_button: $("#category_button_favorites")
    };

    //
    // methods
    //
    p.clear_parents = function(){ $("div.category-button", p.items.parents).hide(); };
    p.clear_children = function(){ $("div.category-button", p.items.children).hide(); };
    p.clear = function(){
        p.clear_parents();
        p.clear_children();
    };

    p.home_button_action = function(){
        // clear everything first
        p.clear();

        // show only top categories in children div
        for(var i = 0; i < p.categories.length; i++){
            p.categories[i].children_button.show();
        }
    };

    //
    // init
    //

    // draggable parents and children
    set_draggable(p.items.parents, "div.category-button:visible", p.g.settings.t_easing);
    set_draggable(p.items.children, "div.category-button:visible", p.g.settings.t_easing);

    // create all categories
    var i, c;
    c = p.g.data.categories;
    for(i = 0; i < c.length; i++){
        p.categories[i] = new CategoryButton(p, null, c[i]);
    }

    // home button action
    p.items.home_button.click(function(){ p.home_button_action(); });

    // in the beginning, show the home button
    p.home_button_action();
};

CategoryButton = function(list, parent, data){
    var p = this;

    p.list = list; // category list, the god of categories
    p.parent = parent;
    p.data = data; // this category's data
    p.g = p.list.g;

    p.has_children = (p.data.children.length > 0);

    p.subcategories = []; // an object for each subcategory

    p.children_button = null; // the button in the children div
    p.parents_button = null; // the button in the parents div (this may not be there at all)

    // add a pair to list.categories_by_id
    p.list.categories_by_id[p.data.id] = p.data;

    //
    // methods
    //
    p.create_button = function(){
        // stuff to add:
        // a div
        p.button = $("<div>", { "class": "category-button"}).hide(); // will be shown later

        if (p.has_children) // show that this category has subcategories
            p.button.addClass("category-button-subcategories");

        // a paragraph with category name
        p.button.append($("<span>", {"class": "category-button-text"}).text(p.data.name));

        // category icon
        var img_obj;
        if (p.data.image) // create a new image from category's icon
            img_obj = $("<img>", {src: p.data.image });
        else // use an existing spacer from template
            img_obj = p.g.items.spacer;

        img_obj.addClass("category-button-icon");
        p.button.prepend(img_obj); // add image

        // appending: in parents div, prepend (subcategory is the last to be shown)
        //            in children, append (sorted by name, alphabetically)

        // append to children div
        p.children_button = p.button.clone().appendTo(p.list.items.children);

        // append to parents div only if it has subcategories
        if(p.subcategories.length > 0)
            p.parents_button = p.button.clone().prependTo(p.list.items.parents);
    };

    p.show_children = function(){
        if(p.has_children){
            // this category has children: show parents_button and all subcategories

            // remove current children
            p.list.clear();

            // show all buttons of all subcategories
            for(var i = 0; i < p.subcategories.length; i++){
                p.subcategories[i].children_button.show();
            }

            // show parents
            var c = p;
            while(c){
                if(c.parents_button) c.parents_button.show();
                c = c.parent;
            }
        }

        // TODO: show products in this category
    };

    p.click_action = function(){
        // show children
        p.show_children();

        // show products from this category
        p.g.objects.products.show_products(
            p.g.objects.search.search_by_category(p.data.id)
        );
    };

    //
    // init
    //
    // create subcategories
    var i, c = p.data.children;
    for(i = 0; i < c.length; i++){
        p.subcategories[i] = new CategoryButton(p.list, p, c[i]);
    }

    // button (categories must already be initialized)
    p.create_button();

    // register events
    $().add(p.parents_button).add(p.children_button).click(function(){ p.click_action(); });
};

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
        window.items.focused = $(".category-button", window.items.children_div).filter(":last"); // assign the first Item (only in the beginning)
        // if nothing is selected, any key must select something, so override 'code'
        code = 39;
    }

    var item;

    // left: 37 up: 38 right: 39 down: 40
    switch(code){
    case 37: // left
        // get the previous Item
        window.items.focused.removeClass("category-button-focused");
    
        item = window.items.focused.prev();
        if (item.length < 1) { // there's no next Item, select the last one
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

            // click the Item before the last parent
            item = window.items.parents_div.children().filter(":last").prev();
            item.click();
        }
        // focus the first child
        window.items.focused = window.items.children_div.children().filter(":first");
        window.items.focused.addClass("category-button-focused");
        break;
    case 39: // right
        // get the next Item
        window.items.focused.removeClass("category-button-focused");
    
        item = window.items.focused.next();
        if (item.length < 1) { // there's no next Item, select the last one
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
