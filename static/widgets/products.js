Products = function(g){
    var p = this;

    p.g = g;

    p.products = []; // a list of all product objects
    p.products_by_id = {}; // a dictionary {id:<product reference>}

    p.items = {
        container: $("#products")
    };

    //
    // methods
    //
    p.sort_products = function(products, sort_by){
        products.sort(function(p1, p2){
            switch(sort_by){
                case 'name':
                default: // sort by name by default
                    return p.products_by_id[p1].data.name
                        .localeCompare(p.products_by_id[p2].data.name);
                    break;
            }
        });

        return products;
    };

    p.show_products = function(ids){
        // products: a list of product ids (normally returned from Search())
        p.items.container.empty();

	    if(ids.length == 0) return;
        if(p.products.length == 0) return;

        p.sort_products(ids, null);

	    // put products in the div:
	    // list them in columns, first down then right to next column
	    var i, j, // loop indexes: i - current product index, j - index in current column
    		n, // number of products in one column
    		div_height, // height of #products div
    		p_size, // size [width, height] of a product button
    		tmp_div; // a 'column' div

	    div_height = p.items.container.height();
	    p_size = get_size(p.products[0].items.container); // there's at least one product in the list

        n = Math.floor(div_height/p_size[1]);
        for(i = 0; i < ids.length;){
            // create a temp 'column' div
            tmp_div = $("<div>", {"class": "products-column"});
            for(j = 0; j < n; j++){
                // add buttons to that div
                tmp_div.append(
                    p.products_by_id[ids[i]].items.container.clone().show()
                );

                i++;
                if(i == ids.length) break;
            }
            p.items.container.append(tmp_div);
        }

        // space product buttons evenly:
        i = Math.floor((div_height - n*p_size[1])/(n+1));
        $("div.product-button", p.items.container)
            .css("margin-top", i.toString() + "px")
            .css("margin-bottom", i.toString() + "px")
            .css("margin-left", Math.floor((i/2).toString()) + "px")
            .css("margin-right", Math.floor((i/2).toString()) + "px");
    };

    //
    // init
    //
    // initialize all products
    var i, product;
    for(i = 0; i < p.g.data.products.length; i++){
        product = new Product(p, p.g.data.products[i]);
        p.products.push(product);
        p.products_by_id[p.g.data.products[i].id] = product;
    }

    // make the div draggable
    set_draggable(p.items.container, "div.products-column", p.g.settings.t_easing);
};

Product = function(list, data){
    var p = this;

    p.list = list;
    p.g = p.list.g;

    p.data = data;

    p.items = {}; // will be filled on init

    //
    // methods
    //
    p.add_to_bill = function(){
        p.g.objects.bill.add_product(p);
    };


    //
    // init
    //

    // create a 'product' div
	// show: name, code, shortcut and background image
	// gray out if there's no products left
    p.items.container = $("<div>", {"class":"product-button"});
    p.items.container.css({
		width: p.g.config.product_button_size,
		height: p.g.config.product_button_size
	});

	if(p.data.image){
        p.items.container.append($("<img>", {src: p.data.image, "class":"product-button-image"}));
    }

    p.items.info = $("<div>", {"class":"shade"});
    p.items.name = $("<p>", {"class":"product-button-name"}).text(p.data.name);
    p.items.code = $("<p>", {"class":"product-button-code"}).text(p.data.code);
    p.items.shortcut = $("<p>", {"class":"product-button-shortcut"}).text(p.data.shortcut);

    p.items.info
        .append(p.items.name)
	    .append(p.items.code)
        .append(p.items.shortcut);

    p.items.container.append(p.items.info);

    // if the product is out of stock,, add a special class
    if(get_number(p.data.stock, p.g.config.separator).cmp(Big(0)) <= 0){
        p.items.info.addClass("out-of-stock");
        // this product cannot be clicked
    }
    else{
        p.items.container.click(function(){console.log("click")});
    }

    // add id to access this object via document tree, not javascript
    p.items.container.data({id: p.data.id});
};

function select_product(){
    select_category(null, $(this).data().category_id)
    
    // on click: add this Item to Bill (or increase quantity of existing Item by 1)
    // $(this).data() is the product itself
    window.bill.add_product($(this).data());
}
