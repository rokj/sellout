Products = function(g){
    var p = this;

    p.g = g;

    p.products = []; // a list of all product objects
    p.products_by_id = {}; // a dictionary {id:<product reference>}

    p.all_ids = [];

    p.items = {
        container: $("#products")
    };

    p.shown_products = null; // will show ids that show_products has shown
    p.no_products_message = $("<div>", {id: "no_products"}).text(gettext("No products found"));

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

    p.empty = function(){
        // remove product buttons
        $(".product-button", p.items.container).remove();
        // and columns that contain it
        $(".products-column", p.items.container).remove();
    };

    p.show_products = function(ids){
        // reset the container's position
        p.items.container.css({left: 0});

        // products: a list of product ids (normally returned from Search())
        p.empty();

        // if there's nothing to show, show the 'no products' message
	    if(ids.length == 0 || p.products.length == 0){
            p.no_products_message.appendTo(p.items.container);
            return;
        }
        else{
            p.no_products_message.detach();
        }

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

        n = Math.floor(div_height/(p_size[1]));
        if(n == 0){
            console.warn("Products div too narrow");
            n = 1;
        }

        for(i = 0; i < ids.length;){
            // create a temp 'column' div
            tmp_div = $("<div>", {"class": "products-column"});
            for(j = 0; j < n; j++){
                // add buttons to that div
                tmp_div.append(
                    p.products_by_id[ids[i]].items.container.show()
                );

                // register events on that button
                p.products_by_id[ids[i]].bind_events();

                i++;
                if(i == ids.length) break;
            }
            p.items.container.append(tmp_div);
        }

        // space product buttons evenly:
        // update: do not do that: maintain consistent margin, set in css
        /*i = Math.floor((div_height - n*p_size[1])/(n+1));
        $("div.product-button", p.items.container)
            .css("margin-bottom", i.toString() + "px")
            .css("margin-right", i + "px");
        */
        // save currently shown products in case of refresh etc.
        p.shown_products = ids;
    };

    p.show_all_products = function(){
        p.show_products(p.all_ids);
    };

    p.refresh = function(){
        if(p.shown_products){
            // there are products to show, just re-show them
            p.show_products(p.shown_products);
        }
        else{
            // there are no products to show, empty the container
            p.empty();
        }

    };

    p.search_to_bill = function(id){
        // same as Product.add_to_bill(), except that it's called from Search() object
        // so that it doesn't have to search for products
        if(id in p.products_by_id){
            p.products_by_id[id].add_to_bill();
        }
        else{
            console.error("Product with this id does not exist: " + id);
        }
    };

    //
    // init
    //
    // initialize all products
    var i, product;
    for(i = 0; i < p.g.data.products.length; i++){
        product = new Product(p, p.g.data.products[i]);

        p.products.push(product);
        p.all_ids.push(p.g.data.products[i].id);
        p.products_by_id[p.g.data.products[i].id] = product;
    }

    // make the div draggable
    set_horizontal_draggable(p.items.container, "div.products-column", p.g.settings.t_easing);
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
        if(p.g.objects.bill) p.g.objects.bill.add_product(p, true);
    };

    p.bind_events = function(){
        p.items.container.unbind();

        // if the product is out of stock,, add a special class
        // this has been removed
        // if(p.data.stock.cmp(Big(0)) <= 0){
        //     p.items.container.addClass("out-of-stock");
        // }
        // else{
            p.items.container.on("click", null, null, function(){
                // if the bill has the 'no-click' class, do nothing
                // (it is being dragged)
                if(p.list.items.container.hasClass("no-click")) return;

                p.add_to_bill();
            });
        // }
    };

    p.update = function(){
        // if the product is out of stock...
        // (disabled)
        // if(p.data.stock.cmp(Big(0)) <= 0){
        //     p.items.container.addClass("out-of-stock");
        // }
        // else{
        //     p.items.container.removeClass("out-of-stock");
        // }
    };

    //
    // init
    //
    // replace all number strings with Big() numbers
    p.data.price = get_number(p.data.price, p.g.config.separator);
    p.data.purchase_price = get_number(p.data.purchase_price, p.g.config.separator);
    p.data.stock = get_number(p.data.stock, p.g.config.separator);
    p.data.tax = get_number(p.data.tax, p.g.config.separator);

    for(var i = 0; i < p.data.discounts.length; i++){ // discounts
        p.data.discounts[i].amount = get_number(
            p.data.discounts[i].amount,
            p.g.config.separator
        );
    }

    // create a 'product' div
    // the square that holds everything
    p.items.container = $("<div>", {"class":"product-button"});
    p.items.container.css({
		width: p.g.config.product_button_size,
		height: p.g.config.product_button_size
	});

    p.items.container.css("background-color", "#" + p.data.color);

    // show light text if background is dark
    if(is_dark(p.data.color)) p.items.container.addClass("dark");

    // if there's an image, show it in image
    p.items.image = $("<div>", {"class": "product-button-image"});
    p.items.image.appendTo(p.items.container);

	if(p.data.image){
        p.items.image.css("background-image", "url(" + p.data.image + ")");
        p.items.container.addClass("no-image"); // so that text will placed in the middle
    }
    else{
        p.items.container.addClass("image");
    }

    p.items.text = $("<div>", {"class": "product-button-text"});
    p.items.text.appendTo(p.items.container);

    p.items.name = $("<p>", {"class":"product-button-name"}).text(p.data.name);
    p.items.name.appendTo(p.items.text);

    /* no code or shortcut is displayed at the moment
    p.items.code = $("<p>", {"class":"product-button-code"}).text(p.data.code);
    p.items.code.appendTo(p.items.text);

    p.items.shortcut = $("<p>", {"class":"product-button-shortcut"}).text(p.data.shortcut);
    p.items.shortcut.appendTo(p.items.text); */

    // out of stock
    // (ignored at the moment)
    // p.items.out_of_stock = $("<div>", {"class": "stock-container"});
    // p.items.out_of_stock.appendTo(p.items.container);

    // add id to access this object via document tree, not javascript
    p.items.container.data({id: p.data.id});

    p.bind_events();

    p.update(); // see what's with this
};