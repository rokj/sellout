/* bill 'class' */
bill = function(bill_data){
    // append items to bill
    var items = [];
    var i, ti;
    for(i = 0; i < bill_data.items.length; i++){
        ti = new item(parse_item(bill_data.items[i]), true, false);
        // convert strings in data to Big() numbers
        items.push(ti); // parent, item data, saved, not exploded
    }
    this.items = items;

    // also save other information (but not items)
    delete bill_data.items;
    this.data = bill_data;

    // TODO: start timer interval that will save unsaved items to server every <n> seconds
}

// bill class methods
bill.prototype.get_product = function(product_id){
    // return an 'unexploded' item object for product 'product_id'
    var i;
    for(i = 0; i < this.items.length; i++){
        if (this.items[i].data.product_id == product_id) {
            if(this.items[i].exploded == false) return this.items[i];
        }
    }
    // nothing was found
    return null;
}

bill.prototype.get_item = function(item_id){
    // return an 'item' object with specified id
    var i;
    for(i = 0; i < this.items.length; i++){
        if(this.items[i].data.id == item_id){
            // return array index and item so it can be removed from array
            return {index:i, item:this.items[i]}; // index will be useful (for deleting)
        }
    }
    // nothing was found
    return null;
}

bill.prototype.add_product = function(product){
    // add product to bill:
    // see if this product is already in bill;
    // if it is, just add '1' to quantity;
    // if it's not, add a new item

    var iexist = this.get_product(product.id); // existing 'item' object in bill

    if(iexist){
        // there is, add <unit_amount> to existing item's quantity
        iexist.add_quantity(true);
    }
    else{
        // no, there's no item for this product in bill, update the last edited and add a new one
        // send the last edited item to the server: it will be updated when the server answers
        var new_item = new item(parse_item(product_to_item(product)), false, false);
        this.items.push(new_item);
    }
}

bill.prototype.save_changes = function(){
    // search bill items and if there are any unsaved ones, update them
    var i, ti;
    for(i = 0; i < this.items.length; i++){
        if(!this.items[i].saved){
            // this item hasn't been saved yet, send it to server
            ti = item_to_string(this.items[i]);
            send_data(window.data.edit_bill_item, ti, window.data.csrf_token, function(recv_data){
                // recv_data contains item's re-calculated fields. update it
                var item_to_update = parse_item(recv_data);
                var r = window.bill.get_item(item_to_update.id);
                if(r){
                    r.item.saved = true;
                    r.item.update();
                }
            });
        }
    }
}

/* item 'class' */
var item = function(data, saved, exploded){
    // item properties:
    // saved - this item has been sent to server already
    // exploded: do not add quantity to this item when adding the same product to bill
    this.saved = saved;
    this.exploded = exploded;

    this.bill = parent;
    this.data = data;

    this.obj = this.update(); // save jquery object for updating and stuff
}

item.prototype.update = function(){
    // create or update an item in the bill
    // product: dictionary (Product) (only if item is null - for adding new items without querying the server,
    //                                later the same item will be updated with data from the server)
    // item: dictionary (BillItem)
    // replace_obj: if null, create a new item, else replace it with the new item
    // exploded:  if true, a data-attribute will be added to prevent updating quantity of this item when adding the same product

    // get the bill header, copy it and change the data to product.whatever
    // window.items.bill_header contains a <tr> 'template' for items
    // copy it to window.items.bill_items and replace the data with useful stuff

    var tmp_obj, btn_obj;
    var new_item = window.items.bill_header.clone();
    var item = this.data;

    new_item.removeAttr("id"); // no duplicate ids in document

    // create a new item
    // product name
    $("td.bill-item-name-container p.bill-title", new_item).text(item.name);
    // unit type and amount
    $("td.bill-item-name-container p.bill-subtitle", new_item).text(item.unit_amount + " " + item.unit_type);

    // code and notes > to info box TODO
    /*tmp_obj = $("td.bill-item-name-container p.bill-subtitle", new_item);
    tmp_obj.text(item.code);
    tmp_obj.append("<br />");
    // notes
    tmp_obj.append(
        $("<input>", {type:"text", "class":"item-notes"})
    );*/

    // quantity: an edit box
    tmp_obj = $("td.bill-item-qty-container p.bill-title", new_item);
    tmp_obj.empty();
    tmp_obj.append($("<input>", {"class":"item-qty", type:"text"}).change({this_item:this}, function(e){
        var qty = get_number($(this).val(), window.data.separator);
        e.data.this_item.set_quantity(qty);
    }));

    // 'plus' button
    btn_obj = $("<input>", {type:"button", "class":"qty-button", value:"+"});
    btn_obj.click({this_item:this}, function(e){ // this is a bit awkward: 'this' has to be passed as data to function or it will be overriden by jquery (?)
        e.data.this_item.add_quantity(true);
    });
    tmp_obj.append(btn_obj);

    // 'minus' button
    btn_obj = $("<input>", {type:"button", "class":"qty-button", value:"-"});
    btn_obj.click({this_item:this}, function(e){ // this is a bit awkward: 'this' has to be passed as data to function or it will be overriden by jquery (?)
        e.data.this_item.add_quantity(false);
    });
    tmp_obj.append(btn_obj);

    // set 'fixed' fields that cannot be changed and/or remove text from 'template' row
    // price: remove the 'currency' sign
    $("td.bill-item-price-container p.bill-subtitle", new_item).empty();

    // tax: percent only
    $("td.bill-item-tax-container p.bill-subtitle", new_item).empty().append(display_number(item.tax_percent, window.data.separator, window.data.decimal_places));

    // discounts: list all discounts by type TODO
    $("td.bill-item-discount-container p.bill-title", new_item).text(item.discount_absolute);
    // the 'more' button TODO

    // other data (that will change) will be set in update_item_prices()

    // add data that we'll need later:
    // product id (to update quantity when adding new product )
    new_item.attr('data-product-id', item.product_id);
    // item id
    new_item.attr('data-item-id', item.id);
    // exploded (to NOT update quantity when adding a new product)
    if(item.exploded){
        // do not add quantity to this item
        new_item.attr('data-exploded', 'true');
    }

    // remove button
    tmp_obj = $("td.bill-item-edit", new_item);
    btn_obj = $("<button>").append("X"); // delete button
    btn_obj.click({this_item:this}, function(e){
        e.data.this_item.delete();
    });
    tmp_obj.append(btn_obj).append("<br />");

    // info button TODO
    btn_obj = $("<button>").append("?");
    tmp_obj.append(btn_obj).append("<br />");

    // 'explode' button
    if(!item.exploded){
        btn_obj = $("<button>").append("폭"); // 'explode' button
        tmp_obj.append(btn_obj);
    }

    // create a new item or replace an existing one
    if(!item.obj){
        // nothing to replace, append new
        window.items.bill_items.append(new_item);
    }
    else{
        // replace
        replace_obj.replaceWith(new_item);
    }

    // set prices etc.
    this.obj = new_item;
    this.update_prices();

    return new_item;
}

item.prototype.delete = function(){
    // delete item from bill and send a notification to server;
    // if this item has id = -1, there's no need to delete it from the server because it hasn't been sent yet,
    // just delete it from the document
    if(this.data.id == -1) this.obj.remove();
    else{
        // if it has an id, send a delete request to server and delete it when response is received
        send_data(window.data.remove_bill_item, {id:this.data.id}, window.data.csrf_token, function(response){
            if(response.status != 'ok') alert(gettext("Could not delete the item from the bill"));
            else{
                // find the item by id that's in data and remove it from bill
                var id = parseInt(response.id); // server sends id of deleted item
                var r = window.bill.get_item(id);
                if(r){
                    // delete from DOM and from bill
                    r.item.obj.remove();
                    delete bill.items[r.index];
                }
            }
        });
    }
}

item.prototype.add_quantity = function(add){
    // add or remove '1' to/from quantity (if add==true >add, etc.)
    var n;

    if(!add){ // don't set a value of 0 or less
        n = this.data.quantity.minus(Big(1));
        if(n.cmp(Big(0)) > 0) this.data.quantity = n;
    }
    else{ // do not add more items than there are in stock
        // add in increments of unit_amount
        n = this.data.quantity.plus(Big(1));
        if(n.cmp(this.data.stock) <= 0) this.data.quantity = n;
    }

    this.set_quantity(this.data.quantity);
}

item.prototype.set_quantity = function(quantity){
    // set the new quantity, check it and update if ok
    var new_qty = null;
    if(!quantity){
        alert(gettext("Wrong quantity format"));
        new_qty = Big(1);
    }
    // check if there's enough of it in stock
    if(quantity.cmp(this.data.stock) > 0){
        alert(gettext("There's not enough items in stock"));
        new_qty = this.data.stock;
    }
    // check if it's not negative or 0
    if(quantity.cmp(Big(0)) <= 0){
        alert(gettext("Quantity cannot be zero or less"));
        new_qty = Big(1);
    }
    else new_qty = quantity;

    // set the new quantity and update everything
    this.data.quantity = new_qty;

    this.update_prices();

    // mark this item as 'not saved' so that it will be updated when another item is edited
    this.saved = false;
}

item.prototype.update_prices = function(){
    var r = total_price(window.data.tax_first,
        this.data.base_price,
        this.data.tax_percent,
        [],
        this.data.quantity,
        this.data.unit_amount,
        window.data.separator
    );

    // quantity
    $("input.item-qty", this.obj).val(display_number(this.data.quantity, window.data.separator, window.data.decimal_places));

    // base price
    $("td.bill-item-price-container p.bill-title", this.obj).text(display_number(r.base, window.data.separator, window.data.decimal_places));

    // tax (only absolute value)
    $("td.bill-item-tax-container p.bill-title", this.obj).text(display_number(r.tax, window.data.separator, window.data.decimal_places));

    // discounts

    // total
    $("td.bill-item-total-container p.bill-title", this.obj).text(display_number(r.total, window.data.separator, window.data.decimal_places));
}

/* other functions */
function product_to_item(product){
    // create a bill item from product
    return {
        id:-1, // a 'fresh' item has this id
        bill_id:window.bill.data.id, // the current bill
        product_id:product.id,
        name:product.name,
        code:product.code,
        quantity:"1",
        unit_type:product.unit_type_display,
        unit_amount:product.unit_amount,
        base_price:product.price,
        tax_percent:product.tax,
        tax_absolute:null,
        stock:product.stock,
        discount_absolute:null
    }
}

function parse_item(item){
    // convert bill item's stringed numbers to Big (or integers)
    item.id = parseInt(item.id);
    item.unit_amount = get_number(item.unit_amount, window.data.separator);
    item.stock = get_number(item.stock, window.data.separator);
    item.quantity = get_number(item.quantity, window.data.separator);
    item.base_price = get_number(item.base_price, window.data.separator);
    item.tax_percent = get_number(item.tax_percent, window.data.separator);
    item.total = get_number(item.total, window.data.separator);
    
    return item;
}

function item_to_string(item){
    // convert bill item's Big numbers to strings
    item.unit_amount = display_number(item.unit_amount, window.data.separator, window.data.decimal_places)
    item.stock = display_number(item.stock, window.data.separator, window.data.decimal_places)
    item.quantity = display_number(item.quantity, window.data.separator, window.data.decimal_places)
    item.base_price = display_number(item.base_price, window.data.separator, window.data.decimal_places)
    item.tax_percent = display_number(item.tax_percent, window.data.separator, window.data.decimal_places)
    item.total = display_number(item.total, window.data.separator, window.data.decimal_places)
    
    return item;
}