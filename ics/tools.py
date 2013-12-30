import re


def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)


def validate(string):
    import requests
    payload = {'snip': string}
    ret = requests.post('http://severinghaus.org/projects/icv/', data=payload)
    if 'Sorry, your calendar could not be parsed.' in ret.text:
        i = ret.text.index('<div class="parse-error">')
        j = ret.text[i:].index('</div>')
        usefull = ret.text[i:i + j]
        usefull_clean = striphtml(usefull)
        lines = usefull_clean.split('\n')
        lines_clean = map(lambda x: x.strip(), lines)
        lines_no_empty = filter(lambda x: x != '', lines_clean)
        return '\n'.join(lines_no_empty)

    elif 'Congratulations; your calendar validated!' in ret.text:
        return True
    else:
        return None
