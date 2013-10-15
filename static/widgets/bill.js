/* bill functions */
function add_to_bill(product){
    // get the bill header, copy it and change the data to product.whatever
    // window.items.bill_header contains a <tr> 'template' for items
    // copy it to window.items.bill_items and replace the data with useful stuff
    var tmp_obj, btn_obj;
    var new_item = window.items.bill_header.clone();

    new_item.removeAttr("id");
    
    // see if this product is already in the bill
    if(product.id in window.products_in_bill){
        // it is, get that item and add 1 to quantity
        tmp_obj = $("td.bill-item-qty-container input.qty", window.products_in_bill[product.id]);
        // TODO: parse BigNumber and add 1
        tmp_obj.val(parseInt(tmp_obj.val()) + 1);
    }
    else{
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
        btn_obj.click(function(){
            var o = $("input.qty", $(this).parent());
            
            alert(o.val())
            
            if(check_number(o.val(), window.data.separator)){
                var q = get_bignumber(o.val(), window.data.separator);
                
                alert(q.plus(1).toString())
            }
            
        });
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
        
        // add to bill
        window.items.bill_items.append(new_item);
        
        // init ui 'gadgets'
        
        
        // add to window.products_in_bill
        window.products_in_bill[product.id] = new_item;
    }
}

