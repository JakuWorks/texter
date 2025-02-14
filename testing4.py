signs: list[str] = [] unicode_highest_code_point: int = UNICODE_HIGHEST_CODE_PONT
excluded_unicode_categories: set[str] = BLACKLISTED_UNICODE_CATEGORIES

for code_point in range(unicode_highest_code_point+1):
    sign: str = chr(code_point)
    category = unicodedata.category(sign)
    if category in excluded_unicode_categories:
        continue
    signs.append(sign)

signs_tuple: tuple[str, ...] = tuple(signs)
signs_length: int = len(signs)

print(f'Selected {signs_length} unicode code points!')
if signs_length <= 0:
    raise RuntimeError(f'ERROR : {get_allowed_unicode_signs.__name__} Found 0 valid code points for the current highest code point setting ({UNICODE_HIGHEST_CODE_PONT})')

return signs_tuple

