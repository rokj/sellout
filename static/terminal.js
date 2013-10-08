function load_data(url){
	$("#loading").css({
		width:$(window).width(),
		height:$(window).height()
	});

    get_data(url,
    		function(recv_data){window.data = recv_data;});

}

/* sizing of elements */
function init_layout(){
	// splitter
	$("#splitter")	
		.draggable({
			axis:"x",
			stop:size_layout
		})
		.css({
			height:$(window).height() - $("#manage_bar").outerHeight(),
			top:$("#manage_bar").outerHeight(),
			left:window.data.bill_width
		});

	// bill
	$("#bill").width(window.data.bill_width);
	
	// products
	$("#products").height(
		// 
			300
	);

	// resize everything now and on resize
	size_layout(); $(window).resize(size_layout);
}

function size_layout(){
	var obj = $("#splitter");
	var pos = obj.position().left;
	
	// splitter
	obj.height($(window).height() - obj.position().top);
	// bill width
	$("#bill").width(pos);
	// selection
	$("#selection").css({left:pos});
	// products
	$("#products").outerHeight(
		$("#controls").offset().top - 
		$("#products").offset().top 
	).empty(); // if the new height is less than previous, product buttons will break out of their parent
}

/* save layout and other after leaving the page */
function save_settings(){
	// get splitter position
	var ld = {};
	ld.bill_width = $("#splitter").position().left;
	
	send_data_blocking(window.data.exit_url, ld, window.data.csrf_token, null);
	return true;
}

/* keyboard */
function handle_keypress(e){
	var code = (e.keyCode ? e.keyCode : e.which);

	if(!window.focused_item){
		window.focused_item = $(".category-button").filter(":first"); // assign the first item (only in the beginning)
		// if nothing is selected, any key must select something, so override 'code'
		code = 39;
	}

	var prev_item, next_item;

	// left: 37 up: 38 right: 39 down: 40
	switch(code){
		case 37: // left
			// get the previous one
			prev_item = window.focused_item.data().prev;
			if(!prev_item) prev_item = window.focused_item.data().last; // jump to the first item

			window.focused_item = prev_item;
			window.focused_item.click();
			break;
		case 38: // up
			prev_item = window.focused_item.data().parent;
			if(prev_item){
				prev_item.data().child = window.focused_item; // rememver the last selected child
				
				window.focused_item = prev_item;
				window.focused_item.click();
			}
			break;
		case 39: // right
			next_item = window.focused_item.data().next;
			if(!next_item) next_item = window.focused_item.data().first; // jump to the first item

			window.focused_item = next_item;
			window.focused_item.click();
			break;
		case 40: // down
			next_item = window.focused_item.data().child;
			if(next_item){
				window.focused_item = next_item; // select sub-item
				window.focused_item.click();
			}
			else{ // jump to products selector
				alert("products!");
			}
			break;
		default: return;
	}
}