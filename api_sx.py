from flask import Flask, request, jsonify
from shixin_handler import ZxInfo
import os

app = Flask(__name__)
zxinfo = ZxInfo()
captcheid = zxinfo.get_captche_id()


@app.route('/zxgk/person')
def person():
    if (os.path.exists("captcha.jpg")):
        os.remove("captcha.jpg")
    cardnum = request.args.get('cardnum')
    pname = request.args.get('pname')
    if not pname:
        pname = ''

    if cardnum and pname:
        pname = ''



    info = zxinfo.zhixing_person_list(pname, cardnum, captcheid)
    result = {'status': '0','results': info}

    return jsonify(result)


@app.route('/zxgk/company')
def company():
    if (os.path.exists("captcha.jpg")):
        os.remove("captcha.jpg")
    cardnum = request.args.get('cardnum')
    pname = request.args.get('pname')
    if not cardnum:
        cardnum = ''

    if not pname:
        pname = ''

    if cardnum and pname:
        pname = ''

    info = zxinfo.zhixing_company_list(cardnum, pname, captcheid)

    result = {'status': '0', 'results': info}

    return jsonify(result)


if __name__ == '__main__':
    app.run()

