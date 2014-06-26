(function($){
    $.fn.customFileInput = function(label){
        return this.each(function(){
            // delete everything from parent and redraw
            var parent = $(this).parent();
            //$(this).detach();
            //parent.empty();

            parent.css("position", "relative");
            parent.height($(this).height());

            // append a style-able browse button
            var browse_button = $("<input>", {
                type: 'button',
                "class": "custom-file-input",
                value: label
            });
            parent
                .addClass("custom-file-input")
                .append($(this))
                .append(browse_button);

            // make the original input transparent and float it above the parent
            $(this).css("opacity", 0);
            $(this).css("position", "absolute");
            $(this).css("z-index", "2");

            // move it over the browse button
            $(this).css("left", "0");

            // make the whole thing as wide as the button
            $(this).width(browse_button.outerWidth());
            $(this).height(browse_button.outerHeight());
        });
    };
}(jQuery));