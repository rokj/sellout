/*

Bill: handles everything regarding billing and bill items, contains items
  Item: data about items, editing, etc.

 */
Bill = function(g){
    var p = this;

    p.g = g;

    p.data = null; // will be fetched in init
    p.items = [];
    p.serial = 0; // a number that will be assigned to every item
                   // (like an unique id - has nothing to do with id on server)

    p.bill_container = $("#bill");

    // summary numbers
    p.summary = $("#bill_summary");
    p.summary_total = $("p.total", p.summary);

    // the 'finish' button
    p.actions = $("#bill_actions");
    p.finish_button = $(".finish-the-fukin-bill", p.actions);

    // save item template for items and remove it from the document
    p.item_template = $("#bill_item_template").detach().removeAttr("id");

    //
    // methods
    //
    // item manipulation
    p.get_item = function(serial){
        // do a linear search for an item with given id
        for(var i = 0; i < p.items.length; i++){
            if(p.items[i].serial == serial){
                return i;
            }
        }
        // nothing was found
        return null;
    };

    p.get_product = function(product_id){
        // returns an index of an item from specified product id

        for(var i = 0; i < p.items.length; i++){
            if(p.items[i].data.product_id == product_id){
                return i;
            }
        }

        return null;
    };

    p.add_product = function(product, to_existing){
        // see if this product is already in the bill;

        if(to_existing == false){
            p.items.push(new Item(p, product));
        }
        else{
            var item_index = p.get_product(product.data.id);

            if(item_index == null){
                // if not, add a new item
                p.items.push(new Item(p, product));
            }
            else{
                // if it is, just update quantity
                p.items[item_index].add_quantity(true);
            }
        }

        p.update_summary();
    };

    p.remove_item = function(item){
        // item is an actual Item() object
        var i = p.get_item(item.id);

        item.item_row.remove();
        remove_from_array(p.items, i);

        item = null;

        p.update_summary();
    };

    p.update_summary = function(){
        // traverse items and sum totals
        var total = Big(0);

        for(var i = 0; i < p.items.length; i++){
            total = total.plus(p.items[i].data.total);
        }

        p.summary_total.text(display_number(total, p.g.config.separator, p.g.config.decimal_places));
    };

    // bill manipulation
    p.finish = function(){
        // put this bill, including all items in a neat json
        // and send it to server

        if(p.items.length == 0){
            error_message(
                gettext("Cannot create bill"),
                gettext("There are no items on it")
            );
            return;
        }

        var i;
        var r = {
            items: []
        };

        // get all items
        for(i = 0; i < p.items.length; i++){
            r.items.push(p.items[i].format());
        }

        // send to server
        send_data(p.g.urls.create_bill, r, p.g.csrf_token, function(recv_data){
            if(recv_data.status != 'ok'){
                error_message(
                    gettext("Error while saving bill"),
                    recv_data.message);

                // TODO: further actions (?!)
            }
            else{
                // TODO: empty this bill and create a new one
            }
        });

        // TODO: what then?
    };

    //
    // init
    //
    // draggable: the same as set_draggable(), but vertical
    p.bill_container.draggable({
        helper: function () {
            return $("<div>").css("opacity", 0);
        },
        drag: function (event, ui) {
            // the position of parent obviously has to be taken into account
            var pos = ui.helper.position().top - p.bill_container.parent().position().top;
            $(this).stop().animate({top: pos},
                p.g.settings.t_easing,
                'easeOutCirc',
                function () {
                    // check if this has scrolled past the last
                    // (first) button
                    var all_buttons = $("div.bill-item", p.bill_container);
                    var first_button = all_buttons.filter(":first");
                    var last_button = all_buttons.filter(":last");
                    var container = p.bill_container.parent().parent();

                    if(first_button.length < 1 || last_button.length < 1) return;

                    // if the whole scroller's height is less than
                    // container's, always slide it back to top border

                    if (first_button.position().top + last_button.position().top + last_button.outerHeight() < container.height()){
                        p.bill_container.animate({top: 0}, "fast");
                    }
                    else {
                        if (first_button.offset().top > container.offset().top) {
                            p.bill_container.animate({top: 0}, "fast");
                        }
                        else if (last_button.offset().top + last_button.height() < container.offset().top + container.height()) {
                            p.bill_container.animate({
                                top: -last_button.position().top + container.height() - last_button.height()}, "fast");
                        }
                    }
                });
        },
        axis: "y"
    });


    // bindings
    p.finish_button.click(function(){
        p.finish();
    });
};

/* Item 'class' */
Item = function(bill, product) {
    // Item properties:
    // saved - this Item has been sent to server already
    // exploded: do not add quantity to this Item when adding the same product to Bill
    var p = this;

    p.bill = bill; // Bill() object
    p.g = p.bill.g;
    p.product = product; // Product() object
    p.data = null; // the actual item data that will be sent to server (initialized later)
    p.serial = ++p.bill.serial; // a unique id for this bill
    p.details = null; // will initialize ItemDetails (if 'more' button is clicked)

    p.item_row = p.bill.item_template.clone().appendTo(p.bill.bill_container);
    p.items = {
        delete_button: $(".delete", p.item_row),

        name: $("div.item.name", p.item_row),
        code: $("div.item.code", p.item_row),

        qty: $("input.qty", p.item_row),
        inc_qty_button: $("button.qty-plus", p.item_row),
        dec_qty_button: $("button.qty-minus", p.item_row),

        price: $("div.item.price", p.item_row),

        tax_absolute: $("div.value.item.tax", p.item_row),

        discount: $(".item-val.discount .value", p.item_row),

        total: $("div.value.item.total", p.item_row),

        more_button: $("button.more", p.item_row),

        explode_button: $("input.explode", p.item_row).hide()
    };

    // properties of this item
    p.expanded = false;

    //
    // methods
    //
    p.update = function(){ // display item data
        if(!p.data) return;

        // the 'usual' item data
        p.items.name.text(p.data.name);
        p.items.code.text(p.data.code);

        // prices:
        var r = total_price(
            p.g.config.tax_first,
            p.data.base_price,
            p.data.tax_percent,
            p.product.data.discounts,
            p.data.quantity,
            p.data.unit_amount);

        // save calculated numbers
        p.data.tax_absolute = r.tax;

        // discounts
        p.data.discount_absolute = r.discount;

        // total
        p.data.total = r.total;

        // quantity
        p.items.qty.val(display_number(p.data.quantity, p.g.config.separator, p.g.config.decimal_places));
        if(p.data.quantity.cmp(Big(1)) > 0) // if qty is more than 1, show the explode button, otherwise it has no function
            p.items.explode_button.show();
        else p.items.explode_button.hide();

        // base price
        p.items.price.text(display_number(p.data.base_price, p.g.config.separator, p.g.config.decimal_places));

        // tax (only absolute value)
        p.items.tax_absolute.text(display_number(p.data.tax_absolute, p.g.config.separator, p.g.config.decimal_places));

        // discounts
        p.items.discount.text(display_number(p.data.discount_absolute, p.g.config.separator, p.g.config.decimal_places));

        // total
        p.items.total.text(display_number(p.data.total, p.g.config.separator, p.g.config.decimal_places));

        // also update bill
        p.bill.update_summary();
    };

    p.add_quantity = function(add){
        // add or remove 1 to/from quantity
        var n, q = p.data.quantity;
        var update = false;

        if(!add){ // don't set a value of 0 or less
            n = q.minus(1);
            if(n.cmp(Big(0)) > 0){
                q = n;
                update = true;
            }
        }
        else{ // do not add more items than there are in stock
            // add in increments of unit_amount
            n = p.data.quantity.plus(Big(1));
            if(n.cmp(p.data.stock) <= 0){
                q = n;
                update = true;
            }
        }

        // update prices
        if(update){
            p.data.quantity = q;
            p.update();
        }
    };

    p.check_quantity = function(){
        var q = get_number(p.items.qty.val(), p.g.config.separator);
        var title = gettext("Invalid quantity");

        // check number format
        if(!q){
            error_message(title, gettext("Wrong number format"));
            q = Big(1);
        }

        // check if there's enough of it in stock
        if(q.cmp(p.data.stock) > 0){
            error_message(title, gettext("There's not enough items in stock"));
            q = p.data.stock;
        }

        // check if it's not negative or 0
        if(q.cmp(Big(0)) <= 0){
            error_message(title, gettext("Quantity cannot be zero or less"));
            q = Big(1);
        }

        // set the new quantity and update everything
        p.data.quantity = q;

        p.update();
    };

    p.format = function(){
        // used for sending to server
        return {
            product_id: p.data.product_id,
            unit_amount: display_number(p.data.unit_amount, p.g.config.separator, p.g.config.decimal_places),
            stock: display_number(p.data.stock, p.g.config.separator, p.g.config.decimal_places),
            quantity: display_number(p.data.quantity, p.g.config.separator, p.g.config.decimal_places),
            base_price: display_number(p.data.base_price, p.g.config.separator, p.g.config.decimal_places),
            tax_percent: display_number(p.data.tax_percent, p.g.config.separator, p.g.config.decimal_places),
            total: display_number(p.data.total, p.g.config.separator, p.g.config.decimal_places)
        }
    };

    p.explode = function(){
        // if this item has quantity > 1, subtract 1 from this and create a new one in the bill
        if(p.data.quantity.cmp(Big(1)) > 0){
            p.bill.add_product(p.product, false);
            p.add_quantity(false);
        }
    };

    p.expand = function(expand){
        p.expanded = expand;

        if(expand){
            // change item's classes
            p.item_row.addClass("expanded").removeClass("collapsed");
        }
        else{
            p.item_row.addClass("collapsed").removeClass("expanded");
        }
    };

    //
    // init
    //
    // create item data from product's
    p.data = {
        product_id: p.product.data.id,
        name: p.product.data.name,
        code: p.product.data.code,
        quantity: Big(1),
        unit_type: p.product.data.unit_type_display,
        unit_amount: p.product.data.unit_amount,
        base_price: p.product.data.price,
        tax_percent: p.product.data.tax,
        tax_absolute: null, // will be calculated later
        stock: p.product.data.stock,
        discount_absolute:null, // calculated later
        total_price: null // calculated later
    };

    // then update it
    p.update();

    // bind events
    // click on an item
    p.item_row.click(function(){
        if(p.expanded){
            // already expanded, just collapse
            p.expand(false);
        }
        else{
            // collapse all bill's items and expand this
            for(var i = 0; i < p.bill.items.length; i++){
                if(p.bill.items[i].serial != p.serial && p.bill.items[i].expanded == true)
                    p.bill.items[i].expand(false);
            }
            p.expand(true);
        }
    });

    // quantity up/down
    p.items.inc_qty_button.click(function(e){
        e.stopPropagation();
        p.add_quantity(true);
    });

    p.items.dec_qty_button.click(function(e){
        e.stopPropagation();
        p.add_quantity(false);
    });

    // remove button
    p.items.delete_button.click(function(e){
        e.stopPropagation();

        confirmation_dialog(
            gettext("Remove bill item"), // message title
            interpolate(gettext("Remove bill item: %(name)s?"), {name: p.data.name}, true),
            function(){ p.bill.remove_item(p); },
            null
        );
    });

    // more button
    p.items.more_button.click(function(e){
        // don't collapse the item
        e.stopPropagation();

        // open the 'more' dialog
        p.details = new ItemDetails(p);
    });

    // quantity
    p.items.qty.change(function(){ p.check_quantity(); });

    // explode button
    p.items.explode_button.click(function(){ p.explode(); });
};

ItemDetails = function(item){
    var p = this;

    p.item = item;
    p.g = p.item.g;

    // gather objects
    p.box = $("#details_box_template")
        .clone()
        .removeAttr("id")
        .hide()
        .removeClass("hidden");

    p.items = {
        tax_percent: $(".tax-percent", p.box),
        tax_absolute: $(".tax-absolute", p.box),
        discounts: $(".discounts", p.box),
        notes: $(".notes", p.box),
        quantity: $(".quantity", p.box),
        explode: $(".explode", p.box),
        save: $("input.ok", p.box),
        cancel: $("input.cancel", p.box)
    };

    //
    // methods
    //
    p.discount_row = function(discount){
        // returns a new jquery object for this discount (to be put in the discount list)
        var li = $("<li>", {title: discount.description});

        if(discount.type == "Percent"){
            // example: ND10 (10 %)
            li.text(
                discount.code + " (" +
                display_number(discount.amount, p.g.config.separator, p.g.config.decimal_places) + " %)"
            );
        }
        else{
            // example ND15 ($ 15)
            li.text(
                discount.code + " (" +
                p.g.config.currency + " " +
                display_number(discount.amount, p.g.config.separator, p.g.config.decimal_places) + ")"
            );
        }

        return li;
    };

    //
    // init
    //

    // move the details box to the correct position
    p.box
        .appendTo($("body"))
        .show()
        .offset({
            left: p.item.item_row.offset().left + p.item.item_row.width(),
            top: 20 // TODO: what is this
        });

    // fill in the details
    // tax:
    p.items.tax_percent.text(
        display_number(p.item.data.tax_percent,
            p.g.config.separator,
            p.g.config.decimal_places));

    p.items.tax_absolute.text(
        display_number(p.item.data.tax_absolute,
            p.g.config.separator,
            p.g.config.decimal_places));

    // discounts: fill in the existing discounts
    var d = p.item.product.data.discounts;
    var i, li;

    for(i = 0; i < d.length; i++){
        p.items.discounts.prepend(p.discount_row(d[i]));
    }

    // bind button actions
    p.items.cancel.click(function(){ p.box.remove(); });
};