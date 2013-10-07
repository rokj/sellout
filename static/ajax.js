// sending 
function send_data(url, data, token, handleFun){
	if(window.request){
		window.request.abort();
		window.request = null;
	}
	
    var sd = {data:JSON.stringify(data), csrfmiddlewaretoken:token}
    window.request = $.post(url,
        sd,
        function(retData){
        	handleFun(retData);
  		},	
  		"json");
	
	return false;
}

function send_data_blocking(url, data, token, handleFun){
	if(window.request){
		window.request.abort();
		window.request = null;
	}
	
	var sd = {data:JSON.stringify(data), csrfmiddlewaretoken:token}
	window.request = $.ajax({
		async:true,
		type: "POST",
		url: url,
		data: sd,
		dataType: "json"
	});
	return false;
}

// receiving
function get_data(url, handleFun){
	if(window.request){
		window.request.abort();
		window.request = null;
	}
	window.request = $.ajax({
		type:"GET",
		dataType: "json",
		url:url,
		async:false,
		success:function(data){handleFun(data);}
	});
	return false;
}