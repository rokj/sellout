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

    p.temp_discounts = [];

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

        return total;
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
            items: [],
            grand_total: display_number(p.update_summary(), p.g.config.separator, p.g.config.decimal_places)
        };

        // get all items
        for(i = 0; i < p.items.length; i++){
            p.items[i].update();
            r.items.push(p.items[i].format());
        }

        // decide what to do depending on user's print settings
        if(p.g.config.printer_driver == "system"){
            // use the default, printer;
            // create a HTML receipt and issue javascript print() method and that's it
            console.log("printing");
            var receipt = format_small_receipt(p, r);
            receipt.printThis();
        }
        else{
            // TODO:
            console.log("wtf is this driver");
        }

        // send to print server
        /*send_data('http://localhost:' + p.g.config.printer_port,  r, null, function(response){
            alert(response);
        });*/
        /*send_data(p.g.urls.create_bill, r, p.g.csrf_token, function(recv_data){
            if(recv_data.status != 'ok'){
                error_message(
                    gettext("Error while saving bill"),
                    recv_data.message);

                // TODO: further actions (?!)
            }
            else{
                error_message("jupi, ratschun je napravljen")
                // TODO: empty this bill and create a new one
            }
        });*/

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
    p.items = { // a list of jQuery objects, not Item() objects
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
            p.data.discounts,
            p.data.quantity,
            p.g.config.decimal_places);

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
        var discounts = [];

        for(var i = 0; i < p.data.discounts.length; i++){
            discounts.push({
                id: p.data.discounts[i].id,
                description: p.data.discounts[i].description,
                code: p.data.discounts[i].code,
                type: p.data.discounts[i].type,
                amount: display_number(p.data.discounts[i].amount, p.g.config.separator, p.g.config.decimal_places)
                // enabled: of course it's enabled
                // active: doesn't matter
            });
        }

        return {
            name: p.data.name,
            product_id: p.data.product_id,
            stock: display_number(p.data.stock, p.g.config.separator, p.g.config.decimal_places),
            quantity: display_number(p.data.quantity, p.g.config.separator, p.g.config.decimal_places),
            base_price: display_number(p.data.base_price, p.g.config.separator, p.g.config.decimal_places),
            tax_percent: display_number(p.data.tax_percent, p.g.config.separator, p.g.config.decimal_places),
            discounts: discounts,
            single_total: display_number(p.data.single_total, p.g.config.separator, p.g.config.decimal_places),
            discount_absolute: display_number(p.data.discount_absolute, p.g.config.separator, p.g.config.decimal_places),
            total: display_number(p.data.total, p.g.config.separator, p.g.config.decimal_places),
            bill_notes: p.data.bill_notes
        };
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
        base_price: p.product.data.price,
        tax_percent: p.product.data.tax,
        tax_absolute: null, // will be calculated later
        discounts: [], // see below
        stock: p.product.data.stock,
        discount_absolute: null, // calculated later
        total_price: null, // calculated later
        bill_notes: ''
    };

    // discounts: copy discounts from product
    for(var i = 0; i < p.product.data.discounts.length; i++)
        p.data.discounts.push(p.product.data.discounts[i]);

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

        // a read-only list of discounts already on the product
        active_discounts: $("ul.discounts", p.box),

        // all other discounts that could be added to the product
        all_discounts_li: $("li.select-existing", p.box),
        all_discounts: $(".select-existing select", p.box),
        all_discounts_add: $(".select-existing button", p.box),

        // a unique discount (not bound to database discounts) for adding on-the-fly
        unique_discount_description: $(".add-new .description", p.box),
        unique_discount_amount: $(".add-new .amount", p.box),
        unique_discount_type: $(".add-new .type", p.box),

        notes: $(".notes", p.box),
        explode: $(".explode", p.box),
        save: $("input.ok", p.box),
        cancel: $("input.cancel", p.box)
    };

    p.temp_discounts = []; // this will be saved into product if details are closed with 'save'

    //
    // methods
    //
    p.update_discounts = function(){
        function discount_row(element, discount, editable){
            // returns an jquery object: list item
            // if editable == true, it includes a 'remove' button, otherwise not
            var li = $(element, {title: discount.description, 'class': 'inserted'});

            if(discount.type == "Percent"){
                // example: ND10 (10 %)
                li.text(discount.code + " (" +
                    display_number(discount.amount, p.g.config.separator, p.g.config.decimal_places) + " %)");
            }
            else{
                // example ND15 ($ 15)
                li.text(discount.code + " (" +
                    p.g.config.currency + " " +
                    display_number(discount.amount, p.g.config.separator, p.g.config.decimal_places) + ")");
            }

            if(editable){
                // append a delete button that removes the list item
                var button = $("<input>", {type: 'button', 'class':"remove-item-discount", 'value': 'x'});
                li.append(button);

                button.click(function(){
                    // remove this discount from temp_discounts and update discounts
                    var index = get_index(p.temp_discounts, discount.id);
                    if(index != null) remove_from_array(p.temp_discounts, index);
                    p.update_discounts();
                });
            }

            return li;
        }

        // clear what's currently entered
        $(".inserted", p.items.active_discounts).remove();

        var i, obj, n_available = 0;

        // all available discounts
        var d_available = p.g.data.discounts;
        var d_used = []; // a list of ids

        // put all discounts from item to list and the rest to select box
        for(i = 0; i < p.temp_discounts.length; i++){
            // ignore the unique discount (it stays in )
            if(p.temp_discounts[i].id == -1) continue;

            // the discount is already on the item, append it to list
            obj = discount_row("<li>", p.temp_discounts[i], true);

            // insert after the last inserted discount
            obj.insertBefore(p.items.all_discounts_li);

            obj.data(p.temp_discounts[i]);
        }

        // put all other discounts to select box
        for(i = 0; i < d_available.length; i++){
            if(d_used.indexOf(d_available[i].id) == -1){
                // the discount is not there yet, append it to select box
                obj = discount_row("<option>", d_available[i], false);
                obj.appendTo(p.items.all_discounts);

                obj.data(d_available[i]);

                n_available += 1;
            }
        }

        // if there's a unique discount (it has id=-1), put the data in
        var d = get_by_id(p.temp_discounts, -1);
        if(d){
            p.items.unique_discount_description.val(d.description);
            p.items.unique_discount_amount.val(display_number(d.amount, p.g.config.separator, p.g.config.decimal_places));
            p.items.unique_discount_type.val(d.type);
        }

        // do not show a discount in the select box, it's confusing
        p.items.all_discounts.prop("selectedIndex", -1);

        // if there are no available discounts, disable stuff
        if(n_available == 0){
            p.items.all_discounts_add.unbind().prop("enabled", false);
            p.items.all_discounts.prop("enabled", false);
        }
        else{
            p.items.all_discounts_add.unbind().prop("enabled", true);
            p.items.all_discounts.prop("enabled", true);

            // the add button function
            p.items.all_discounts_add.unbind().click(function(){
                // append a new, editable list item to temp_discounts and update
                var selected_discount = p.items.all_discounts.find(":selected").data();

                p.temp_discounts.push(selected_discount);

                p.update_discounts();
            });
        }

        // in the end, show the user what happened
        p.update_prices();
    };

    p.get_discounts = function(){
        // get the .inserted items from discount list and
        var d = []; // new discounts

        $("li.inserted", p.active_discounts).each(function(){
            d.push($(this).data());
        });

        // see if there is the on-the-fly discount
        if(p.items.unique_discount_amount.val().trim() != ''){
            var amount = get_number(p.items.unique_discount_amount.val());
            if(!amount){
                error_message(
                    gettext("Wrong item format"),
                    gettext("Please check discount number format")
                );

                return null;
            }

            d.push({
                // discount contains:
                id: -1, // a new discount
                description: p.items.unique_discount_description.val(),
                code: "", // no code entered
                type: p.items.unique_discount_type.val(),
                amount: amount,
                enabled: true
            });
        }

        return d;
    };

    p.update_prices = function(){
        var r = total_price(p.g.config.tax_first,
            p.item.data.base_price,
            p.item.data.tax_percent,
            p.temp_discounts,
            p.item.data.quantity,
            p.g.config.decimal_places
        );

        // update only text fields, not item's data;
        // if the user cancels this dialog, nothing must be saved

        // fields:
        // tax in item and details
        $().add(p.item.items.tax_absolute)
            .add(p.items.tax_absolute)
            .text(display_number(r.tax, p.g.config.separator, p.g.config.decimal_places));

        // discount sum in item and details
        p.item.items.discount.text(display_number(r.discount, p.g.config.separator, p.g.config.decimal_places));
        // total in item
        p.item.items.total.text(display_number(r.total, p.g.config.separator, p.g.config.decimal_places));

        // show update prices when:
        //  - quantity changes
        //  - discounts are added or reordered
    };

    p.cancel_button_action = function(){
         p.box.remove();
    };

    p.save_button_action = function(){
        // copy details' values to item data
        p.item.data.discounts = p.get_discounts();
        p.item.data.bill_notes = p.items.notes.val();

        p.item.update();

        // close the box
        p.box.remove();
    };

    p.details_changed = function(){
        // compare original item's details to this dialog's values
        // and there's a difference, return true

        // discounts: check that ids are in the same order than in item
        if(p.item.data.discounts.length != p.temp_discounts.length) return true;

        for(var i = 0; i < p.item.data.discounts.length; i++){
            if(p.item.data.discounts[i].id != p.temp_discounts[i].id) return true;
        }

        // unique discount
        if(p.items.unique_discount_amount.val().trim() != "") return true;

        // check notes
        if(p.item.data.bill_notes != p.items.notes.val()) return true;

        // all tests passed, the items are the same
        return false;
    };

    p.check_unique_discount = function(){
        // check that number is 'parsable'
        // and that percentage discount does not exceed 100%
        var a = get_number(p.items.unique_discount_amount.val(), p.g.config.separator);

        if(!a) return false;

        return !(p.items.unique_discount_type.val() == 'Percent' && a.cmp(Big(100)) > 0);
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
        display_number(p.item.data.tax_percent, p.g.config.separator, p.g.config.decimal_places));

    p.items.tax_absolute.text(
        display_number(p.item.data.tax_absolute, p.g.config.separator, p.g.config.decimal_places));

    // copy current item's discounts to a temporary list;
    // it will be edited and when details is saved, the item's discounts will
    // be pointed to this list
    for(var i = 0; i < p.item.data.discounts.length; i++){
        p.temp_discounts.push(p.item.data.discounts[i]);
    }
    p.update_discounts();

    p.items.active_discounts.sortable({
        items: "li.inserted",
        opacity: 0.5,
        stop: function(){
            p.temp_discounts = p.get_discounts();
            p.update_discounts();
        }
    });

    $().add(p.items.unique_discount_amount)
       .add(p.items.unique_discount_type)
       .blur(function(){
            if(p.check_unique_discount()){
                p.temp_discounts = p.get_discounts();
                p.update_prices();
            }
            else{
                error_message(
                    gettext("Invalid discount"),
                    gettext("Please check discount format and type")
                );
            }
       });

    p.items.notes.val(p.item.data.bill_notes);

    // bind button actions
    p.items.cancel.click(function(){ p.cancel_button_action();});

    p.items.save.click(function(){ p.save_button_action(); });

    // explode button
    p.items.explode.unbind().click(function(){
        // if anything has been changed, ask the user to save or cancel
        if(p.details_changed()){
            // warn the user about changed details
            var dlg = confirmation_dialog(
                gettext("Confirm explode"),
                gettext("You have made changes to this item that will not be saved to the new item. Continue?"),
                function(){
                    // yes action: cancel, explode and close the 'dialog'
                    p.cancel_button_action();
                    p.item.explode();
                    dlg.dialog("close");
                },
                function(){
                    // no action: do nothing (just close the dialog)
                    dlg.dialog("close");
                }
            );
        }
        else{
            p.item.explode();
            p.cancel_button_action();
        }
    });
};