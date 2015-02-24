Categories = function(g){
    var p = this;

    p.g = g;

    p.categories = []; // will hold Category() objects
    p.categories_by_id = {}; // will hold pairs id:{category reference} for faster searching

    p.section = $("#categories"); // terminal section
    p.items = {
        parents: $("#parents"), // parent categories
        children: $("#children"), // children categories

        home_button: $("#category_button_home"),
        favorites_button: $("#category_button_favorites"),
        back_button: $("#category_button_back"),

        subcategories_title: $("#subcategories_title"),
        products_title: $("#products_title")
    };

    //
    // methods
    //
    p.set_texts = function(showing, has_children){
        // showing:
        // 1: showing a category
        // 2; home button
        // 3: favorites button

        switch(showing){
            case 1: // a normal (sub)category
                p.items.products_title.text(gettext("Products in this category"));

                break;
            case 2: // home button
                p.items.products_title.text(gettext("All products"));

                p.items.subcategories_title.text(gettext("Categories"));
                break;
            case 3:
                p.items.products_title.text(gettext("Favorite products"));

                p.items.subcategories_title.text(gettext("Categories"));
                break;
        }

        if(has_children) p.items.subcategories_title.text(gettext("Subcategories"));
        else p.items.subcategories_title.text(gettext("No Subcategories"));
    };

    p.clear_parents = function(){ $("div.category-button", p.items.parents).hide(); };

    p.clear_children = function(){ $("div.category-button", p.items.children).hide(); };

    p.clear = function(){
        p.clear_parents();
        p.clear_children();
    };

    p.favorites_button_action = function(show_all){
        // clear everything first
        p.clear();

        // show only top categories in children div
        for(var i = 0; i < p.categories.length; i++){
            p.categories[i].children_button.show();
        }

        // hide the back button if displaying breadcrumbs
        if(!p.g.config.display_breadcrumbs){
            toggle_element(p.items.back_button, false);
        }

        if(show_all){
            // display all products
            p.g.objects.search.show_all_products();
            p.set_texts(2, p.categories.length != 0); // showing favorites
        }
        else{
            // display only favorites
            p.g.objects.search.show_favorites();
            p.set_texts(3, p.categories.length != 0); // showing favorites
        }
    };

    //
    // init
    //
    if(p.g.config.display_breadcrumbs) p.section.parent().addClass("breadcrumbs");
    else p.section.parent().addClass("no-breadcrumbs");

    // draggable parents and children
    if(p.g.config.display_breadcrumbs){
        set_horizontal_draggable(p.items.parents, "div.category-button:visible", p.g.settings.t_easing);
    }
    set_horizontal_draggable(p.items.children, "div.category-button:visible", p.g.settings.t_easing);

    // create all top-level categories
    var i, c;
    c = p.g.data.categories;
    for(i = 0; i < c.length; i++){
        p.categories[i] = new CategoryButton(p, null, c[i]);
    }

    // home button action
    p.items.home_button.click(function(){
        p.favorites_button_action(true);
    });

    // favorites button action
    p.items.favorites_button.click(function(){
        p.favorites_button_action(false);
    });
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
    p.parents_button = null; // the button in the parents div

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

        // category color
        p.button.css("background-color", "#" + p.data.color);
        p.button.css("border-left-color", "#" + p.data.color); // so that :after pseudo-class will inherit it
        // text color
        if(is_dark(p.data.color)){
            p.button.addClass("dark");
        }

        // appending: in parents div, prepend (subcategory is the last to be shown)
        //            in children, append (sorted by name, alphabetically)

        // append to children div
        p.children_button = p.button.clone().appendTo(p.list.items.children);

        // append to parents div only if it has subcategories
        p.parents_button = p.button.clone().prependTo(p.list.items.parents);
        p.parents_button.addClass("has-subcategories");
    };

    p.show_children = function(){
        if(p.g.config.display_breadcrumbs){
            // TODO (if, that is)
            console.warn("Not implemented: display breadcrumbs");

            /*
            // show parents: if display_breadcrumbs is on
            if(p.g.config.display_breadcrumbs){
                var z = 1;

                var c = p;
                while(c){
                    if(c.parents_button){
                        c.parents_button.show();
                        c.parents_button.css("z-index", z);
                        z += 1;
                    }
                    c = c.parent;
                }

                // adjust z-index of all visible parent

            }
            */
        }
        else{
            // remove current children
            p.list.clear();

            // show all buttons of all subcategories (if there's any)
            for(var i = 0; i < p.subcategories.length; i++){
                p.subcategories[i].children_button.show();
            }

            // if display_breadcrumbs is off, show only this category's parent and back button
            p.parents_button.show();

            // show the back button (unless showing breadcrumbs)
            // and bind an action to it
            toggle_element(p.list.items.back_button, true);
            p.list.items.back_button.unbind().click(function(){
                // 'p' is the selected category;
                if(p.parent) p.parent.click_action();
                else p.list.favorites_button_action();
            });
        }
    };

    p.click_action = function(){
        // if the parent has the 'no-click' class, do nothing
        // (it's being dragged)
        if(p.list.items.parents.hasClass("no-click") ||
           p.list.items.children.hasClass("no-click")){
            return;
        }

        // show children
        p.show_children();

        // show products from this category
        p.g.objects.products.show_products(
            p.g.objects.search.search_by_category(p.data.id)
        );

        p.list.set_texts(1, p.has_children); // not showing favorites anymore
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
    $().add(p.parents_button)
       .add(p.children_button)
       .click(p.click_action);
};