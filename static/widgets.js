/* categories selector */
function categories_selector(div, categories){
	// add a div and add categories from 'categories' to it. for each 'child' category, do everything again
	var category_div = $("<div>", {"class":"scrollyeah"});
	div.append(category_div);
	
	// create parent categories
	function add_category(parent, cat_data){
		// create a custom button for category
		// it's a div
	    var btn_obj = $("<div>", {"class":"category-select"});
	    
	    var p_obj = $("<p>", {"class":"category-name"});
	    btn_obj.append(p_obj);
	    
	    // add an image, if it has one
	    var img_obj = $("<img>", {"class":"category-select-icon"});
	    
	    if(cat_data.image) img_obj.attr("src", cat_data.image);
	    else img_obj.attr("src", data['spacer']); // data is a global variable, set in terminal.html
	    p_obj.append(img_obj); // add image
	    
	    // add name to a new div
	    p_obj.append(cat_data.name);
	    
	    // data contains everything about this category
	    btn_obj.data(cat_data);
	    
	    parent.append(btn_obj);
	    
	    return p_obj;
	}

	// first, the 'no category' button
	var no_category = {name:gettext("No Category"), id:-1};
	add_category(category_div, no_category).addClass("category-select-none");
	
	for(var i = 0; i < categories.length; i++){
		add_category(category_div, categories[i]);
		if(categories[i].children.length > 0){
			categories_selector(div, categories[i].children);//.hide();
		}
	}
	
	return category_div;
}

function handle_keypress(e){
	// left: 37 up: 38 right: 39 down: 40
	
}