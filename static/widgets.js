
/* categories selector */
function categories_selector(div, categories){
	// create container div for scrollyeah
	div.empty();
	
	// create parent categories
	function add_category(parent, cat_data){
	    div_obj = $("<div>", {"class":"category"});
	    div_obj.data(cat_data);
	    div_obj.append(cat_data.name);
	    
	    parent.append(div_obj);
	}

	// first, the 'no category' button
	
	
	for(var i = 0; i < categories.length; i++){
		add_category(div, categories[i]);
	}
	
	// initialize the scrollyeah on the new div
	reinit();
}