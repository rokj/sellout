/* products selector */
function products_draggable(obj) {
	var params = {
		// Kudos:
		// http://stackoverflow.com/questions/6602568/jquery-ui-draggable-deaccelerate-on-stop
        helper: function(){
            return $('<div></div>').css('opacity',0);
        },
        drag: function(event, ui){
            var p = ui.helper.position();
            $(this).stop().animate(
            		{ left: p.left },
            		window.data.t_easing,
            		'easeOutCirc',
            		function(){
        				// check if this has scrolled past the last button
            			/*first_button = $(".category-button", obj).filter(":first").data().first;
            			last_button = $(".category-button", obj).filter(":first").data().last;
            			container = $("div#selection");

            			// either left border is inside the scroll area or 
            			if(first_button.offset().left > container.offset().left || first_button.parent().outerWidth() < container.width()){
            				first_button.parent().animate({left:0}, "fast");
            			}
            			else if(last_button.offset().left + last_button.outerWidth() < container.offset().left + container.width()){
		    				first_button.parent().animate({left:-last_button.position().left + container.width() - last_button.outerWidth()}, "fast");
            			}*/

            		});
        },
        axis:"x"
    }

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

function get_products(){
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
	for(i = 0; i < pl.length; i++){
		// create a temp 'column' div
		tmp_div = $("<div>", {"class":"products-column"});
		for(j = 0; j < n, i < pl.length; j++){
			// add buttons to that div
			tmp_div.append(product_button(pl[i]));
			i++;
		}
		window.items.products_list.append(tmp_div);
	}
	
	// space product buttons evenly:
	i = (div_height - n*p_size[1])/(n+1);
	$("div .product-button")
		.css("margin-top", i.toString() + "px")
		.css("margin-bottom", i.toString() + "px")
		.css("margin-left", (i/2).toString() + "px")
		.css("margin-right", (i/2).toString() + "px");
}

function product_button(product){
	// create a 'product' div
	// show: dimensions, name, code, and background image
	var div = $("<div>", {"class":"product-button"});
	div.css({
		width:window.data.product_button_size,
		height:window.data.product_button_size,
	});
	if(product.image) backgroundImage:"url("+product.image+")"

	var name = $("<p>", {"class":"product-button-name"});
	name.append(product.name);
	var code = $("<p>", {"class":"product-button-code"});
	code.append(product.code);
	var shortcut = $("<p>", {"class":"product-button-shortcut"});
	shortcut.append(product.shortcut);
	
	div.append(name);
	div.append(code);
	div.append(shortcut);
	
	return div;
}