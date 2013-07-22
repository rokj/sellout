
def fill_countries():
    from config.countries import country_list
    from config.models import Country
    
    for c in country_list:
        country = Country(two_letter_code = c[1],
                          three_letter_code = c[2],
                          name = c[0])
        country.save()