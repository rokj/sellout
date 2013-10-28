/* bill 'class' */
Bill = function(bill_data){
    // append items to Bill
    var items = [];
    var i, ti;
    for(i = 0; i < bill_data.items.length; i++){
        ti = new Item(parse_item_data(bill_data.items[i]), true, false); // Item data, saved, not exploded
        // convert strings in data to Big() numbers
        items.push(ti);
    }
    this.items = items;

    // also save other information (but not items)
    delete bill_data.items;
    this.data = bill_data;

    // TODO: start timer interval that will save unsaved items to server every <n> seconds
    // remember last edited item so that when another one is edited, the previous (unsaved) is sent to server
    this.last_item_id = -1;
}

// Bill class methods
Bill.prototype.get_product = function(product_id){
    // return an 'unexploded' Item object for product 'product_id'
    var i;
    for(i = 0; i < this.items.length; i++){
        if (this.items[i].data.product_id == product_id) {
            if(this.items[i].exploded == false) return this.items[i];
        }
    }
    // nothing was found
    return null;
}

Bill.prototype.get_item = function(item_id){
    // return an 'Item' object with specified id
    var i;
    for(i = 0; i < this.items.length; i++){
        if(this.items[i].data.item_id == item_id){
            // return array index and Item so it can be removed from array
            return {index:i, item:this.items[i]}; // index will be useful (for deleting)
        }
    }
    // nothing was found
    return null;
}

Bill.prototype.add_product = function(product){
    // add product to Bill:
    // see if this product is already in Bill;
    // if it is, just add '1' to quantity;
    // if it's not, add a new Item

    var iexist = this.get_product(product.id); // existing 'Item' object in Bill

    if(iexist){
        // there is, add 1 to existing Item's quantity
        iexist.add_quantity(true);
    }
    else{
        // no, there's no Item for this product in Bill, update the last edited and add a new one
        // send the last edited Item to the server: it will be updated when the server answers
        var new_item = new Item(product_to_item_data(product), false, false);
        this.items.push(new_item);
    }
};

Bill.prototype.save_changes = function(){
    // search Bill items and if there are any unsaved ones, update them
    var i, ti;
    for(i = 0; i < this.items.length; i++){
        if(!this.items[i].saved){
            // this Item hasn't been saved yet, send it to server
            ti = item_data_to_string(this.items[i].data);
            send_data(window.data.edit_bill_item, ti, window.data.csrf_token, function(recv_data){
                if(recv_data.status != 'ok'){
                    alert(recv_data.message);
                }
                else{
                    // recv_data contains Item's re-calculated fields. update it
                    var item_to_update = parse_item_data(recv_data);
                    var r = window.bill.get_item(item_to_update.item_id);
                    if(r){
                        r.item.data = item_to_update; // copy new data to the 'old' Item
                        r.item.saved = true; // do not send it again until updated
                        r.item.update(); // update to reflect data from the server
                    }
                }
            });
        }
    }
};

/* Item 'class' */
Item = function (data, saved, exploded) {
    // Item properties:
    // saved - this Item has been sent to server already
    // exploded: do not add quantity to this Item when adding the same product to Bill
    this.saved = saved;
    this.exploded = exploded;

    this.data = data;

    this.obj = this.update(); // save jquery object for updating and stuff

    // after adding a new Item, send the old ones to the server
    if (!saved) window.bill.save_changes();
};

// Item class methods
Item.prototype.update = function(){
    // create or update an Item in the Bill
    // product: dictionary (Product) (only if Item is null - for adding new items without querying the server,
    //                                later the same Item will be updated with data from the server)
    // Item: dictionary (BillItem)
    // replace_obj: if null, create a new Item, else replace it with the new Item
    // exploded:  if true, a data-attribute will be added to prevent updating quantity of this Item when adding the same product

    // get the Bill header, copy it and change the data to product.whatever
    // window.items.bill_header contains a <tr> 'template' for items
    // copy it to window.items.bill_items and replace the data with useful stuff

    var tmp_obj, btn_obj;
    var new_item = window.items.bill_header.clone();
    var item = this.data;

    new_item.removeAttr("id"); // no duplicate ids in document

    // create a new Item
    // product name
    $("td.bill-item-name-container p.bill-title", new_item).text(item.name);
    // unit type and amount
    $("td.bill-item-name-container p.bill-subtitle", new_item).text(item.unit_amount + " " + item.unit_type);

    // code and notes > to info box TODO
    /*tmp_obj = $("td.Bill-Item-name-container p.Bill-subtitle", new_item);
    tmp_obj.text(Item.code);
    tmp_obj.append("<br />");
    // notes
    tmp_obj.append(
        $("<input>", {type:"text", "class":"Item-notes"})
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
    // Item id
    new_item.attr('data-item-id', item.item_id);

    // remove button
    tmp_obj = $("td.bill-item-edit", new_item);
    btn_obj = $("<button>").append("X"); // 'remove' button
    btn_obj.click({this_item:this}, function(e){
        e.data.this_item.remove();
    });
    tmp_obj.append(btn_obj).append("<br />");

    // info button TODO
    btn_obj = $("<button>").append("?");
    tmp_obj.append(btn_obj).append("<br />");

    // 'explode' button
    if(!item.exploded){
        btn_obj = $("<button>").append("폭");
        tmp_obj.append(btn_obj);
    }

    // create a new Item or replace an existing one
    if(!item.obj){
        // nothing to replace, append new
        window.items.bill_items.append(new_item);
    }
    else{
        // replace an 'old' item
        item.obj.replaceWith(new_item);
    }

    this.obj = new_item;

    // update numbers
    this.update_prices();

    return new_item;
}

Item.prototype.remove = function(){
    if(confirm(gettext("Remove this bill Item") + ": " + this.data.name + "?")){
        // remove Item from Bill and send a notification to server;
        // if this Item has id = -1, there's no need to remove it from the server because it hasn't been sent yet,
        // just remove it from the document
        if(this.data.item_id == -1) this.obj.remove();
        else{
            // if it has an id, send a remove request to server and remove it when response is received
            send_data(window.data.remove_bill_item, {id:this.data.item_id}, window.data.csrf_token, function(response){
                if(response.status != 'ok') alert(gettext("Could not remove the item from the bill"));
                else{
                    // find the Item by id that's in data and remove it from Bill
                    var id = parseInt(response.item_id); // server sends id of removed Item
                    var r = window.bill.get_item(id);
                    if(r){
                        // remove from DOM and from Bill
                        r.item.obj.remove();
                        remove_from_array(window.bill.items, r.index);
                    }
                }
            });
        }
    }
}

Item.prototype.add_quantity = function(add){
    // add or remove '1' to/from quantity (if add==true >add, etc.)
    var n, q = this.data.quantity;

    if(!add){ // don't set a value of 0 or less
        n = q.minus(Big(1));
        if(n.cmp(Big(0)) > 0) q = n;
        else return;
    }
    else{ // do not add more items than there are in stock
        // add in increments of unit_amount
        n = this.data.quantity.plus(Big(1));
        if(n.cmp(this.data.stock) <= 0) q = n;
        else return;
    }

    this.set_quantity(q);
}

Item.prototype.set_quantity = function(quantity){
    // set the new quantity, check it and update if ok
    var new_qty = null;
    if(quantity == null){
        alert(gettext("Wrong quantity format"));
        new_qty = Big(1);
    }
    // check if there's enough of it in stock
    else if(quantity.cmp(this.data.stock) > 0){
        alert(gettext("There's not enough items in stock"));
        new_qty = this.data.stock;
    }
    // check if it's not negative or 0
    else if(quantity.cmp(Big(0)) <= 0){
        alert(gettext("Quantity cannot be zero or less"));
        new_qty = Big(1);
    }
    else new_qty = quantity;

    // set the new quantity and update everything
    this.data.quantity = new_qty;

    // mark this Item as 'not saved' so that it will be updated when another Item is edited
    this.saved = false;

    this.update_prices();

    // update bill if this is the second unsaved item
    if(window.bill.last_item_id != this.data.item_id){
        window.bill.save_changes();
        window.bill.last_item_id = this.data.item_id;
    }
}

Item.prototype.update_prices = function(){
    // calculate prices only if item is not saved - if it is,
    // it has just arrived from the server and has its numbers defined already
    if(!this.saved){
        var r = total_price(window.data.tax_first,
            this.data.base_price,
            this.data.tax_percent,
            [],
            this.data.quantity,
            this.data.unit_amount,
            window.data.separator);

        // save calculated numbers
        this.data.tax_absolute = r.tax;

        // discounts

        // total
        this.data.total = r.total;
    }

    // quantity
    $("input.item-qty", this.obj).val(display_number(this.data.quantity, window.data.separator, window.data.decimal_places));

    // base price
    $("td.bill-item-price-container p.bill-title", this.obj).text(display_number(this.data.base_price, window.data.separator, window.data.decimal_places));

    // tax (only absolute value)
    $("td.bill-item-tax-container p.bill-title", this.obj).text(display_number(this.data.tax_absolute, window.data.separator, window.data.decimal_places));

    // discounts

    // total
    $("td.bill-item-total-container p.bill-title", this.obj).text(display_number(this.data.total, window.data.separator, window.data.decimal_places));
}

/* other functions */
function product_to_item_data(product){
    // create a Bill Item from product
    return parse_item_data({
        item_id:-1, // a 'fresh' Item has this id
        bill_id:window.bill.data.bill_id, // the current Bill
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
    });
}

function parse_item_data(data){
    // convert Bill Item's stringed numbers to Big (or integers)
    data.item_id = parseInt(data.item_id);
    data.unit_amount = get_number(data.unit_amount, window.data.separator);
    data.stock = get_number(data.stock, window.data.separator);
    data.quantity = get_number(data.quantity, window.data.separator);
    data.base_price = get_number(data.base_price, window.data.separator);
    data.tax_percent = get_number(data.tax_percent, window.data.separator);
    data.tax_absolute = get_number(data.tax_absolute, window.data.separator);
    data.total = get_number(data.total, window.data.separator);

    return data;
}

function item_data_to_string(item_data){
    // convert Bill Item's Big numbers to strings
    // achtung: returns item.data, not item (that has field 'data')
    return {
        item_id:item_data.item_id.toString(),
        bill_id:item_data.bill_id.toString(),
        product_id:item_data.product_id,
        unit_amount:display_number(item_data.unit_amount, window.data.separator, window.data.decimal_places),
        stock:display_number(item_data.stock, window.data.separator, window.data.decimal_places),
        quantity:display_number(item_data.quantity, window.data.separator, window.data.decimal_places),
        base_price:display_number(item_data.base_price, window.data.separator, window.data.decimal_places),
        tax_percent:display_number(item_data.tax_percent, window.data.separator, window.data.decimal_places),
        total:display_number(item_data.total, window.data.separator, window.data.decimal_places)
    }
}