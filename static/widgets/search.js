Search = function(g){
    var p = this;

    p.g = g;

    p.items = {
        field: $("#search_products_filter"),
        submit: $("#search_products_submit")
    };

    // save search results to avoid linear search over and over:
    p.subcategories = {}; // pairs {category_id:[subcategory ids]}
    p.results_by_category = {}; // pairs {category_id:[products list]}
    p.results_by_text = {}; // pairs {search_text:[products list]}

    //
    // methods
    //
    p.search_by_category = function(id){
        // first, check if the id is already in results_by_category;
        if(id in p.results_by_category){
            // return what's there
            return p.results_by_category[id];
        }
        else{
            // if not, create a new entry;
            // a category that has subcategories should include all products from
            // itself AND all subcategories
            var cats = [id];
            if(p.subcategories[id]) cats = cats.concat(p.subcategories[id]);

            // search all products and return those that match the requested category id
            var r = [];
            var q = p.g.data.products;
            var i;

            for(i = 0; i < q.length; i++){
                if(cats.indexOf(q[i].category_id) > -1) r.push(q[i].id);
            }

            p.results_by_category[id] = r;

            return r;
        }
    };

    p.search_by_text = function(text){
        if(text.length == 0) return []; // nothing to search for, nothing to show (really?)

        // keep everything lowercase
        text = text.toLowerCase();

        if(text in p.results_by_text){
            return p.results_by_text[text];
        }
        else{
            var r = [];
            var q = p.g.data.products;

            // do a linear search through all products
            // and search the following fields:
            // name
            // description
            // code
            // shortcut
            // category name
            // ... and return anything that matches
            for(var i = 0; i < q.length; i++){
                if((q[i].name.toLowerCase().indexOf(text) > -1) ||
                   (q[i].description.toLowerCase().indexOf(text) > -1) ||
                   (q[i].code.toLowerCase().indexOf(text) > -1) ||
                   (q[i].shortcut.toLowerCase().indexOf(text) > -1) ||
                   (q[i].category.toLowerCase().indexOf(text) > -1)){

                    r.push(q[i].id);
                }
            }

            // save results for later
            p.results_by_text[text] = r;
            return r;
        }
    };

    p.init_subcategories = function(){
        // create a p.subcategories dictionary:
        // p.g.data.categories is in format:
        //  [category
        //        <other data>
        //        children: [category, category]
        //   category
        //        <other data>
        //        children: [category
        //                    <other data>
        //                    children: [... etc]
        //                  ]
        //   category]
        //
        // etc.
        // first, put all categories in a flat list
        var flat = {};
        function make_flat_list(cats){
            for(var i = 0; i < cats.length; i++){
                flat[cats[i].id] = cats[i].parent_id;
                make_flat_list(cats[i].children);
            }
        }
        make_flat_list(p.g.data.categories);
        // the list now contains
        // {<id>:<parent>, 2:1, 3:1, 4:3, 5:3}
        // but we need:
        // {<id>:[<children>], 1:[2,3], 3:[4,5]}
        // that's inverted dictionary
        var key, new_key;

        for(key in flat) {
            if(flat.hasOwnProperty(key)){
                // make sure it's an integer (keys are converted to strings... obviously)
                new_key = flat[key];
                if(!new_key) new_key = -1; // no parent
                else new_key = parseInt(new_key);

                key = parseInt(key);

                // don't just invert, make new values arrays
                // and push if it exists
                if(new_key in p.subcategories) p.subcategories[new_key].push(key);
                else p.subcategories[new_key] = [key];
            }
        }
        // now add subcategories to parents, that is:
        // {1:[2,3,4,5], 3:[4,5]}
        var i, j,
            cats, // current category's children
            children, // children's children
            l, m; // lengths of list (current and previous

        // loop over all categories
        for(key in p.subcategories){
            if(p.subcategories.hasOwnProperty(key)){
                cats = p.subcategories[key];
                l = cats.length;
                m = -1;

                // find categories that are children of each of this category's
                // children and add them;
                // iterate over this list as long as it's changing
                // (that's adding subsubsubsub...categories as long as they're there)
                while(l != m){
                    m = l;

                    for(i = 0; i < cats.length; i++){
                        // get that category's children
                        children = p.subcategories[cats[i]];

                        if(!children) continue;

                        // add them to this category's list
                        for(j = 0; j < children.length; j++){
                            if(cats.indexOf(children[j]) == -1)
                                cats.push(children[j]);
                        }
                    }

                    l = cats.length;
                }

                m = -1;
            }
        }
    };

    //
    // init
    //
    // firefox (and other browsers as well) remember last entered data, clear it
    p.items.field.val("");

    p.init_subcategories();

    // events
    p.items.submit.click(function(){
        p.g.objects.products.show_products(
            p.search_by_text(p.items.field.val())
        );
    });
    p.items.field.change(function(){
        p.g.objects.products.show_products(
            p.search_by_text($(this).val())
        );
    });

};