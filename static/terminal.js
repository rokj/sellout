function load_data(url){
    $("#loading").css({
        width:$(window).width(),
        height:$(window).height()
    });

    get_data(url, function(recv_data){window.data = recv_data;});

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
    
    // resize everything now and on resize
    size_layout();
    $(window).resize(size_layout);
}

function size_layout(){
    var splitter = $("#splitter");
    var pos = splitter.offset();
    var obj;
    
    // splitter
    splitter.height($(window).height() - pos.top);
    // selection
    $("#selection").css({left:pos.left});
    // products
    $("#products").outerHeight(
        $("#controls").offset().top - 
        $("#products").offset().top 
    ).empty(); // if the new height is less than previous, product buttons will break out of their parent
    
    // bill: if wider than pos.left, move it back to show the whole bill
    obj = $("#bill");
    obj.width(pos.left);
    if(obj.width() > pos.left){
        splitter.offset({left:obj.width(), top:pos.top});
        pos = splitter.offset().left;
        size_layout();
    }

    
    save_settings();
}

/* save layout and other after leaving the page */
function save_settings(){
    // get splitter position
    var ld = {};
    ld.bill_width = $("#splitter").position().left;
    
    send_data_blocking(window.data.save_url, ld, window.data.csrf_token, null);
    return true;
}
