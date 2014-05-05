function preview_image(input, preview_img_id, max_width, max_height) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();

        reader.onload = function (e) {
            img_obj = $(preview_img_id);
            img_obj.attr("src", e.target.result);
            img_obj.css("max-width", max_width);
            img_obj.css("max-height", max_height);
        };

        reader.readAsDataURL(input.files[0]);
    }
}

function escape(text){
    if(!text) return ""; // avoid writing "undefined"
    
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

function remove_from_array(array, index){
    // kudos: http://stackoverflow.com/questions/5767325/remove-specific-element-from-an-array
    if(index > -1) {
        array.splice(index, 1); // original array is modified
        return true;
    }
    else return false;
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

function set_draggable(obj, items_selector, easing_time){
    // items_selector (string): items that should be fitted into view
    // obj: the inner div of the 'scrolling trinity':
    //  div scroll_outer (prevents selection)
    //    div scroll inner (overflow-x: hidden)
    //      div content ('infinite' width)

    var params = {
        // Kudos:
        // http://stackoverflow.com/questions/6602568/jquery-ui-draggable-deaccelerate-on-stop
        helper: function () {
            return $("<div>").css("opacity", 0);
        },
        drag: function (event, ui) {
            // the position of parent obviously has to be taken into account
            var pos = ui.helper.position().left - obj.parent().position().left;
            $(this).stop().animate({left: pos},
                easing_time,
                'easeOutCirc',
                function () {
                    // check if this has scrolled past the last
                    // (first) button
                    var all_buttons = $(items_selector, obj);
                    var first_button = all_buttons.filter(":first");
                    var last_button = all_buttons.filter(":last");
                    var container = obj.parent();

                    if(first_button.length < 1 || last_button.length < 1) return;

                    // if the whole scroller's width is less than
                    // container's, always slide it back to left border
                    if (first_button.position().left + last_button.position().left + last_button.outerWidth() < container.width()) {
                        first_button.parent().animate({left: 0}, "fast");
                    }
                    else {
                        if (first_button.offset().left > container.offset().left) {
                            first_button.parent().animate({left: 0}, "fast");
                        }
                        else if (last_button.offset().left + last_button.outerWidth() < container.offset().left + container.width()) {
                            first_button.parent().animate({left: -last_button.position().left + container.width() - last_button.outerWidth()}, "fast");
                        }
                    }
                });
        },
        axis: "x"
    };

    obj.draggable(params);
}

function error_message(title, message){
    // create a div for error dialog
    var dlg_obj = $("<div>");
    var msg_obj = $("<p>", {"class": "error-message"});

    if(!title) title = gettext("Error");

    msg_obj.text(message);

    dlg_obj.append(msg_obj);

    dlg_obj.dialog({
        modal: true,
        width: 350,
        title: title,
        buttons:[ {text: gettext("OK"), click: function(){ $(this).dialog("close"); }} ]
    });
}

function confirmation_dialog(title, text, yes_action, no_action){
    // returns "true" if the user clicked 'yes' or false otherwise
    var dlg = $("<div>");

        dlg.text(text);

        dlg.dialog({
            modal: true,
            width: 430,
            draggable: false,
            title: title,
            buttons: [
                { text: gettext("Yes"), click: function(){
                    if(yes_action) yes_action.call();

                    dlg.dialog("destroy");
                }},
                { text: gettext("No"), click: function(){
                    if(no_action) no_action.call();

                    dlg.dialog("destroy");
                }} ]
        });

    return dlg;
}

function get_url_hash() {
    return window.location.hash.replace(/^#/,'');
}