// Big() setup
Big.RM = 1; // ROUND_HALF_UP, away from zero (must match settings in python)

var r_discount = {
    amount: Big(20),
    type: 'percent'
};

var a_discount = {
    amount: Big(1),
    type: 'absolute'
};

var items = [
    {
        // these never change, they are defined in database
        quantity: Big(2),
        base: Big(10), // this is without discounts and without tax
        tax_rate: Big(20), // price in percentage
        discounts: [r_discount, a_discount], // a list of discount objects

        // this is what we want to know
        /*base */ // does not change
        discount: Big(0), // absolute amount od all discounts combined
        net: null, // base minus discounts, without tax
        tax: null, // absolute amount of tax
        total: null // total.
    },
    {
        quantity: Big(1),
        base: Big(100),
        tax_rate: Big(9.5),
        discounts: [a_discount],

        discount: Big(0),
        net: null,
        tax: null,
        total: null
    },
    {
        quantity: Big(5),
        base: Big(25),
        tax_rate: Big(0),
        discounts: [r_discount],

        discount: Big(0),
        net: null,
        tax: null,
        total: null
    },
    {
        quantity: Big(2),
        base: Big(10),
        tax_rate: Big(0),
        discounts: [],

        discount: Big(0),
        net: null,
        tax: null,
        total: null
    }
];

function get_tax(price, tax){
    return price.times(tax.div(Big(100)));
}

function calculate(items, bill_discount_amount, bill_discount_type){
    // 1. calculate all items's prices
    var i, j;

    // current item and temp stuff
    var item, item_discount;
    var new_item_base, new_item_discount, new_item_total;

    // whole bill
    var base, discount, tax, total;

    for(i = 0; i < items.length; i++){
        item = items[i];

        item.net = item.base.times(item.quantity);

        // subtract all discounts from this item's current base
        for(j = 0; j < item.discounts.length; j++){
            item_discount = item.discounts[j];

            if(item_discount.type == 'percent'){
                // relative discount: get amount according to item's current base
                new_item_discount = item.net.times(item_discount.amount.div(100));

                // subtract from item's current base
                item.net = item.net.minus(new_item_discount);

                // the new discount
                item.discount = item.discount.plus(new_item_discount);
            }
            else{
                // absolute discount:
                // do it so that the new price INCLUDING tax will be lower
                // by the amount of this discount

                // get current total price and subtract discount from it
                new_item_total = item.net.plus(get_tax(item.net, item.tax_rate))
                    .minus(item_discount.amount.times(item.quantity));

                // get the new base
                new_item_base = new_item_total.div(item.tax_rate.div(100).plus(1));

                // get the new discount according to the new base
                item.discount = item.discount.plus(new_item_total.minus(new_item_base));
            }
        }

        // discounts are subtracted, get the item's shit together
        // item.discount // already there
        item.net = item.base.minus(item.discount);
        item.tax = get_tax(item.net, item.tax_rate);
    }

    // 2. calculate bill's total
    function get_total(){
        base = Big(0);
        discount = Big(0);
        tax = Big(0);
        total = Big(0);

        for(i = 0; i < items.length; i++){
            item = items[i];
            item.total = item.net.plus(item.tax);

            base = base.plus(item.net);
            discount = discount.plus(item.discount);
            tax = tax.plus(item.tax);
            total = total.plus(item.total);
        }
    }

    get_total();

    // 3. bill discount:
    if(bill_discount_amount.cmp(Big(0)) != 0){
        if(bill_discount_type == 'absolute'){
            // convert absolute discount to relative using current total
            bill_discount_amount = bill_discount_amount.div(total);
        }
        else{
            bill_discount_amount = bill_discount_amount.div(100);
        }

        // subtract this (now relative) discount from each item
        for(i = 0; i < items.length; i++){
            item = items[i];

            new_item_discount = item.net.div(bill_discount_amount);

            item.discount = item.discount.plus(new_item_discount);
            item.net = item.net.minus(bill_discount_amount);
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

p = calculate(items, Big(0), 'relative');
console.log(p);
console.log(p.total.toString());

////////////////////////////////////////////////////////////
////////////////////                    ////////////////////
//////////////////// useless junk below ////////////////////
////////////////////                    ////////////////////
////////////////////////////////////////////////////////////

// utilities for calculation of prices etc.
function do_tax(p_incl, p_excl, tax){

}

function total_price(base_price, tax, discounts, quantity, decimal_places){

}