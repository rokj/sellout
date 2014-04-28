Terminal = function(g){
    var p = this;

    p.g = g;
    
    p.items = {
        manage_bar: $("#manage_bar"),

        bill: $("#bill_scroll_outer"),

        till: $("#till"),
        bill_header: $("#bill_header"),
        bill_summary: $("#bill_summary"),
        bill_actions: $("#bill_actions"),

        splitter: $("#splitter"),

        selector: $("#selector"),
        categories: $("#categories"),
        products: $("#products_scroll_outer"),
        controls: $("#controls")
    };

    //
    // methods
    //
    p.size_layout = function(save){
        /* fixed layout, positioned 100% by javascript:
        __________ manage_bar__________
        bill header  | sp | categories |
        bill         | li | products   |
        till         | t  |            |
        bill_summary | t  | ___________|
        bill_actions | er | controls   | */

        var window_height = $(window).height();
        var window_width = $(window).width();

        // manage bar: height is defined with css
        var manage_height = p.items.manage_bar.height();
        p.items.manage_bar.width(window_width); // width is 100%

        // splitter: if it is pushed away further than the width of window, reset it
        var sp = p.g.config.bill_width;
        if(sp > $(window).width()){
            // a reasonable default
            sp = $(window).width() / 4;
        }

        p.items.splitter.offset({ top: manage_height, left: sp });
        p.items.splitter.height(window_height - manage_height);
        var splitter_left = sp + p.items.splitter.width();

        // till
        var till_height = p.items.till.height();
        p.items.till.offset({left: 0, top: window_height - till_height});
        p.items.till.width(sp);

        // bill header
        var header_height = p.items.bill_header.height();
        p.items.bill_header.offset({top: manage_height, left: 0});
        p.items.bill_header.width(sp);

        // bill
        p.items.bill.offset({ top: manage_height + header_height, left: 0 });
        p.items.bill.height(window_height - manage_height - till_height - header_height);
        p.items.bill.width(sp);

        // controls
        var controls_height = p.items.controls.height();
        p.items.controls.offset({ top: window_height - controls_height, left: splitter_left });
        p.items.controls.width(window_width - splitter_left);

        // selection
        p.items.selector.offset({left: splitter_left, top: manage_height});
        p.items.selector.width(window_width - splitter_left);
        p.items.selector.height(window_height - manage_height - controls_height);

        // categories
        var categories_height = p.items.categories.height();

        // products
        p.items.products.offset({left: splitter_left});
        p.items.products.width(window_width - splitter_left);
        p.items.products.height(window_height - manage_height - controls_height - categories_height);

        // refresh if necessary
        if(p.g.objects.products) p.g.objects.products.refresh();

        // save?
        if(save){
            // get splitter position
            send_data(
                p.g.urls.save_terminal_settings,
                { bill_width: sp },
                p.g.csrf_token, null
            );
        }
    };

    //
    // init
    //

    // splitter
    p.items.splitter // resize on splitter drag and save data
        .css({
            height: $(window).height() - p.items.manage_bar.outerHeight(),
            top: p.items.manage_bar.outerHeight(),
            left: p.g.config.bill_width
        })
        .draggable({
            axis: "x",
            stop: function(){
                var new_width = $(this).offset().left;
                var min_width = parseInt(p.items.bill.css("min-width"));

                // if minimum bill width more than new_width, set to minimum value
                if(min_width > new_width){
                    new_width = min_width;
                }

                p.g.config.bill_width = new_width;
                p.size_layout(true);
            }
        });

    // resize everything now and on resize
    p.size_layout(false); // no need to save on load
    $(window).resize(function(){p.size_layout(false); }); // and no need to save on window resize
};