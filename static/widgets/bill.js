/* bill functions */
function add_to_bill(product){
    // get the bill header, copy it and change the data to product.whatever
    // window.items.bill_header contains a <tr> 'template' for items
    // copy it to window.items.bill_items and replace the data with useful stuff
    var tmp_obj;
    var new_item = window.items.bill_header.clone();

    new_item.removeAttr("id");
    
    // see if this product is already in the bill
    if(product.id in window.products_in_bill){
        // it is, get that item and add 1 to quantity
        tmp_obj = $("td.bill-item-qty-container input.qty", window.products_in_bill[product.id]);
        tmp_obj.val(parseInt(tmp_obj.val()) + 1);
    }
    else{
        // add a new item to bill
        // product name
        $("td.bill-item-name-container p.bill-title", new_item).text(product.name);
        // code
        $("td.bill-item-name-container p.bill-subtitle", new_item).text(product.code);
        // quantity: an edit box
        tmp_obj = $("<input>", {"class":"qty"});
        $("td.bill-item-qty-container p.bill-title", new_item).empty()
            .append(tmp_obj.spinner().val(1)); // quantity: 1 to begin with
        $("td.bill-item-qty-container p.bill-subtitle", new_item)
            .text("[" + product.unit_type_display + "]"); // unit type
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
        
        // add to bill
        window.items.bill_items.append(new_item);
        
        // add to window.products_in_bill
        window.products_in_bill[product.id] = new_item;
    }
}
