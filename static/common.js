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

function tax(p_incl, p_excl, tax, separator){
    // add or remove tax from price

    // p_incl: price including tax | one of these
    // p_excl: price excluding tax | must be null
    // all parameters are strings
    var t = get_number(tax, separator);
    alert(t)    
    if(p_incl) p = p_incl;
    else p = p_excl;
    
    alert(p)
    
    p = get_number(p, separator);
    if(!p){
        alert(gettext("Check price format"));
        return null;
    }
    
    if(p_incl){ // subtract tax from price
        return p.div(Big(1).plus(t.div(100)));
    }
    else{ // add tax to price
        return p.times(Big(1).plus(t.div(100)));
    }
}

function total_product_price(tax_first, base, tax, discounts){
    // returns the total price, including tax and discounts
    
    // tax_first: true if tax is to be calculated first, else false
    // base: base price, excluding tax, string
    // tax: percentage, string
    // discounts: list of discount amounts and types in correct order (!)
    
    return "OK";
}

