// Big() setup
Big.RM = 1; // ROUND_HALF_UP, away from zero (must match settings in python)

/*

    the calculate() function expects items and discounts in this format:

    var r_discount = {
        amount: Big(20),
        type: 'Percent'
    };

    var a_discount = {
        amount: Big(1),
        type: 'Absolute'
    };

    var items = [
        {
            // these never change, they are defined in database
            serial: <serial>,
            quantity: Big(2),
            base: Big(10), // this is without discounts and without tax
            tax_rate: Big(20), // price in percentage
            discounts: [r_discount, a_discount], // a list of discount objects

            // this is what we want to know
            // does not change
            discount: Big(0), // absolute amount od all discounts combined
            net: null, // base minus discounts, without tax
            tax: null, // absolute amount of tax
            total: null // total.
        }
    ];
*/

function get_tax(price, tax){
    return price.times(tax.div(Big(100)));
}

function calculate_item(item, decimal_places){
    var i;
    var item_discount, new_discount, new_total, new_net;

    // single item numbers:
    item.net = item.base;

    // what is going to be calculated
    item.discount = Big(0);
    item.tax = Big(0);
    item.total = Big(0);

    // subtract all discounts from this item's current base
    for(i = 0; i < item.discounts.length; i++){
        item_discount = item.discounts[i];

        if(item_discount.type == 'Relative'){
            // relative discount: get amount according to item's current base
            new_discount = item.net.times(item_discount.amount.div(100));

            // the new discount and net
            item.discount = item.discount.plus(new_discount);
            item.net = item.net.minus(new_discount);
        }
        else if(item_discount.type == 'Absolute'){
            // absolute discount:
            // do it so that the new price INCLUDING tax will be lower
            // by the amount of this discount

            // get current total and subtract discount from it
            new_total = item.net.plus(get_tax(item.net, item.tax_rate))
                .minus(item_discount.amount);

            // get the new price without tax
            new_net = new_total.div(item.tax_rate.div(100).plus(1));
            item.discount = item.discount.plus(item.net.minus(new_net));
            item.net = new_net;
        }
        else{
            // it's the 'bill' discount, remove it for now
            remove_from_array(item.discounts, i);
        }
    }

    // discounts are subtracted, get the item's shit together;
    // multiply everything by quantity and round to desired decimal places;
    // in real life, one would first multiply by quantity and then calculate with 4 decimal
    // places instead of 2 (depending on config), but we have Big() that uses 'infinite'
    // amount of decimal places for exact calculation
    item.batch = item.base.times(item.quantity).round(decimal_places);
    item.discount = item.discount.times(item.quantity).round(decimal_places);
    item.tax = get_tax(item.net, item.tax_rate).times(item.quantity).round(decimal_places);
    item.net = item.net.times(item.quantity).round(decimal_places);

    item.total = item.batch.minus(item.discount).plus(item.tax).round(decimal_places);

    return item;
}

function calculate_bill(items, bill_discount_amount, bill_discount_type, decimal_places){
    // 1. calculate all items's prices
    var i, item;

    // whole bill
    var base, discount, tax, total;

    for(i = 0; i < items.length; i++){
        items[i] = calculate_item(items[i], decimal_places);
    }

    // 2. calculate bill's total
    function get_total(){
        base = Big(0);
        discount = Big(0);
        tax = Big(0);
        total = Big(0);

        for(i = 0; i < items.length; i++){
            item = items[i];

            base = base.plus(item.batch);
            discount = discount.plus(item.discount);
            tax = tax.plus(item.tax);
            total = total.plus(item.total);
        }
    }

    get_total();

    // 3. bill discount:
    if(bill_discount_amount.cmp(Big(0)) != 0){
        if(bill_discount_type == 'Absolute'){
            // convert absolute discount to relative using current total
            bill_discount_amount = bill_discount_amount.div(total);
        }
        else{
            bill_discount_amount = bill_discount_amount.div(100);
        }

        var new_discount;

        // subtract this (now relative) discount from each item
        for(i = 0; i < items.length; i++){
            item = items[i];

            // discount amount:
            new_discount = item.net.times(bill_discount_amount);

            // create a new discount and add it to item's list discount
            item.discounts.push({
                id: -1,
                type: 'Bill',
                amount: new_discount
            });

            item.discount = item.discount.plus(new_discount).round(decimal_places);
            item.net = item.net.minus(new_discount).round(decimal_places);
            item.tax = item.net.times(item.tax_rate.div(100)).round(decimal_places);
            item.total = item.net.plus(item.tax).round(decimal_places);
        }
    }

    // 4. the new total is here.
    get_total();

    return {
        base: base,
        discount: discount,
        tax: tax,
        total: total,

        items: items
    };
}

