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

    p.items = {
        parents: $("#parents"), // parent categories
        children: $("#children"), // children categories
        home_button: $("#category_button_home"),
        back_button: $("#category_parent"),
        favorites_button: $("#category_button_favorites")
    };

    // show the home button if displaying breadcrumbs
    if(p.g.config.display_breadcrumbs){
        p.items.home_button.show();
    }

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

        // hide the back button if displaying breadcrumbs
        if(!p.g.config.display_breadcrumbs){
            p.items.back_button.hide();
        }

        // TODO: display what products?
    };

    //
    // init
    //

    // draggable parents and children
    set_draggable(p.items.parents, "div.category-button:visible", p.g.settings.t_easing);
    set_draggable(p.items.children, "div.category-button:visible", p.g.settings.t_easing);

    // create all top-level categories
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

            // show parents: if display_breadcrumbs is on
            if(p.g.config.display_breadcrumbs){
                var c = p;
                while(c){
                    if(c.parents_button) c.parents_button.show();
                    c = c.parent;
                }
            }
            else{
                // if display_breadcrumbs is off, show only this category's parent and back button
                p.parents_button.show();

                // show the back button (unless showing breadcrumbs)
                // and bind an action to it
                p.list.items.back_button.unbind().show().click(function(){
                    // 'p' is the selected category;
                    if(p.subcategories.length > 0){
                        // if it has no children, show its parent
                        if(p.parent) p.parent.click_action();
                        else p.list.home_button_action();
                    }
                    else{
                        // if it has children, show its parent's parent
                        if(p.parent.parent) p.parent.parent.click_action();
                        else p.list.home_button_action();
                    }
                });
            }
        }
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