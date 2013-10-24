/* bill functions */
function get_bill(){
    // get the active bill for the current user
    get_data(window.data.get_bill_url, render_bill);
}

function product_to_item(product){
    // create a bill item from product
    return {
        id:-1, // a 'fresh' item has this id
        bill_id:window.bill.bill.id, // the current bill
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
    // convert bill item's stringed numbers to Big
    item.unit_amount = get_number(item.unit_amount, window.data.separator)
    item.stock = get_number(item.stock, window.data.separator)
    item.quantity = get_number(item.quantity, window.data.separator)
    item.base_price = get_number(item.base_price, window.data.separator)
    item.tax_percent = get_number(item.tax_percent, window.data.separator)
    item.total = get_number(item.total, window.data.separator)
    
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

function item_to_server(item){
    send_data(window.data.add_bill_item, item_to_string(item), window.data.csrf_token, function(recv_data){
        // recv_data is an item already, just convert strings to Big()s
        var item_to_update = $("#item-"+item.id.toString(), window.items.bill_items);
        
        if(item_to_update.length == 1){
            update_item(parse_item(recv_data), item_to_update, false);
        }
    });
}

function render_bill(bill){
    // draw the whole bill on page load
    window.bill.bill = bill;
    
    // if this not a new bill (there's no .new field), 
    // alert about the last item that may or may not be there
    if(!bill.new){
        alert(gettext("This is an unfinished bill from the last session, please check the last item"));
        
        // put each of the items in this loaded bill to #bill_items
        var i, item;
        for(i = 0; i < bill.items.length; i++){
            // save the last item
            window.bill.last_item = update_item(parse_item(bill.items[i]), null, false);
        }
    }
}

/* handling bill items */
function add_item(product){
    if(!window.bill.last_item){
        // this is the first item, add it immediately
        // create an item from product
        window.bill.last_item = update_item(parse_item(product_to_item(product)), null, false);
    }
    else{
        // this is not the first item
        // see if there's already an item in bill for this product
        var item_data;
        existing_item_obj = get_bill_item(product.id);
        
        if(existing_item_obj){
            item_data = existing_item_obj.data(); // .data() = item
            // there is, add <unit_amount> to existing item's quantity
            item_data.quantity = item_data.quantity.plus(Big(1));
            window.bill.last_item = update_item(item_data, existing_item_obj, false);
        }
        else{
            // no, there's no item for this product in bill, update the last edited and add a new one
            // send the last edited item to the server: it will be updated when the server answers
            item_to_server(window.bill.last_item.data());

            // a new item
            window.bill.last_item = update_item(parse_item(product_to_item(product)), null, false);
        }
    }
}

function get_bill_item(product_id){
    // returns the $("tr") object of the item we're looking for, or null if it wasn't found
    // search by product id (stored in tr.data())
    var obj = null;
    
    obj = $("tr[data-product-id='" + product_id + "']", window.items.bill_items);
    if(!obj){
        alert(gettext("A problem occured, please refresh the terminal"));
        return null; // nothing found
    }
    else{
        // there may be more than 1 element found: check which of them has no special discounts set
        // if all of them have, return null
        var found = false;
        obj.each(function(){
            if($(this).attr('data-exploded') != 'true'){
                obj = $(this);
                found = true;
                
                return false; // breaks each() 'loop'
            }
        });
        
        if(found) return obj;
        else return null;
    }
}

function update_item(item, replace_obj, exploded){
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

    new_item.attr("id", "item-"+item.id.toString()); // no duplicate ids in document
    new_item.data(item);
    
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
    
    // add/remove quantity
    function change_qty(add, obj){ // if 'add' is false subtract
        if(!add){ // don't set a value of 0 or less
            n = item.quantity.minus(Big(1));
            if(n.cmp(Big(0)) > 0) item.quantity = n;
        }
        else{ // do not add more items than there are in stock
            // add in increments of unit_amount
            n = item.quantity.plus(Big(1));
            if(n.cmp(item.stock) <= 0) item.quantity = n;
        }
        
        // update the looks
        obj.val(display_number(item.quantity, window.data.separator, window.data.decimal_places));
        update_item_prices(item, new_item);
    }
    
    // quantity: an edit box
    tmp_obj = $("td.bill-item-qty-container p.bill-title", new_item);
    tmp_obj.empty();
    tmp_obj.append($("<input>", {"class":"item-qty", type:"text"})
        .change(function(){
            // set the new quantity, check it and update if ok
            new_qty = get_number($(this).val(), window.data.separator);
            if(!new_qty){
                alert(gettext("Wrong quantity format"));
                new_qty = Big(1);
            }
            // check if there's enough of it in stock
            if(new_qty.cmp(item.stock) > 0){
                alert(gettext("There's not enough items in stock"));
                new_qty = item.stock;
            }
            // check if it's not negative or 0
            if(new_qty.cmp(Big(0)) <= 0){
                alert(gettext("Quantity cannot be zero or less"));
                new_qty = Big(1);
            }
            // set the new quantity and update everything
            item.quantity = new_qty;
            $(this).val(display_number(item.quantity, window.data.separator, window.data.decimal_places));
            update_item_prices(item, new_item);
        }));
    
    // 'plus' button
    btn_obj = $("<input>", {type:"button", "class":"qty-button", value:"+"});
    btn_obj.click(function(){ change_qty(true, $("input.item-qty", $(this).parent())); });
    tmp_obj.append(btn_obj);
    
    // 'minus' button
    btn_obj = $("<input>", {type:"button", "class":"qty-button", value:"-"});
    btn_obj.click(function(){ change_qty(false, $("input.item-qty", $(this).parent())); });
    tmp_obj.append(btn_obj);
    
    // set 'fixed' fields that cannot be changed
    // unit amount and type
    $("td.bill-item-qty-container p.bill-subtitle", new_item).empty().append(item.unit_type);
    // price will be set later
    // tax: percent only
    $("td.bill-item-tax-container p.bill-title", new_item).empty().append(display_number(item.tax_percent, window.data.separator, window.data.decimal_places));
    
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
    if(exploded){
        // do not add quantity to this item
        new_item.attr('data-exploded', 'true');
    }
    
    // remove button
    tmp_obj = $("td.bill-item-edit", new_item);
    btn_obj = $("<button>").append("X"); // delete button
    btn_obj.click(function(){
        // if this item has id = -1, there's no need to delete it from the server because it hasn't been sent yet,
        // just delete it from the document
        var tr_obj = $(this).parent().parent(); // parent #1: td, parent #2: tr <- delete that
        
        if(item.id == -1) tr_obj.remove();
        else{
            // if it has an id, send a delete request to server and delete it when response is received
            send_data(window.data.remove_bill_item, {id:item.id}, window.data.csrf_token, function(response){
                if(response.status != 'ok') alert(gettext("Could not delete the item from the bill"));
                else tr_obj.remove();
            });
        }
    });
    tmp_obj.append(btn_obj).append("<br />");
    
    // info button TODO
    btn_obj = $("<button>").append("?");
    tmp_obj.append(btn_obj).append("<br />");
    
    // 'explode' button
    if(!exploded){
        btn_obj = $("<button>").append("폭"); // 'explode' button
        tmp_obj.append(btn_obj);
    }
    
    // create a new item or replace an existing one
    if(!replace_obj){
        // nothing to replace, append new
        window.items.bill_items.append(new_item);
    }
    else{
        // replace
        replace_obj.replaceWith(new_item);
    }
    
    // set prices etc.
    update_item_prices(item, new_item);
    
    return new_item;
}

function update_item_prices(item, obj){
    // item - 'json'
    // obj - jquery object, bill item
    
    var r = total_price(window.data.tax_first, item.base_price, item.tax_percent, [], item.quantity, window.data.separator);
    
    // quantity
    $("input.item-qty", obj).val(display_number(item.quantity, window.data.separator, window.data.decimal_places));

    // base price
    $("td.bill-item-price-container p.bill-title", obj).text(display_number(r.base, window.data.separator, window.data.decimal_places));
    
    // tax (only absolute value)
    $("td.bill-item-tax-container p.bill-subtitle", obj).text(display_number(r.tax, window.data.separator, window.data.decimal_places));
    
    // discounts
    
    // total
    $("td.bill-item-total-container p.bill-title", obj).text(display_number(r.total, window.data.separator, window.data.decimal_places));
}
