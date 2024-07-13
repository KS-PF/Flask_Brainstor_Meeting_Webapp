import secrets
import re
from flask import (
    session, make_response
)
from werkzeug.exceptions import abort




def token_check(type,post_token = None):

    if type == "set":
        token = secrets.token_hex(16)
        session['sc_token'] = token
        return token
    
    if type == "check":
        result = False

        session_token = session.get('sc_token')
        if post_token == session_token:
            result = True
        
        return result




def replace_str(content):
    content = str(content)
    l = [
        'javascript:',"\b",'<','>','/','?','|','<iframe>',
        '\\','#','$','%','&',':',';','*','\b','--','"',"'",
        '¥','^','~','=','(',')','`','+','[',']','{','}','!'
    ]
    for i in l:
        i = str(i)
        num = len(i)
        aw = '×'*num
        content = content.replace(i, aw)
    
    return content




def secure_response_headers(response):
    response = make_response(response)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response




def is_length_within(s, min_length, max_length):
    resalt = False
    min_length = int(min_length)
    max_length = int(max_length)

    str_length = len(s)
    if max_length >= str_length and str_length >= min_length:
        resalt = True 

    return resalt




def regular_expression(content):
    if re.fullmatch(r'\A(?=.*?[a-z])(?=.*?[A-Z])(?=.*?\d)[a-zA-Z\d]{3,140}\Z', content):
        return True
    else:
        return False




def form_validation(
        content,
        error,
        label,
        rex = True,
        hidden = False,
        len_check = True,
        len_min = 0,
        len_max = 0,
):
    hidden_error = "ERROR:もう一度入力してください"

    if error is not None:
        return error
    
    elif not content:
        if hidden:
            return hidden_error + ' (1c)'
        else:
            return f"ERROR:{label}が未入力です"
    
    elif len_check == True and is_length_within(content, len_min, len_max) == False:
        content_num = len(content)
        return f"ERROR:「{label}」は{len_min}~{len_max}文字の間で入力してください。現在{content_num}文字"
    
    elif (rex == True) and (regular_expression(content) == False):
        if hidden:
            return hidden_error + ' (3r)'
        else:
            return f"ERROR:「{label}」は半角英単語の小文字、大文字、数字で構成され、それぞれ含んでください"
    else:
        return None




def int_check(num):
    try:
        num = int(num) 
        return num
    except ValueError:
        abort(404)