function preview_image(input, preview_img_id) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();

        reader.onload = function (e) {
            $(preview_img_id).attr("src", e.target.result);
        }

        reader.readAsDataURL(input.files[0]);
    }
}
