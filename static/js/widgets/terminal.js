Terminal = function(g){
    var p = this;

    p.g = g;
    
    p.items = {
        status_bar: $("#status_bar"),
        status_bar_company: $("#status_bar_company"),

        left_column: $("#left_column"),
        bill_container: $("#bill_container"),

        till: $("#till"),
        bill_header: $("#bill_header"),

        splitter: $("#splitter"),

        selector: $("#selector"),
        categories: $("#categories"),
        products: $("#products_scroll_outer"),
        products_title: $("#products_title"),
        controls: $("#controls"),

        registers_dialog: $("#registers"),
        registers_list: $("#registers_list"),
        select_register: $("#select_register"),

        current_till: $("#current_till")
    };

    // bill sizes (in pixels):
    // showing columns:
    // width 1 (narrowest):
    //     - name
    //     - quantity
    //     - price
    //     - subtotal
    // width 2:
    //     added tax
    // width 3 (widest):
    //     added discount
    p.bill_sizes = [350, 450, 600];

    // register: will point to a register object in g.data.registers
    p.register = null;

    //
    // methods: sizing and layout
    //
    p.size_layout = function(save){
        // position: #bill_container, #splitter, #selector
        var window_height = $(window).height();
        var window_width = $(window).width();

        // manage bar: height is defined with css
        var manage_height = p.items.status_bar.height();

        // splitter: if it is pushed away further than the width of window, reset it
        var sp = p.g.config.bill_width;
        if(sp > $(window).width()){
            // a reasonable default
            sp = $(window).width() / 3.3;
        }

        p.items.splitter.offset({ top: manage_height, left: sp });
        p.items.splitter.height(window_height - manage_height);
        var splitter_width = p.items.splitter.width();
        var splitter_left = sp + splitter_width;

        // left column: according to splitter
        p.items.left_column.offset({ top: manage_height, left: 0 });
        p.items.left_column.height(window_height - manage_height);
        p.items.left_column.width(sp - splitter_width);

        // bill container
        p.items.bill_container.css("top", p.items.bill_header.outerHeight() + "px");
        p.items.bill_container.css("bottom", p.items.till.outerHeight() + "px");

        // controls
        var controls_height = p.items.controls.height();
        p.items.controls.offset({ top: window_height - controls_height, left: splitter_left });
        p.items.controls.width(window_width - splitter_left);

        // selection
        p.items.selector.offset({left: splitter_left , top: manage_height});
        p.items.selector.width(window_width - splitter_left);
        p.items.selector.height(window_height - manage_height - controls_height);

        // categories
        var categories_height = p.items.categories.height();

        // products
        p.items.products.width(window_width - splitter_left);
        p.items.products.css("top", p.items.categories.outerHeight() + p.items.categories.position().top);

        // refresh if necessary
        if(p.g.objects.products) p.g.objects.products.refresh();

        // show or hide bill columns
        p.size_bill();

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

    p.size_bill = function(){
        var bw = p.g.config.bill_width;

        if(bw <= p.bill_sizes[0]){
            // hide tax and discount columns (hiding is done in css)
            // size columns (css only)
            $().add(p.items.bill_header).add(p.items.bill_container)
                .removeClass("medium wide").addClass("narrow");

        }
        else if(bw > p.bill_sizes[0] && bw < p.bill_sizes[1]){
            // show tax column
            $().add(p.items.bill_header).add(p.items.bill_container)
                .removeClass("narrow wide").addClass("medium");
        }
        else{
            // show tax and discounts column
            $().add(p.items.bill_header).add(p.items.bill_container)
                .removeClass("narrow medium").addClass("wide");
        }
    };

    p.set_register = function(r){
        if(!r){
            console.log("No register set");
            return;
        }

        // the register must be set (p.register)
        p.register = r;

        p.items.current_till.text(p.register.name);

        // TODO: ?
    };

    p.get_register = function(id){
        if(p.g.data.registers.length == 0){
            alert(gettext("There are no registers defined, please add one"));
            window.location.href = p.g.urls.manage_registers;
        }

        if(id){
            // the id is set already, just find the right one in the list
            var i, selected = false;

            for(i = 0; i < p.g.data.registers.length; i++){
                if(p.g.data.registers[i].id == id){
                    p.set_register(p.g.data.registers[i]);
                    selected = true;
                    break;
                }
            }

            if(!selected){
                error_message(
                    gettext("Register could not be set"),
                    gettext("There was an error while setting your register, " +
                        "the first available register settings will be used")
                );

                p.set_register(p.g.data.registers[0]);
            }

            return;
        }

        // at this point, prompt the user to choose one
        if(!p.register){
            // bind the choose button
            p.items.select_register.unbind().click(function(){
                // get the selected register id from the list
                var id = parseInt(p.items.registers_list.val());
                if(isNaN(id)) id = -1; // the first register will be chosen

                // call this function again, with (more or less) known id
                p.get_register(id);

                // close the dialog
                p.items.registers_dialog.dialog("destroy");

                // send the register to the server so that it will be remembered
                send_data(p.g.urls.set_register, {id: p.register.id},
                    p.g.csrf_token, function(response){
                        if(response.status != 'ok'){
                            // just log the response the console;
                            // if this fails, the only nuissance for the user is
                            // to select the register at next logon
                            console.error("Could not set register: " + response.message);
                        }
                    });
            });

            // show the registers dialog
            p.items.registers_dialog.dialog({
                title: gettext("Choose a register"),
                closeOnEscape: false,
                modal: true,
                // the dialog can only close on 'select' button
                beforeClose: function(){ return false; },
                dialogClass: "no-close"
            });
        }
    };

    //
    // init
    //

    // splitter
    p.items.splitter // resize on splitter drag and save data
        .css({
            height: $(window).height() - p.items.status_bar.outerHeight(),
            top: p.items.status_bar.outerHeight(),
            left: p.g.config.bill_width
        })
        .draggable({
            axis: "x",
            stop: function(){
                var new_width = $(this).offset().left;
                var min_width = parseInt(p.items.bill_container.css("min-width"));

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

    // convert all stringed numbers to Big() numbers
    // discounts:
    var d = p.g.data.discounts;
    for(var i = 0; i < d.length; i++){
        d[i].amount = get_number(d[i].amount, p.g.config.separator);
    }

    // load company's logo and store it to terminal
    if(p.g.data.receipt_logo)
        p.g.items.receipt_logo = $("<img>", {src: p.g.data.company.receipt_logo});

    // get register
    p.get_register(p.g.config.register_id);

    // set status bar title
    p.items.status_bar_company.text(p.g.data.company.name);
};