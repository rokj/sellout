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
        get_bignumber(string, separator);
        return true;
    }
    catch (error) {
        return false;
    }
}

function get_bignumber(string, separator){
    // receives a string with number with decimal separator <separator> and returns BigNumber
    // bignumber: https://github.com/MikeMcl/bignumber.js/
    return BigNumber(string.replace(separator, "."))
}

function display_bignumber(number, separator, decimal_places){
    // receives a BigNumber as a parameter and returns a string with user specified decimal separator
    return number.toFixed(decimal_places).replace('.', separator);
}

function add_tax(p, t){ // returns a decimal object with added tax t
    
}

function cut_tax(P){ // returns a decimal object without tax t
    
}
