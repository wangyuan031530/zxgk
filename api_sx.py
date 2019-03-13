from flask import Flask, request, jsonify
from shixin_person import ZxPersonInfo
from shixin_company import ZxCompanyInfo
import os

app = Flask(__name__)


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
    zxinfo = ZxPersonInfo()
    captcheid = zxinfo.get_captche_id()

    info = zxinfo.get_zhixing_list(pname, cardnum, captcheid)
    result = {'status': '0','results': info}

    return jsonify(result)


@app.route('/zxgk/company')
def company_id():
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

    zxinfo = ZxCompanyInfo()
    captcheid = zxinfo.get_captche_id()

    info = zxinfo.get_zhixing_list(cardnum, pname, captcheid)

    result = {'status': '0', 'results': info}

    return jsonify(result)



if __name__ == '__main__':
    app.run()

