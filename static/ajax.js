// sending 
function send_data(url, data, token, handleFun){
    var sd = {data:JSON.stringify(data), csrfmiddlewaretoken:token};
    $.post(
        url,
        sd,
        function(retData){
            if(handleFun) handleFun(retData);
  		},
  		"json"
    );
}

// receiving
function get_data(url, handleFun){
	$.ajax({
		type: "GET",
		dataType: "json",
		url: url,
		async: false,
		success: function(data){
            if(handleFun) handleFun(data);
        }
	});
}