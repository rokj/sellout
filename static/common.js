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

function getBase64Image(img_obj_id, format){
	// encode the image selected for upload to base64
	
	// imgElem must be on the same server -
	// otherwise a cross-origin error will be thrown "SECURITY_ERR: DOM Exception 18"
	img_obj = document.getElementById(img_obj_id);
	
    var canvas = document.createElement("canvas");
    canvas.width = img_obj.clientWidth;
    canvas.height = img_obj.clientHeight;
    var ctx = canvas.getContext("2d");
    ctx.drawImage(img_obj, 0, 0);
    return canvas.toDataURL("image/" + format);
}
