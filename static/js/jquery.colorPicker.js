// works only on one element at a time
(function($){
    $.fn.colorPicker = function(colors, container, callback){
        // an input type=hidden is expected
        // colors is an array of 6-char RGB colors
        // container is a div that will contain all colors
        var input = $(this);

        function set_color(element, color){
            element.css("background-color", "#" + color);
        }

        function get_id(color){
            return "colorPicker_" + color;
        }

        if(input.val() != ""){
            // set default color if it's not there yet
            set_color(input, colors[0]);
        }

        // create a grid that will contain all colors
        var l = colors.length;

        // number of buttons
        var m = Math.ceil(Math.sqrt(l)); // number of columns
        var n = Math.floor(Math.sqrt(l));

        // size of buttons: make them square (choose the minimum size)
        var size = Math.max(container.width()/m, container.height()/n);

        // create a container for each color
        var e, elements = [];
        for(var i = 0; i < colors.length; i++){
            e = $("<div>", {
                "class": "color-button",
                "data-color": colors[i],
                "id": get_id(colors[i])
                });
            set_color(e, colors[i]);

            elements.push(e);

            e.width(size);
            e.height(size);

            e.appendTo(container);

            // chosen color (or default)
            if(input.val() == colors[i] ||
               (input.val() == "" && i == 0)){
                e.addClass("selected");
            }
        }

        // register events
        $(".color-button", container).click(function(){
            // remove the 'selected' class from the currently selected color
            $(".selected", container).removeClass("selected");
            // add class to current element
            $(this).addClass("selected");
            input.val($(this).attr("data-color"));

            // anything else?
            if(callback) callback()
        });

    };
}(jQuery));