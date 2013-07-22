def model_to_dict(obj, include=[], level=0):
    """ converts django model to dictionary.
        includes data from foreign key objects, if it's in include[] list. """
    if not obj:
        return None
    
    data = {}
    level += 1
    
    # put all fields' values in a dictionary
    for field in obj._meta.fields:
        if field.rel and str(field.name) in include: # if this is a foreign key, write down the whole object
            sub_obj = getattr(obj, str(field.name))
            data[str(field.name)] = model_to_dict(sub_obj, include=include, level=level)
        else:
            data[str(field.name)] = getattr(obj, str(field.name))
    
    return data
