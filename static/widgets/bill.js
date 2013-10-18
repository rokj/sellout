/* bill functions */
function get_bill(){
    // get the active bill for the current user
    get_data(window.data.get_bill_url, render_bill);
}

function render_bill(bill){
    // draw the whole bill on page load
    window.bill.bill = bill;
    
    // if this not a new bill (there's no .new field), 
    // alert about the last item that may or may not be there
    if(!bill.new){
        alert(gettext("This is an unfinished bill from the last session, please check the last item"));
        
        // put each of the items in this loaded bill to #bill_items
        var i;
        for(i = 0; i < bill.items.length; i++){
            update_item(bill.items[i], null, null);
        }
    }
}

/* handling bill items */
function add_item(product){
    // send the last edited item to the server and put the current 'product' in the list

    if(window.bill.last_item){
        // send the last edited item to the server
        // JSON to send:
        // {'bill':bill_id, 'product_id':<id>, 'qty':<qty>, 'notes':<notes>}
        data_to_send = {
            bill_id:window.bill.bill.id,
            product_id:product.id,
            qty:"1", // TODO BigNumber
            notes:"SOMENOTES"
        }
        
        // send request to server
        send_data(window.data.add_bill_item, data_to_send, window.data.csrf_token, function(recv_data){
            update_item(recv_data, window.bill.last_item, false);
        });
    } // while waiting for response, draw the item
    
    // create a new item for the currently 'added' product
    // only add it if there's not such item in the bill yet
    // if there is one, add 1 to Quantity
    // when checking for new items, do not add quantity to an item that has some custom discounts set -
    // rather add a new item without those discounts
    if(get_bill_item(product.id) == null){
        // item not found, add a new one to the product
        last_item = update_item(null, null, false); // add 'unexploded' item
        window.items.bill_items.append(last_item);
    }
    else{
        // item found, add 1 to its quantity
        alert("updating item")
    }
    
    // set last item to this
    window.bill.last_item = last_item;
}

function get_bill_item(product_id){
    // returns the $("tr") object of the item we're looking for, or null if it wasn't found
    // search by product id (stored in tr.data())
    var obj = null;
    
    obj = $("tr[data-product-id='" + product_id + "']");
    if(!obj) return null; // nothing found
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
    // item: dictionary (BillItem)
    // replace_obj: if null, create a new item, else replace it with the new item
    // exploded:  if true, a data-attribute will be added to prevent updating quantity of this item when adding the same product

    // get the bill header, copy it and change the data to product.whatever
    // window.items.bill_header contains a <tr> 'template' for items
    // copy it to window.items.bill_items and replace the data with useful stuff
    var tmp_obj, btn_obj;
    var new_item = window.items.bill_header.clone();

    if(!item){
        // no stuff from server has been received *yet*
        // create an empty 'item'
        item = {
            name:"***",
            code:"***",
            quantity:"***",
            unit_type:"***",
            base_price:"***",
            tax_absolute:"***",
            discount_absolute:"***",
            product_id:"***"
        }
    }

    new_item.removeAttr("id"); // no duplicate ids in document

    // create a new item    
    // product name
    $("td.bill-item-name-container p.bill-title", new_item).text(item.name);
    // code
    $("td.bill-item-name-container p.bill-subtitle", new_item).text(item.code);
    
    // quantity: an edit box
    tmp_obj = $("td.bill-item-qty-container p.bill-title", new_item);
    tmp_obj.append($("<input>", {"class":"qty", type:"text"}).val(item.quantity));
    // 'plus' button
    btn_obj = $("<input>", {type:"button", "class":"qty-button", value:"+"});
    tmp_obj.append(btn_obj);
    // 'minus' button
    btn_obj = $("<input>", {type:"button", "class":"qty-button", value:"-"});
    tmp_obj.append(btn_obj);
    // unit type        
    $("td.bill-item-qty-container p.bill-subtitle", new_item).empty().append("[" + item.unit_type + "]");
    
    // price
    $("td.bill-item-price-container p.bill-title", new_item).text(item.base_price);
    $("td.bill-item-price-container p.bill-subtitle", new_item).remove();
    
    // tax
    $("td.bill-item-tax-container p.bill-title", new_item).text(item.tax_percent); // percent
    $("td.bill-item-tax-container p.bill-subtitle", new_item).text(item.tax_absolute); // absolute value
    
    // discounts: list all discounts by type
    $("td.bill-item-discount-container p.bill-title", new_item).text(item.discount_absolute);
    
    // total
    $("td.bill-item-total-container p.bill-title", new_item).text(item.total);
    
    // add data that we'll need later:
    // product id (to update quantity when adding new product )
    new_item.attr('data-product-id', item.product_id);
    // exploded (to NOT update quantity when adding a new product)
    if(exploded){
        // do not add quantity to this item
        new_item.attr('data-exploded', 'true');
    }
    
    // init ui 'gadgets'
    
    
    // create a new item or replace an existing one
    if(!replace_obj){
        // nothing to replace, append new
        window.items.bill_items.append(new_item);
    }
    else{
        // replace
        replace_obj.replaceWith(new_item);
    }
    
    
    return new_item;
}

