function preview_image(input, preview_img_id, max_width, max_height) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();

        reader.onload = function (e) {
            img_obj = $(preview_img_id) 
            img_obj.attr("src", e.target.result);
            img_obj.css("max-width", max_width);
            img_obj.css("max-height", max_height);
        }

        reader.readAsDataURL(input.files[0]);
    }
}

function escape(text){
    if(!text) return "" // avoid writing "undefined"
    
    // kudos: 
    // http://stackoverflow.com/questions/24816/escaping-html-strings-with-jquery
    var entityMap = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': '&quot;',
        "'": '&#39;',
        "/": '&#x2F;'
    };

    return String(text).replace(/[&<>"'\/]/g, function (s) {
        return entityMap[s];
    });
}

function get_size(element){ // get computed element size before it's inserted into document
    element.hide();
    $("body").append(element); // add to DOM, in order to read the CSS property
    try {
        return [element.outerWidth(), element.outerHeight()];
    } finally {
        element.remove(); // and remove from DOM
    }
}

function check_number(string, separator){
    // returns true if string parsed to BigNumber successfully, or false otherwise
    try{
        get_number(string, separator);
        return true;
    }
    catch (error) {
        return false;
    }
}

function get_number(string, separator){
    // receives a string with number with decimal separator <separator> and returns BigNumber
    // bignumber: https://github.com/MikeMcl/bignumber.js/
    try{
        return Big(string.replace(separator, "."));
    }
    catch(error){
        return null;
    }
}

function display_number(number, separator, decimal_places){
    // receives a BigNumber as a parameter and returns a string with user specified decimal separator
    return number.toFixed(decimal_places).replace('.', separator);
}

function do_tax(p_incl, p_excl, tax){
    // add or remove tax from price

    // p_incl: price including tax | one of these
    // p_excl: price excluding tax | must be null
    // all parameters are Big()numbers
    if(p_incl) p = p_incl;
    else p = p_excl;
    
    if(p_incl){ // subtract tax from price
        return p.div(Big(1).plus(t.div(Big(100))));
    }
    else{ // add tax to price
        return p.times(Big(1).plus(t.div(Big(100))));
    }
}

function total_price(tax_first, base, tax, discounts, separator){
    // calculates total price
    // parameters:
    // tax_first: if true, first tax is added and then discounts, else v.v.
    // base: base price, Big()
    // tax: tax in percent, Big()
    // discounts: list of discounts (from py's discount_to_dict())
    // returns Big() calculated price
    // if anything fails, returns null
    function subtract_discounts(p, d){ // price, discounts[]
        for(var i = 0; i < d.length; i++){
            if(d[i].type == 'Absolute'){
                p = p.minus(get_number(d[i].amount, separator));
            }
            else{
                p = p.div(Big(1).plus(get_number(d[i].amount, separator).div(Big(100))));
            }
        }
        return p;
    }
    
    if(tax_first){
        // add tax
        price = do_tax(null, price, t);
        
        if(!price)return;
        // subtract discounts
        price = subtract_discounts(price, discounts);
        if(!price) return null;
    }
    else{
        // subtract discounts
        price = subtract_discounts(price, discounts);
        if(!price) return;
        // add tax
        price = tax(null, price, t);
        if(!price) return;
    }
    
    return price;
}

