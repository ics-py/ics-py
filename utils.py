#!/usr/bin/env python
# -*- coding: utf-8 -*-

from parsley import makeGrammar

def unfold(text):
    lines = text.split('\n')
    new_lines = []
    while len(lines) > 0:
        line = lines.pop(0)
        if not len(line) > 0:
            continue

        if line[0] == " ":
            last_line = new_lines.pop()
            line = last_line + line[1:]

        new_lines.append(line)

    return "\n".join(new_lines)


grammar = """
contentline   = name (";" param )* ":" value crlf
name          = (iana_token | x_name)
iana_token    = (alpha | digit | "-")+
alpha         = letter
x_name        = "X-" (vendorid "-"){0,1} (alpha | digit | "-")+
vendorid      = (alpha | digit){3,100000000}

param         = param_name "=" param_value ("," param_value)*
param_name    = (iana_token | x_name)
param_value   = (paramtext | quoted_string)

quoted_string = dquote qsafe_char* dquote

paramtext     = safe_char*
value         = value_char*

dquote        = '"'
wsp           = (" " | "\t")+

qsafe_char    = (wsp | "!" | ascii23_7e | non_ascii)
safe_char     = (wsp | "!" | ascii23_2b | ascii2d_39 | ascii3c_7e)
value_char    = (wsp | ascii21_7e | non_ascii)

non_ascii     = 'ç'

crlf          = '\r\n'

ascii21_7e    = ('!' | '"' | sharp_to_slash | digit | alpha | colon_to_tilde)
ascii2d_39    = ('-' | '.' | '/' | digit)
ascii23_2b    = sharp_to_plus
ascii3c_7e    = ('<' | '=' | '>' | '?' | '@' | alpha | crochet_to_tilde)
ascii23_7e    = (sharp_to_slash | digit | alpha | colon_to_tilde)
ascii00_08    = ('\x00' | '\x01' | '\x02' | '\x03' | '\x04' | '\x05' | '\x06' | '\x07' | '\x08')
ascii0a_1f    = ('\x0a' | '\x0b' | '\x0c' | '\x0d' | '\x0e' | '\x0f' | '\x10' | '\x11' | '\x12' | '\x13' | '\x14' | '\x15' | '\x16' | '\x17' | '\x18' | '\x19' | '\x1a' | '\x1b' | '\x1c' | '\x1d' | '\x1e' | '\x1f')

crochet_to_tilde  = ('[' | '\\\\' | ']' | '^' | '_' | '`' | '{' | '|' | '}' | '~')
colon_to_tilde    = (':' | ';' | '<' | '=' | '>' | '?' | '@' | crochet_to_tilde)
sharp_to_plus     = ('#' | '$' | '%' | '&' | "'" | '(' | ')' | '*' | '+')
sharp_to_slash    = (sharp_to_plus | ',' | '-' | '.' | '/')
"""
# TODO : fix non ascii

Example = makeGrammar(grammar, {})

def parser(text):
    g = Example(unfold(text))
    result = g.contentline()
    return result