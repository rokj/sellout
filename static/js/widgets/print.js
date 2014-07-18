function format_small_receipt(g, bill){
    // g: terminal globals
    // bill: Bill() objects
    var receipt = g.items.small_receipt_template.clone().removeAttr("id");

    // company details:
    // logo:
    if(g.objects.terminal.register.print_logo && g.items.company_monochrome_logo){
        // if company's logo exists, append
        $(".receipt-logo", receipt).append(g.items.company_monochrome_logo);
    }

    // issuing company details: create some
    $(".issuing.company-details-name", receipt).text(g.data.company.name);

    $(".issuing.company-details-1", receipt).html(
        escape(g.data.company.street) + "<br/>" +
        escape(g.data.company.postcode) + " " + escape(g.data.company.city) +
        escape(g.data.company.state) + " " + escape(g.data.company.country)
    );

    $(".issuing.company-details-2", receipt).html(
        escape(g.data.company.phone) + "<br/>" +
        escape(g.data.company.vat_no) + "<br/>" +
        escape(g.data.company.website)
    );

    // the same for client company (if selected)

    // register location (if selected in register settings)
    if(g.objects.terminal.register.print_location && g.objects.terminal.register.location){
        $(".register-location", receipt).text(g.objects.terminal.register.location);
    }

    // bill items:
    var items_list = $(".items-body", receipt);
    var item_template_1 = $(".receipt-row.first", receipt);
    var item_template_2 = $(".receipt-row.second", receipt);
    var i, item, io1, io2;

    for(i = 0; i < bill.items.length; i++){
        // get item data
        item = bill.items[i];

        // clone the two rows
        io1 = item_template_1.clone();
        io2 = item_template_2.clone();

        // name
        $(".item-name", io1).text(item.name);

        // quantity and unit type
        if(item.unit_type != 'Piece') $(".item-unit", io1).text(item.unit_type);

        $(".item-quantity", io1).text(item.quantity);

        // amount
        $(".item-amount", io1).text(item.total);

        $(".item-price", io2).text(item.base_price);
        $(".item-tax", io2).text(item.tax_percent + "%");
        $(".item-discount", io2).text(item.discount_absolute);

        // append to items_list
        items_list.append(io1);
        items_list.append(io2);
    }

    // currency
    $(".receipt-currency", receipt).text(g.config.currency);
    // the grand total
    $(".receipt-total", receipt).text(bill.total);

    // cashier name
    $(".receipt-cashier-name", receipt).text(g.data.user_name);
    $(".receipt-datetime", receipt).text(
        today(g.config.date_format) + " " + now(g.config.time_format)
    );

    // the calling function will handle the printing
    return receipt;
}