Search = function(g){
    var p = this;

    p.g = g;

    p.items = {
        field: $("#search_products_filter"),
        submit: $("#search_products_submit")
    };

    // save search results to avoid linear search over and over:
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
            // if not, create a new entry
            // search all products and return those that match the requested category id
            var r = [];
            var q = p.g.data.products;
            var i;

            for(i = 0; i < q.length; i++){
                if(q.category_id == id) r.append(q.id);
            }

            p.results_by_category[id] = r;

            return r;
        }
    };

    p.search_by_text = function(text){

    };

    //
    // init
    //
    // firefox (and other browsers as well) remember last entered data, clear it
    p.items.field.val("");

    // events
    p.items.submit.click(function(){

    });

};