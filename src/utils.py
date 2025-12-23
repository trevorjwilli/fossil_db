
def format_string_from_list(x: iter):
    "Convert iterable to a string ready for query"
    return ','.join([f"'{j}'" for j in x])
                    











