Terminal = function(g){
    var p = this;

    p.g = g;
    
    p.items = {
        splitter: $("#splitter"),
        manage_bar: $("#manage_bar"),
        bill: $("#bill"),
        products_container: $("#products"),
        selector_container: $("#selector"),
        controls_container: $("#controls")
    };

    //
    // methods
    //
    p.size_layout = function(save){
        var pos = p.items.splitter.offset();

        // splitter
        p.items.splitter.height($(window).height() - pos.top);
        // selection
        p.items.selector_container.css({left:pos.left});
        // products
        p.items.products_container.outerHeight(
            p.items.controls_container.offset().top -
            p.items.products_container.offset().top
        ).empty(); // if the new height is less than previous, product buttons will break out of their parent

        // bill: if wider than pos.left, move it back to show the whole bill
        p.items.bill.width(pos.left);
        if(p.items.bill.width() > pos.left){
            p.items.splitter.offset({left: p.items.bill.width(), top: pos.top});
            p.size_layout();
            return;
        }

        // save?
        if(save){
            // get splitter position
            var ld = {};
            ld.bill_width = p.items.splitter.position().left;

            send_data(p.g.urls.save_terminal, ld, p.g.csrf_token, null);
        }
    };

    //
    // init
    //

    // splitter
    p.items.splitter // resize on splitter drag and save data
        .draggable({ axis: "x", stop: function(){p.size_layout(true); }})
        .css({
            height: $(window).height() - p.items.manage_bar.outerHeight(),
            top: p.items.manage_bar.outerHeight(),
            left: p.g.config.bill_width
        });
    p.items.bill.width(p.g.config.bill_width);

    // resize everything now and on resize
    p.size_layout(false); // no need to save on load
    $(window).resize(function(){p.size_layout(false); }); // and no need to save on window resize

};