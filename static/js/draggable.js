/*
 * functions for draggable boxes:
 *   horizontal and vertical (very similar, but separate functions)
 *  */

/* common functions to both horizontal and vertical */
function enable_clicking(obj){
    obj.removeClass("no-click");
}

function disable_clicking(obj){
    obj.addClass("no-click");
}

/*
 * horizontal draggable
 */
function set_horizontal_draggable(obj, items_selector, easing_time){
    // items_selector (string): items that should be fitted into view
    // obj: the inner div of the 'scrolling trinity':
    //  div scroll_outer (prevents selection)
    //    div scroll inner (overflow-x: hidden)
    //      div content ('infinite' width)

    function check_boundaries(){
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
            first_button.parent().animate({left: 0}, "fast", function(){enable_clicking(obj);});
        }
        else {
            if (first_button.offset().left > container.offset().left) {
                first_button.parent().animate({left: 0}, "fast", function(){enable_clicking(obj);});
            }
            else if (last_button.offset().left + last_button.outerWidth() < container.offset().left + container.width()) {
                first_button.parent().animate({left: -last_button.position().left + container.width() - last_button.outerWidth()},
                    "fast", function(){enable_clicking(obj);});
            }
            else{
                enable_clicking(obj);
            }
        }
    }

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
                check_boundaries);
            },
        start: function(event, ui){
            disable_clicking(obj);
        },
        axis: "x"
    };

    // the draggable object
    obj.draggable(params);

    // register mousewheel events
    obj.parent().on("mousewheel", function(e){
        var interval = 50; // move by this number of pixels
        var timeout_duration = 500;

        var current_position = obj.position().left;

        // always use deltaY events, the usual vertical scrolling
        obj.css({left: current_position + interval*e.deltaY});

        // see if there's a timeout for checking boundaries
        if(obj.data().timeout){
            clearTimeout(obj.data().timeout);

            obj.data({
                timeout: setTimeout(check_boundaries, timeout_duration)
            });
        }
        else{
            // set timeout to check position of the object after scrolling
            obj.data({
                timeout: setTimeout(check_boundaries, timeout_duration)
            });
        }
    });
}

function horizontal_scroll_into_view(btn){
    // ACHTUNG: only for horizontal scrolling
    // scrolls the object into view;
    // the object is a category/product button in a container what was set_horizontal_draggable().
    var scroller = btn.parent();
    var frame = scroller.parent();

    // scrolling left: if button.left is less than container.left, scroll it into view
    if (btn.offset().left < frame.offset().left) {
        scroller.animate({left : -btn.position().left});
    }
    else if(btn.offset().left + btn.outerWidth() > frame.offset().left + frame.width()) {
        // scrolling right: if button.left + button.width > container.left + container.width, scroll it into view
        scroller.animate({left:-btn.position().left + frame.width() - btn.outerWidth()});
    }
}

/*
 * vertical draggable
 */
function set_vertical_draggable(obj, items_selector, easing_time){
    // see comments for the horizontal version
    function check_boundaries(){
        // check if this has scrolled past the last
        // (first) button
        var all_buttons = $(items_selector, obj);
        var first_button = all_buttons.filter(":first");
        var last_button = all_buttons.filter(":last");
        var container = obj.parent();

        if(first_button.length < 1 || last_button.length < 1){
            return;
        }

        // if the whole scroller's height is less than
        // container's, always slide it back to top border

        if (first_button.position().top + last_button.position().top + last_button.outerHeight() < container.height()){
            obj.animate({top: 0}, "fast", function(){enable_clicking(obj);});
        }
        else {
            if (first_button.offset().top > container.offset().top) {
                obj.animate({top: 0}, "fast", function(){enable_clicking(obj);});
            }
            else if (last_button.offset().top + last_button.height() < container.offset().top + container.height()) {
                obj.animate({
                    top: -last_button.position().top + container.height() - last_button.height()},
                    "fast",
                    function(){enable_clicking(obj);}
                );
            }
            else{
                enable_clicking(obj);
            }
        }
    }

    obj.draggable({
        helper: function () {
            return $("<div>").css("opacity", 0);
        },
        drag: function (event, ui) {
            // the position of parent obviously has to be taken into account
            var pos = ui.helper.offset().top - obj.parent().offset().top;
            $(this).stop().animate({top: pos},
                easing_time,
                'easeOutCirc',
                check_boundaries);
        },
        start: function(){
            // prevent clicking while dragging (must be handled in its children)
            disable_clicking(obj);
        },
        axis: "y"
    });

    // register mousewheel events
    obj.parent().on("mousewheel", function(e){
        var interval = 30; // move by this number of pixels
        var timeout_duration = 500;

        var current_position = obj.position().top;

        // always use deltaY events, the usual vertical scrolling
        obj.css({top: current_position + interval*e.deltaY});

        // see if there's a timeout for checking boundaries
        if(obj.data().timeout){
            clearTimeout(obj.data().timeout);

            obj.data({
                timeout: setTimeout(check_boundaries, timeout_duration)
            });
        }
        else{
            // set timeout to check position of the object after scrolling
            obj.data({
                timeout: setTimeout(check_boundaries, timeout_duration)
            });
        }
    });
}

function vertical_scroll_into_view(obj){
    var frame = obj.parent().parent(); // the parent of the scrolling container
    var container = obj.parent();

    var border_top = 0;
    var border_bottom = frame.outerHeight(true);

    var container_position = container.position().top;

    var button_position = obj.position().top;
    var button_height = obj.outerHeight(true);

    if(container_position + button_position < border_top){
        // scroll the bill down so that the selected item is the first on the list
        container.animate({
            top: -button_position
        }, "fast");
    }
    else if((container_position + button_position + button_height) > border_bottom){

        // scroll the bill up so that the selected item is the last on the list
        container.animate({
            top: - button_position + border_bottom - button_height
        }, "fast");
    }
}