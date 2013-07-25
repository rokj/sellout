function send_data(url, data, token, handleFun){
  var sd = {data:JSON.stringify(data), csrfmiddlewaretoken:token}
  $.post(url,
    sd,
      function(retData){
        handleFun(retData);
      }, "json"); 
  return false;
}

function get_data(url, handleFun){
  $.ajax({
    type:"GET",
    dataType: "json",
    url:url,
    async:false,
    success:function(data){handleFun(data);}
  });
  return false;
}
