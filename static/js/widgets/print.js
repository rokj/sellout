function format_small_receipt(bill, data){
    // g: terminal globals
    // bill: Bill() objects

    var g = bill.g;
    var receipt = g.items.small_receipt_template.clone().removeAttr("id");

    // company details:
    // logo:
    if(g.data.company.logo_url){
        // if company's logo exists, append
        $(".receipt-logo", receipt).append(g.items.company_logo);
    }

    // company details: create some
    $("receipt-company-details-1", receipt).text(
        escape(g.data.company.name) + "<br/>" +
        escape(g.data.company.street) + "<br/>" +
        escape(g.data.company.postcode) + " " + escape(g.data.company.city)
    );
    $("receipt-company-details-2", receipt).text(
        escape(g.data.company.phone) + "<br/>" +
        escape(g.data.company.website) + "<br/>" +
        escape(g.data.company.vat_no)
    );

    // bill items:
    var items_list = $("tbody", receipt);
    var item_template_1 = $(".receipt-row.first", receipt);
    var item_template_2 = $(".receipt-row.second", receipt);
    var i, item, io1, io2;

    for(i = 0; i < data.items.length; i++){
        // get item data
        item = data.items[i];

        // clone the two rows
        io1 = item_template_1.clone();
        io2 = item_template_2.clone();

        // name
        $(".item-name", io1).text(item.name);
        // quantity
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
    $(".receipt-grand-total", receipt).text(data.grand_total);

    // cashier name
    $(".receipt-cashier", receipt).text(g.data.user_name);
    $(".receipt-datetime", receipt).text(
        today(g.config.date_format) + " " + now(g.config.time_format)
    );

    // the calling function will handle the printing
    return receipt;
}