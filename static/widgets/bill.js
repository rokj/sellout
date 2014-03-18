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

    p.bill_container = $("#bill"); // <table> object
    p.items_container = $("#bill_items"); // <tbody> with items

    // save item template for items and remove it from the document
    p.item_template = $("#bill_item_template").detach().removeAttr("id");

    //
    // methods
    //
    // bill manipulation

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

    p.add_product = function(product){
        // see if this product is already in the bill;
        var item_index = p.get_product(product.data.id);

        if(item_index){
            // if it is, just update quantity
            //p.items[item_index].something_something()
        }
        else{
            // if not, add a new item
            var item = new Item(p, product);
        }

    };

    p.remove_item = function(item){
        // item is an actual Item() object
        var i = p.get_item(item.id);

        item.item_row.remove();
        remove_from_array(p.items, i);

        item = null;
    };

    //
    // init
    //
    // start a new bill


    // append items to Bill
    /*for(i = 0; i < bill_data.items.length; i++){
        ti = new Item(parse_item_data(bill_data.items[i]), true, false); // Item data, saved, not exploded
        // convert strings in data to Big() numbers
        items.push(ti);
    }
    p.items = items;

    // also save other information (but not items)
    delete bill_data.items;
    p.data = bill_data;

    p.last_item_id = -1;
    */

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
    p.serial = ++p.bill.serial;

    p.item_row = p.bill.item_template.clone().appendTo(p.bill.items_container);
    p.items = {
        name: $("div.item.name", p.item_row),
        code: $("div.item.code", p.item_row),
        qty: $("input.qty", p.item_row),
        inc_qty_button: $("input.qty-plus", p.item_row),
        dec_qty_button: $("input.qty-minus", p.item_row),
        price: $("div.item.price", p.item_row),
        tax_relative: $("div.value.item.tax", p.item_row),
        tax_absolute: $("div.subvalue.item.tax", p.item_row),
        discount: $("div.item.discount", p.item_row),
        discount_more_button: $("input.discount-more", p.item_row),
        total: $("div.value.item.total", p.item_row),
        explode_button: $("input.explode", p.item_row).hide(),
        delete_button: $("input.delete", p.item_row)
    };

    //
    // methods
    //
    p.update = function(){ // display item data
        if(!p.data) return;

        // the 'usual' item data
        p.items.name.text(p.data.name);
        p.items.code.text(p.data.code);
        p.items.qty.val(
            display_number(p.data.quantity, p.g.config.separator, p.g.config.decimal_places)
            + " x " + display_number(p.data.unit_amount, p.g.config.separator, p.g.decimal_places)
        );

        // prices:
        var r = total_price(
            p.g.config.tax_first,
            p.data.base_price,
            p.data.tax_percent,
            [], // TODO: discounts
            p.data.quantity,
            p.data.unit_amount);

        // save calculated numbers
        p.data.tax_absolute = r.tax;

        // TODO: discounts
        p.data.discount_absolute = null;

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
        // TODO

        // total
        p.items.total.text(display_number(p.data.total, p.g.config.separator, p.g.config.decimal_places));
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

    p.format_item = function(){
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
        console.log("explode")
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
        unit_type: get_number(p.product.data.unit_type_display, p.g.config.separator),
        unit_amount: get_number(p.product.data.unit_amount, p.g.config.separator),
        base_price: get_number(p.product.data.price, p.g.config.separator),
        tax_percent: get_number(p.product.data.tax, p.g.config.separator),
        tax_absolute: null, // will be calculated later
        stock: get_number(p.product.data.stock, p.g.config.separator),
        discount_absolute:null // calculated later
    };

    // then update it
    p.update();

    // bind events
    // quantity up/down
    p.items.inc_qty_button.click(function(){ p.add_quantity(true); });
    p.items.dec_qty_button.click(function(){ p.add_quantity(false); });

    // remove button
    p.items.delete_button.click(function(){
        confirmation_dialog(
            gettext("Remove bill item"), // message title
            interpolate(gettext("Remove bill item: %(name)s?"), {name: p.data.name}, true),
            function(){ p.bill.remove_item(p); },
            null
        );
    });

    // quantity
    p.items.qty.change(function(){ p.check_quantity(); });

    // explode button
    p.items.explode_button.click(function(){ p.explode(); });
};