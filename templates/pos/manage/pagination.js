/* this must be included inside $(document).ready() code */

// intercept back and forward links for paginator; update the form and submit it
$("a.fake.paginator").unbind().click(function(e){
    e.preventDefault();

    if($(this).hasClass("disabled")) return;

    var page_obj = $("#id_page");
    var page = parseInt(page_obj.val());

    if(isNaN(page)){
        page = 1;
    }
    else{
        if($(this).attr("data-action") == "next") page += 1;
        else page -= 1;
    }

    page_obj.val(page);
    $("#filter_form").submit();
});

// when any of search parameters change, reset the page back to 1
$("input", "#filter_form").change(function(){
    $("#id_page").val(1);
});