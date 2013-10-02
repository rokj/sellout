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
            		'easeOutSine',
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

function products_selector(obj){
	var products_obj = $("#products");
	products_draggable(products_obj); // make the results div draggable
	
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
	criteria = {general_filter:window.items.search_field.val()};
	send_data(window.data.search_products_url, criteria, window.data.csrf_token, show_products);
}

function show_products(data){
	window.items.products_list.empty();

	for(var i = 0; i < data.length; i++){
		window.items.products_list.append(product_button(data[i]));
	}
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