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
    p.show_products = function(products){
        // products: a list of product ids (normally returned from Search())
        console.log(products)

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


/* products draggable with easing */
function products_draggable(obj) {
    var params = {
        // Kudos:
        // http://stackoverflow.com/questions/6602568/jquery-ui-draggable-deaccelerate-on-stop
        helper: function () {
            return $("<div>").css("opacity", 0);
        },
        drag: function (event, ui) {
            var pos = ui.helper.position().left - obj.parent().position().left;
            $(this).stop().animate({left: pos},
                window.data.t_easing,
                'easeOutCirc',
                function() {
	                // see categories.js for more info
	                var first_button = $("div.products-column", obj).filter(":first");
	                var last_button = $("div.products-column", obj).filter(":last");
	                var container = obj.parent();

                    if(first_button.length < 1 || last_button.length < 1) return;


	                if (first_button.position().left + last_button.position().left + last_button.outerWidth() < container .width()) {
	                    first_button.parent().animate({left:0}, "fast");
	                }
	                else{
	                    if(first_button.offset().left > container.offset().left){
	                    	first_button.parent().animate({left:0}, "fast");
	                    }
	                    else if(last_button.offset().left+ last_button.outerWidth() < container.offset().left + container.width()) {
	                    	first_button.parent().animate({left:-last_button.position().left + container.width() - last_button.outerWidth()}, "fast");
	                    }
	                }
	            });

        },
        axis: "x"
    };

    obj.draggable(params);
}

function products_selector(){
	products_draggable(window.items.products_list); // make the results div draggable
	
	// check if products search box has changed on fixed interval
	var s_int = self.setInterval(function(){
		var  s = window.items.search_field.val();
		if(s != window.data.last_search){
			if(s.replace(" ", "") != '') get_products();
			window.data.last_search = s;
		}
	}, window.data.search_update_interval);
	window.items.search_field.val()
}

function get_products(category_id){
    // send JSON: {general_filter:#search_products_filter.val()} to data['search_url']
    var criteria = {general_filter:window.items.search_field.val()};

	send_data(window.data.search_products_url, criteria, window.data.csrf_token, show_products);
}

function show_products(pl){
	
	window.items.products_list.empty();
	if(pl.length == 0){
		return;
	}
	
	// put products in the div:
	// list them in columns, first down then right to next column
	var i, j, // loop indexes: i - current product index, j - index in current column
		n, // number of products in one column
		div_height, // height of #products div
		p_size, // size [width, height] of a product button
		tmp_div; // a 'column' div
		
	div_height = window.items.products_list.height();
	p_size = get_size(product_button(pl[0])); // there's at least one product in the list 
	
	n = Math.floor(div_height/p_size[1]);
	i = 0;
	for(i = 0; i < pl.length;){
		// create a temp 'column' div
		tmp_div = $("<div>", {"class":"products-column"});
		for(j = 0; j < n; j++){
			// add buttons to that div
			tmp_div.append(product_button(pl[i++]));
            if(i == pl.length) break;
		}
		window.items.products_list.append(tmp_div);
	}
	
	// space product buttons evenly:
	i = Math.floor((div_height - n*p_size[1])/(n+1));
	$("div .product-button")
		.css("margin-top", i.toString() + "px")
		.css("margin-bottom", i.toString() + "px")
		.css("margin-left", Math.floor((i/2).toString()) + "px")
		.css("margin-right", Math.floor((i/2).toString()) + "px");
}

function product_button(product){

}

function select_product(){
    // $(this) is the product div
    // 'unstyle' any currently selected product
    // change style
    // show the product's category
    $(".product-button-focused").removeClass("product-button-focused");
    $(this).addClass("product-button-focused");

    select_category(null, $(this).data().category_id)
    
    // on click: add this Item to Bill (or increase quantity of existing Item by 1)
    // $(this).data() is the product itself
    window.bill.add_product($(this).data());
}
