/*

    Bill: handles everything regarding billing and bill items, contains items
      Item: data about items, editing, etc.


    Messages sent to the document:
     - bill.item-changed : update bill summary


 */
Bill = function(g){
    var p = this;

    p.g = g;

    p.data = null; // bill be set in clear()

    // bill properties
    p.serial = 0; // a number that will be assigned to every item (has nothing to do with id on server)
    p.items = []; // a list of Item objects
    p.items_by_serial = {}; // pairs item_number:Item object for quick access
    p.items_by_id = {}; // pairs product_id:Item

    p.contact = null; // reference to contact (object with details) (if chosen)
    p.saved = false; // true if the bill in this state is saved on the server

    p.payment = null; // will hold the Payment() object

    // items
    p.bill = $("#bill");

    // summary numbers
    p.summary = $("#bill_summary");
    p.summary_total = $("p.total", p.summary);

    // the 'finish' button
    p.actions = $("#bill_actions");
    p.pay_button = $("#finish_the_bill", p.actions);

    // the options menu
    p.options_button = $("button.open-menu", "#bill_options");
    p.options_menu = $("#bill_options_menu");

    p.option_contacts = $(".select-client", p.options_menu);
    p.option_options = $(".options", p.options_menu);
    p.option_save = $(".save", p.options_menu);
    p.option_load = $(".load", p.options_menu);
    p.option_clear = $(".clear", p.options_menu);

    // the options dialog
    p.bill_options = null; // BillOptions object, (initialized later)

    // the dialogs for loading/saving unpaid bills
    p.save_bill_dialog = $("#save_bill_dialog");
    p.load_bill_dialog = $("#load_bill_dialog");

    // save item template for items and remove it from the document
    p.item_template = $("#bill_item_template").detach().removeAttr("id");

    //
    // methods
    //
    // item manipulation
    p.get_item = function(serial){
        return p.items_by_serial[serial];
    };

    p.get_product = function(product_id){
        // returns an Item object given a product id
        return p.items_by_id[product_id];
    };

    p.add_item = function(product){
        // create a new item
        var item = new Item(p, product);

        // save it to the list of items
        p.items.push(item);
    };

    p.add_product = function(product, to_existing){
        // see if this product is already in the bill;

        if(to_existing == false){
            p.add_item(product);
        }
        else{
            // see if this item is already on the bill
            var existing_item = p.get_product(product.data.id);

            if(!existing_item){
                // it's not there yet, add a new item
                p.add_item(product);
            }
            else{
                // if it is, just update quantity
                existing_item.add_quantity(true);
            }
        }

        // bill has been changed and it must be saved
        p.bill.saved = false;

        p.update();
    };

    p.remove_item = function(item){
        // item is an actual Item() object;
        // to remove the item from list, one has to do the vanilla linear search...
        for(var i = 0; i < p.items.length; i++){
            if(p.items[i] == item){
                break;
            }
        }

        item.item_row.remove();
        remove_from_array(p.items, i);
        delete p.items_by_serial[item.serial];
        delete p.items_by_id[item.product.id];

        item = null;

        // updated bill
        p.bill.saved = false;
    };

    p.get_discount = function(){
        // get the discount from bill data;
        // return {type: and amount:};
        // if there's not data, the amount is 0
        if(p.data && p.data.discount_amount != null){
            return {type: p.data.discount_type, amount: p.data.discount_amount}
        }
        else{
            return {type: 'Relative', amount: Big(0)};
        }
    };

    p.clear = function(){
        // clear local storage: we don't want the same bill to pop up next time
        clear_local('bill');

        // remove all items one by one
        for(var i = 0; i < p.items.length; i++){
            p.items[i].item_row.remove();
        }

        p.items = [];
        p.items_by_serial = {};
        p.items_by_id = {};

        p.data = { // Data that should be here at all times
            items: [],
            contact: null,

            discount_amount: Big(0),
            discount_type: 'Relative',
            notes: ''
        };

        p.serial = 0;
        p.contact = null;
        p.saved = true; // there's nothing to be saved
        p.payment = null; // will hold the Payment() object

        // contact
        if(p.g.objects.contacts) // may not be initialized yet
            p.g.objects.contacts.update_labels();

        // discounts and notes
        p.bill_options = new BillOptions(p);

        // total
        p.summary_total.text(dn(Big(0), p.g));

    };

    p.update = function(){
        // get the numbers from all items in one place and send it to calculation

        // items and their discounts
        var i, j, item, discount, discount_list;
        var c_items = [], c_item;

        for(i = 0; i < p.items.length; i++){
            item = p.items[i];

            c_item = {
                serial: item.serial,
                quantity: item.data.quantity,
                base: item.data.base, // price without discounts and without tax
                tax_rate: item.data.tax_rate, // price in percentage
                discounts: [] // a list of discount objects
            };

            // discount format for calculation:
            // if the item details box is open, use temp_discounts from that objects;
            // otherwise, use stored discounts on the item
            if(item.details) discount_list = item.details.temp_discounts;
            else discount_list = item.data.discounts;

            // { amount: Big(), type: 'absolute'/'percent' }
            for(j = 0; j < discount_list.length; j++){
                discount = discount_list[j];
                c_item.discounts.push({
                    amount: discount.amount,
                    type: discount.type
                });
            }

            c_items.push(c_item);
        }

        // bill discounts
        var bill_discount = p.get_discount();

        // do the calculation
        var prices = calculate_bill(c_items, bill_discount.amount, bill_discount.type, p.g.config.decimal_places);

        // update all items' data and refresh them
        for(i = 0; i < prices.items.length; i++){
            item = p.items_by_serial[prices.items[i].serial];

            item.data.batch = prices.items[i].batch;
            item.data.net = prices.items[i].net;
            item.data.tax = prices.items[i].tax;
            item.data.discount = prices.items[i].discount;
            item.data.total = prices.items[i].total;

            item.update();
        }

        // update bill's amounts
        p.summary_total.text(dn(prices.total, p.g));

        return prices;
    };

    // bill manipulation
    p.load = function(data){
        p.clear();

        // loads bill from data;
        // from the server or local storage;
        // if data is null, init a new bill
        if(data == null) return;

        p.data = data;

        // add bill items
        var i, product;
        for(i = 0; i < p.data.items.length; i++){
            // get products from items' ids and create new items
            product = p.g.objects.products.products_by_id[p.data.items[i].product_id];

            if(!product) continue;

            p.items.push(new Item(p, product));
        }

        // contact: if the bill is retrieved from the server, the contact is id only,
        // otherwise it's a contact object (saved from js)
        if(typeof(p.data.contact) == 'number'){
            // search contacts by id and select the right one
            for(i = 0; i < p.g.data.contacts.length; i++){
                if(p.g.data.contacts[i].id == data.contact){
                    p.data.contact = p.g.data.contacts[i].id;
                    break;
                }
            }
        }
        else{
            // just assign the data
            p.contact = p.data.contact;
        }

        // other bill data
        p.data.discount_amount = get_number(p.data.discount_amount, p.g.config.separator);

        p.update();
    };

    p.get_data = function(){
        // returns bill and item data for saving/sending

        // if no registers are defined, there's no point in doing anything
        // (the script redirects to register management anyway, this is just
        // to prevent errors)
        if(!p.g.objects.terminal.register) return null;

        // data

        // id: if saving existing bill
        var id;

        if(p.data && !isNaN(p.data.id)) id = p.data.id;
        else id = -1;

        // timestamp: send an array of numbers: year, month (1-based!), day, hour, minute, second
        var d = new Date();
        var timestamp = [d.getFullYear(), d.getMonth()+1, d.getDate(), d.getHours(), d.getMinutes(), d.getSeconds()];

        // issuer: the current company, in view

        // contact:
        var contact = p.contact;

        // register:
        var register_id = p.g.objects.terminal.register.id;

        // user and user_id: from request
        // serial: will be set on the server

        // discount amount and type:
        var discount_amount = p.data.discount_amount;
        var discount_type = p.data.discount_type;

        // prices: recalculate everything
        var prices = p.update();

        // base price:
        var base = prices.base;
        var discount = prices.discount;
        var tax = prices.tax;
        var total = prices.total;

        // note:
        var notes = p.data.notes;

        // prepare items:
        var i, item, items = [];

        for(i = 0; i < prices.items.length; i++){
            item = p.get_item(prices.items[i].serial);

            items.push(item.format());
        }

        // put everything in a neat object
        return {
            id: id,
            timestamp: timestamp,
            contact: contact,
            register_id: register_id,

            discount_amount: dn(discount_amount, p.g),
            discount_type: discount_type,

            base: dn(base, p.g),
            discount: dn(discount, p.g),
            tax: dn(tax, p.g),
            total: dn(total, p.g),

            notes: notes,

            items: items
        }
    };

    p.pay = function(){
        // put this bill, including all items in a neat json
        // and send it to server
        if(p.items.length == 0){
            error_message(
                gettext("Cannot create bill"),
                gettext("The bill is empty")
            );
            return;
        }

        var data = p.get_data();

        // send to server, continue with payment when response returns
        send_data(p.g.urls.create_bill, data, p.g.csrf_token, function(response){
            if(response.status != 'ok'){
                error_message(
                    gettext("Could not create bill"),
                    response.message
                );
            }
            else{
                p.data = response.data.bill;
                p.payment = new Payment(p.g, p);
            }
        });
    };

    p.show_item = function(item){
        // scrolls the bill so that the current item is shown
        vertical_scroll_into_view(item.item_row);
    };

    p.toggle_bill_options = function(show){
        p.bill_options.toggle_dialog(show);
    };

    p.save_unpaid = function(post_save_callback){
        var notes = $("#save_bill_notes");

        notes.val("");

        // open the dialog
        custom_dialog(
            gettext("Save Bill"), // title
            p.save_bill_dialog, // content
            400, // width
            { // buttons: 'save' and 'cancel'
                yes: gettext("Save"),
                yes_action: function(){
                    // put the notes to p.data
                    p.data.notes = notes.val();

                    // send it to server
                    send_data(
                        p.g.urls.create_bill, p.get_data(), p.g.csrf_token, function(response){
                            if(response.status != 'ok'){
                                error_message(gettext("Saving bill failed"),
                                    response.message);
                            }
                            else{
                                // create a new, empty bill
                                p.clear();

                                // do anything that's ordered
                                if(post_save_callback) post_save_callback();
                            }
                        });
                },

                no: gettext("Cancel"),
                no_action: function(){
                    // do absolutely nothing apart from closing the dialog
                }
            }
        );

        // focus notes
        notes.focus();
    };

    p.load_unpaid = function(){
        // this is the function that will be called after checks and save dialogs
        function do_load(){
            // fetch unpaid bills from the server
            get_data(p.g.urls.get_unpaid_bills, function(response){
                if(response.status != 'ok'){
                    error_message(gettext("Loading bills failed"),
                        response.message);
                }
                else{
                    // data
                    var bill_list = response.data;

                    // open the dialog and list bills
                    var list_obj = $("table", p.load_bill_dialog);
                    var template_obj = $("thead tr", list_obj).clone();

                    list_obj = $("tbody", list_obj);
                    list_obj.empty();

                    // fill the table with bills
                    for(var i = 0; i < bill_list.length; i++){
                        // wrap everything in a new function to prevent
                        // 'access mutable variable from closure' problem
                        (function(i){
                            var bill = bill_list[i];

                            var list_item = template_obj.clone();
                            $(".time", list_item).text(bill.timestamp);
                            $(".items", list_item).text(bill.items.length);
                            $(".notes", list_item).text(bill.notes);

                            // the buttons:
                            // delete
                            $(".delete-button", list_item).show().unbind().click(function(){
                                // ask if the user is  S U R E 'cuz dis is veri imparrtent
                                confirmation_dialog(gettext("Delete this bill?"), "",
                                    function(){
                                        // send a delete request to server
                                        send_data(p.g.urls.delete_unpaid_bill, { bill_id: bill.id },
                                            p.g.csrf_token, function(response){
                                                if(response.status != 'ok'){
                                                    error_message(gettext("Deleting bill failed"),
                                                        response.message);
                                                }
                                                else{
                                                    // the bill has been deleted, delete the list item as well
                                                    list_item.remove();
                                                }
                                            });
                                    },
                                    function(){ }
                                );
                            });

                            // load
                            $(".load-button", list_item).show().unbind().click(function(){
                                // load this bill to terminal
                                p.load(bill);
                                p.load_bill_dialog.close_dialog(); // custom_dialog() adds this method to jquery object
                            });

                            // append to list
                            list_obj.append(list_item);
                        })(i);
                    }

                    custom_dialog(gettext("Load bill"), p.load_bill_dialog, 600, {});

                }
            });
        }

        // check if there's an unsaved bill;
        // if it is, ask to save or clear
        if(!p.saved){
            custom_dialog(
                gettext("The current bill is not saved"),
                gettext("Do you wish to save or clear it?"),
                400, {
                    yes: gettext("Save"),
                    yes_action: function(){
                        p.save_unpaid(do_load);
                    },
                    no: gettext("Clear"),
                    no_action: function(){
                        p.clear();
                        do_load();
                    }
                });
        }
        else{
            do_load();
        }
    };

    //
    // init
    //
    // draggable bill
    set_vertical_draggable(p.bill, "div.bill-item", p.g.settings.t_easing);

    // bindings:
    p.pay_button.click(function(){
        p.pay();
    });

    // bill options:
    // the menu
    p.options_button.unbind().simpleMenu(p.options_menu);

    // contacts
    p.option_contacts.unbind().click(function(){ p.g.objects.contacts.choose_contact(); });

    // discounts and notes (the bill options menu)
    p.option_options.unbind().click(function(){
        p.toggle_bill_options(true);
    });

    // save bill
    p.option_save.unbind().click(p.save_unpaid);

    // load bill
    p.option_load.unbind().click(p.load_unpaid);

    // clear bill
    p.option_clear.unbind().click(function(){
        // a confirmation is required
        confirmation_dialog(
            gettext("Confirm bill clear"),
            gettext("Are you sure you want to clear bill? All items will be removed."),
            p.clear,
            function(){}
        );
    });

    // a new bill
    p.clear();
};

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

    p.item_row = p.bill.item_template.clone().appendTo(p.bill.bill);
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

        more_button: $("button.more", p.item_row)
    };

    // properties of this item
    p.expanded = false;

    //
    // methods
    //
    p.update = function(){ // display item data
        if(!p.data) return;

        // the 'usual' item data
        p.items.name.text(p.data.name).attr("title", p.data.name).tooltip();
        p.items.code.text(p.data.code);

        // quantity: never round numbers
        p.items.qty.val(display_exact_number(p.data.quantity, p.g.config.separator));

        // batch price
        p.items.price.text(dn(p.data.batch, p.g));

        // tax (only absolute value)
        p.items.tax_absolute.text(dn(p.data.tax, p.g));

        // discounts
        p.items.discount.text(dn(p.data.discount, p.g));

        // total
        p.items.total.text(dn(p.data.total, p.g));

        // out of stock class
        //if(p.data.quantity.cmp(p.product.data.stock) >= 0) p.item_row.addClass("out-of-stock");
        //else p.item_row.removeClass("out-of-stock");
    };

    p.add_quantity = function(add){
        // add or remove 1 to/from quantity
        var n, q = p.data.quantity;
        var update = false;

        if(!add){
            n = q.minus(1);
            if(n.cmp(Big(0)) > 0){ // don't set a value of 0 or less
                q = n;
                update = true;
            }
        }
        else{
            n = p.data.quantity.plus(Big(1));
            // disabled at the moment
            // if(n.cmp(p.data.stock) <= 0){ // do not add more items than there are in stock
                q = n;
                update = true;
            //}
        }

        // update prices
        if(update){
            p.data.quantity = q;
            p.bill.update();
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

        // round to set precision
        // wtf! of course not. this is user input
        //q = q.round(p.g.config.decimal_places);

        // check if there's enough of it in stock
        // this has been disabled
        // if(q.cmp(p.data.stock) > 0){
        //     error_message(title, gettext("There's not enough items in stock"));
        //     q = p.data.stock;
        // }

        // check if it's not negative or 0
        if(q.cmp(Big(0)) <= 0){
            error_message(title, gettext("Quantity cannot be zero or less"));
            q = Big(1);
        }

        // set the new quantity and update everything
        p.data.quantity = q;

        p.bill.update();
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
                amount: dn(p.data.discounts[i].amount, p.g)
                // enabled: of course it's enabled
                // active: doesn't matter
            });
        }

        return {
            name: p.data.name,
            product_id: p.data.product_id,
            stock: dn(p.data.stock, p.g),
            bill_notes: p.data.bill_notes,

            base: dn(p.data.base, p.g),
            quantity: display_exact_number(p.data.quantity, p.g.config.separator), // !never round quantity
            tax_rate: dn(p.data.tax_rate, p.g),

            batch: dn(p.data.batch, p.g),
            discount: dn(p.data.discount, p.g),
            net: dn(p.data.net, p.g),
            tax: dn(p.data.tax, p.g),
            total: dn(p.data.total, p.g),

            discounts: discounts
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
        unit_type: p.product.data.unit_type_display,
        bill_notes: '',
        stock: p.product.data.stock,

        quantity: Big(1),
        base: p.product.data.price,
        tax_rate: p.product.data.tax,

        batch: null,
        discount: null,
        net: null,
        tax: null, // will be calculated later
        total: null, // calculated later
        discounts: [] // see below
    };

    // discounts: copy discounts from product
    for(var i = 0; i < p.product.data.discounts.length; i++)
        p.data.discounts.push(p.product.data.discounts[i]);

    // bind events
    // click on an item
    p.item_row.click(function(){
        // if the bill has the 'no-click' class, do nothing (it's being dragged)
        if(p.bill.bill.hasClass("no-click")) return;

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

        // show the item
        p.bill.show_item(p);
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

        p.bill.remove_item(p);
    });

    // more button
    p.items.more_button.click(function(e){
        // don't collapse the item
        e.stopPropagation();

        // open the 'more' dialog
        p.details = new ItemDetails(p);
    });

    // quantity
    p.items.qty
        .unbind()
        .click(function(e){ e.stopPropagation(); })
        .change(p.check_quantity);


    // save references for quick access:
    // by serial number on this bill
    p.bill.items_by_serial[p.serial] = p;
    // by product id
    p.bill.items_by_id[p.data.product_id] = p;

    // when the item is added, scroll the bill to show it
    p.bill.show_item(p);

    // show the numbers
    p.update();
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

        notes: $("textarea.notes", p.box),
        explode: $("button.explode", p.box),
        save: $("input.ok", p.box),
        cancel: $("input.cancel", p.box),

        arrow: $(".item-arrow", p.box)
    };

    p.temp_discounts = []; // this will be saved into product if details are closed with 'save'

    // will contain $ shadow divs once the box is displayed
    p.shadow_top = null; // shadow above the item
    p.shadow_left = null; // to the left
    p.shadow_bottom = null; // below
    p.shadow_right = null; // to the right

    p.item_blocker = null; // an element to block all actions on item (directly above item)

    //
    // methods
    //
    p.update_discounts = function(){
        function discount_row(element, discount, editable){
            // returns an jquery object: list item
            // if editable == true, it includes a 'remove' button, otherwise not
            var li = $(element, {title: discount.description, 'class': 'inserted'});

            if(discount.type == "Relative"){
                // example: ND10 (10 %)
                li.text(discount.code + " (" + dn(discount.amount, p.g) + " %)");
            }
            else{
                // example ND15 (15 $)
                li.text(discount.code + " (" + display_currency(discount.amount, p.g) + ")");
            }

            if(editable){
                // append a delete button that removes the list item
                var button = $("<button>", {'class':"remove-item-discount"});
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

        // put all discounts from item to list
        for(i = 0; i < p.temp_discounts.length; i++){
            // ignore the unique discount (it stays in )
            if(p.temp_discounts[i].id == -1) continue;

            // the discount is already on the item, append it to list
            obj = discount_row("<li>", p.temp_discounts[i], true);

            // insert after the last inserted discount
            obj.insertBefore(p.items.all_discounts_li);

            obj.data(p.temp_discounts[i]);

            d_used.push(p.temp_discounts[i].id);
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
            p.items.unique_discount_amount.val(dn(d.amount, p.g));
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
                if(!selected_discount) return;

                p.temp_discounts.push(selected_discount);

                p.update_discounts();
            });
        }

        // in the end, show the user what happened
        p.update_prices();

        // reposition the box if need to
        p.position_box();
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

    p.update_texts = function(){
        // re-show numbers
        p.items.tax_percent.text(dn(p.item.data.tax_rate, p.g) + " %");
        p.items.tax_absolute.text(display_currency(p.item.data.tax, p.g));
    };


    p.update_prices = function(){
        p.item.bill.update();

        p.update_texts();
    };

    p.cleanup = function(){
        p.temp_discounts = [];

        // common to cancel and save buttons
        p.box.remove();

        var shadows = $()
            .add(p.shadow_top)
            .add(p.shadow_bottom)
            .add(p.shadow_left)
            .add(p.shadow_right)
            .add(p.item_blocker);

        shadows.fadeOut("fast", function(){
            shadows.remove();
        });

        // dereference this object on its parent
        p.item.details = null;
    };

    p.cancel_button_action = function(){
        p.cleanup();

        p.item.bill.update();
    };

    p.save_button_action = function(){
        // copy details' values to item data
        p.item.data.discounts = p.get_discounts();
        p.item.data.bill_notes = p.items.notes.val();

        p.item.bill.update();

        p.cleanup();
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

        return !(p.items.unique_discount_type.val() == 'Relative' && a.cmp(Big(100)) > 0);
    };

    p.create_shadows = function(){
        var body = $("body");

        p.shadow_top = $("<div>", {"class": "shadow __top"}).appendTo(body);
        p.shadow_bottom = $("<div>", {"class": "shadow __bottom"}).appendTo(body);
        p.shadow_left = $("<div>", {"class": "shadow __left"}).appendTo(body);
        p.shadow_right = $("<div>", {"class": "shadow __right"}).appendTo(body);
        p.item_blocker = $("<div>", {"class": "blocker"}).appendTo(body);
    };

    p.position_box = function(){
        // the position of the item
        var item_position = p.item.item_row.offset();

        var arrow_position = {
            left: item_position.left + p.item.item_row.outerWidth(true),
            top: item_position.top + p.item.item_row.outerHeight(true)/2
        };

        var item_size = {
            width: p.item.item_row.outerWidth(true),
            height: p.item.item_row.outerHeight(true)
        };

        var box_size = {
            width: p.box.outerWidth(true),
            height: p.box.outerHeight(true)
        };

        var WINDOW_MARGIN = 10; // minimum distance from window edges
        var ARROW_MARGIN = 25; // keep the box's arrow from covering item details
        var window_height = $(window).height();
        var window_width = $(window).width();

        if(arrow_position.top >= (box_size.height/2 + WINDOW_MARGIN) &&
           (window_height - arrow_position.top) >= box_size.height/2){
            // there's enough space above and below, center the box
            p.box.offset({
                left: arrow_position.left + ARROW_MARGIN,
                top: arrow_position.top - box_size.height/2
            });

            // position the arrow to the middle
            p.items.arrow.css("top", Math.round(box_size.height/2) + "px").show();
        }
        else if(arrow_position.top <= (box_size.height/2 + WINDOW_MARGIN)){
            // show the box (almost) at the top of the screen, then adjust the arrow position
            p.box.offset({
                left: arrow_position.left + ARROW_MARGIN,
                top: WINDOW_MARGIN
            });

            // arrow position
            p.items.arrow.css("top", Math.round(arrow_position.top - WINDOW_MARGIN) + "px").show();
        }
        else{
            // show the box (almost) at the bottom of the screen
            p.box.css({
                left: arrow_position.left + ARROW_MARGIN,
                bottom: WINDOW_MARGIN
            });

            // arrow position
            p.items.arrow.css("bottom",
                Math.round(window_height - arrow_position.top - WINDOW_MARGIN - p.items.arrow.width()/2)
                    + "px").show();
        }

        // move the shadow around the item
        p.shadow_top.css({
            top: 0, left: 0, width: window_width, height: item_position.top
        });
        p.shadow_left.css({
            top: item_position.top, left: 0, width: item_position.left, height: item_size.height
        });
        p.shadow_right.css({
            top: item_position.top, left: item_position.left + item_size.width,
            height: item_size.height, right: 0
        });
        p.shadow_bottom.css({
            top: item_position.top + item_size.height,
            left: 0, right: 0, bottom: 0
        });
        p.item_blocker.click(function(e){
                e.preventDefault();
                e.stopPropagation();
            })
            .css({
                top: item_position.top, left: item_position.left,
                width: item_size.width, height: item_size.height
            })
            .css("z-index", p.box.css("z-index")); // use the same index as the details box
    };

    //
    // init
    //

    // shade the stuff
    p.create_shadows();

    // move the details box to the correct position
    p.box
        .appendTo($("body"))
        .show();

    p.position_box();

    p.update_texts();

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
            if(p.items.unique_discount_amount.val().trim() != ''){
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
            }
       });

    p.items.notes.val(p.item.data.bill_notes);

    // bind button actions
    p.items.cancel.unbind().click(function(){ p.cancel_button_action();});
    p.items.save.unbind().click(function(){ p.save_button_action(); });

    // explode button: if quantity is 1, hide it
    if(p.item.data.quantity.cmp(Big(1)) > 0){
        toggle_element(p.items.explode, true);

        p.items.explode.unbind().click(function(){
            // if anything has been changed, ask the user to save or cancel
            if(p.details_changed()){
                // warn the user about changed details
                confirmation_dialog(
                    gettext("Confirm explode"),
                    gettext("You have made changes to this item that will not be saved to the new item. Continue?"),
                    function(){
                        // yes action: cancel and explode
                        p.cancel_button_action();
                        p.item.explode();
                    },
                    function(){
                        // no action: do nothing
                    }
                );
            }
            else{
                p.item.explode();
                p.cancel_button_action();
            }
        });

    }
    else{
        toggle_element(p.items.explode, false);
    }

    // when any part of the shadow is clicked, close the details
    $()
        .add(p.shadow_top)
        .add(p.shadow_bottom)
        .add(p.shadow_left)
        .click(function(){
            p.cancel_button_action();
        });
};

BillOptions = function(bill){
    var p = this;

    p.bill = bill;
    p.g = p.bill.g;

    p.dialog = $("#bill_options_dialog");
    p.items = {
        discount_amount: $("#bill_discount_amount"),
        discount_type: $("#bill_discount_type"),
        notes: $("#bill_notes")
    };

    //
    // methods
    //
    p.toggle_dialog = function(show){
        if(show){
            // set all data to what's on the bill
            p.items.discount_amount.val(dn(p.bill.data.discount_amount, p.g));
            p.items.discount_type.val(p.bill.data.discount_type);
            p.items.notes.val(p.bill.data.notes);

            custom_dialog(gettext("Bill options"), p.dialog, 500,
                {yes: gettext("Save"), yes_action: p.save_action,
                 no: gettext("Cancel"), no_action: p.cancel_action});
        }
        else{
            p.dialog.close_dialog();
        }
    };

    p.save_action = function(){
        // check discount format
        var amount = get_number(p.items.discount_amount.val(), p.g.config.separator);

        if(!amount){
            error_message(
                gettext("Wrong number format"),
                gettext("Please check discount amount"));

            return;
        }

        // save stuff to data
        p.bill.data.discount_amount = amount;
        p.bill.data.discount_type = p.items.discount_type.val();
        p.bill.data.notes = p.items.notes.val();

        p.close_dialog();
    };

    p.cancel_action = function(){

        p.close_dialog();
    };

    p.close_dialog = function(){
        p.bill.update();
        p.toggle_dialog(false);
    };

    //
    // init
    //

    // [nothing at all.]
};