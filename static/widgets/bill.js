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
    }
    
}

/* handling bill items */
function update_item(item_obj, item_data){ // updates the bill item after it was received from the server
    
}

function edit_item(){ // sends the last item to the server and creates 
    
}

function create_item(item){ // creates a new row in the bill table and fills it with item's data
    
}

function add_item(product){
    // send the last edited item to the server and put the current 'product' in the list

    if(window.bill.last_item){
        // send the last edited item to the server
        // JSON to send:
        // {'bill':bill_id, 'product_id':<id>, 'qty':<qty>, 'notes':<notes>}
        data_to_send = {
            
        }
    }
    
    // create a new item for the currently 'added' product
    // only add it if there's not such item in the bill yet
    // if there is one, add 1 to Quantity
    // when checking for new items, do not add quantity to an item that has some custom discounts set -
    // rather add a new item without those discounts
    if(get_bill_item(product.id) == null){
        // item not found, add a new to the product
        create_item(product, false); // add 'unexploded' item
    }
    else{
        // item found, add 1 to its quantity
        alert("updating item")
    }
    
    // set last item to this
}

function get_bill_item(product_id){
    // returns the $("tr") object of the item we're looking for, or null if it wasn't found
    // search by product id (stored in tr.data())
    var obj = null;
    
    obj = $("tr[data-id='" + product_id + "']");
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

function create_item(product, exploded){
    // creates a new table row in the bill table

    // get the bill header, copy it and change the data to product.whatever
    // window.items.bill_header contains a <tr> 'template' for items
    // copy it to window.items.bill_items and replace the data with useful stuff
    var tmp_obj, btn_obj;
    var new_item = window.items.bill_header.clone();

    new_item.removeAttr("id");
    
    // add a new item to bill
    // product name
    $("td.bill-item-name-container p.bill-title", new_item).text(product.name);
    // code
    $("td.bill-item-name-container p.bill-subtitle", new_item).text(product.code);
    // quantity: an edit box
    tmp_obj = $("td.bill-item-qty-container p.bill-title", new_item);
    tmp_obj.append($("<input>", {"class":"qty", type:"text"}).val(1));
    
    // 'plus' button
    btn_obj = $("<input>", {type:"button", "class":"qty-button", value:"+"});
    tmp_obj.append(btn_obj);
    
    // 'minus' button
    btn_obj = $("<input>", {type:"button", "class":"qty-button", value:"-"});
    tmp_obj.append(btn_obj);

    // add unit type        
    $("td.bill-item-qty-container p.bill-subtitle", new_item).empty().append("[" + product.unit_type_display + "]");
    // price
    $("td.bill-item-price-container p.bill-title", new_item).text(product.price);
    $("td.bill-item-price-container p.bill-subtitle", new_item).remove();
    // tax
    $("td.bill-item-tax-container p.bill-title", new_item).text(product.tax);
    $("td.bill-item-tax-container p.bill-subtitle", new_item).remove();
    // discounts: list all discounts by type
    $("td.bill-item-discount-container p.bill-title", new_item).text(
        product.discount_percent + "%\n" + // first line: percent
        product.discount_absolute + " " + window.data.currency // second line: absolute
    );
    
    // total
    //alert(get_bignumber(product.price, window.data.separator).toString())
    
    // add data that we'll need later
    new_item.attr('data-id', product.id);
    if(exploded){
        // do not add quantity to this item
        new_item.attr('data-exploded', 'true');
    }
    
    // add to bill
    window.items.bill_items.append(new_item);
    
    // init ui 'gadgets'
}

