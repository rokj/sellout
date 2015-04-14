(function($){
    $.fn.customFileInput = function(image_obj){
        return this.each(function(){
            // $(this): the input button
            // image_obj: the image that should do the same as the file input

            // make the original input transparent and float it above the image
            $(this).css("opacity", 0);
            $(this).css("position", "absolute");
            $(this).css("z-index", "2");

            // image position
            // make the whole thing as wide as the button
            $(this).width(image_obj.width());
            $(this).height(image_obj.height());
            $(this).css("top", image_obj.position().top);
            $(this).css("left", image_obj.position().left);
        });
    };
}(jQuery));