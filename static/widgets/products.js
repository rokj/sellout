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
	// create a 'product' div
	// show: name, code, shortcut and background image
	// gray out if there's no products left
	var div = $("<div>", {"class":"product-button"});
	div.css({
		width:window.data.product_button_size,
		height:window.data.product_button_size
	});
	if(product.image){
        div.append($("<img>", {src:product.image, "class":"product-button-image"}));
    }

    info_div = $("<div>", {"class":"shade"});

	var name = $("<p>", {"class":"product-button-name"});
	name.append(product.name);
	var code = $("<p>", {"class":"product-button-code"});
	code.append(product.code);
	var shortcut = $("<p>", {"class":"product-button-shortcut"});
	shortcut.append(product.shortcut);

    info_div.append(name);
	info_div.append(code);
	info_div.append(shortcut);
    div.append(info_div);

    div.data(product); // everything about the product

    if(get_number(product.stock, window.data.separator).cmp(Big(0)) <= 0){
        info_div.addClass("out-of-stock");
        // this product cannot be clicked
    }
    else{
        div.click(select_product);
    }

	return div;
}

function select_product(){
    // $(this) is the product div
    // 'unstyle' any currently selected product
    // change style
    // show the product's category
    $(".product-button-focused").removeClass("product-button-focused");
    $(this).addClass("product-button-focused");

    select_category(null, $(this).data().category_id)
    
    // on click: add this item to bill (or increase quantity of existing item by 1)
    // $(this).data() is the product itself
    window.bill.add_product($(this).data());
}
