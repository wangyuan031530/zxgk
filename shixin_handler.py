import requests
import re
import os
import random
from lxml import etree
from aip import AipOcr
import time
from config import APP_ID, API_KEY, SECRET_KEY, HEADERS

client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

session = requests.session()


class ZxInfo:
    @staticmethod
    def get_captche_id():
        url = "http://zxgk.court.gov.cn/zhzxgk/index_form.do"
        response = requests.request("GET", url, headers=HEADERS)
        result = re.search(r'var captchaId = \'(.*)\';', response.text)
        print(result)
        if result:
            print(result.group(1))
            captchaid = result.group(1)
            return captchaid

    @staticmethod
    def recognize_image(captchaid):
        url = "http://zxgk.court.gov.cn/zhzxgk/captcha.do"
        querystring = {"captchaId": captchaid, "random": random.uniform(0, 1)}
        if os.path.exists("captcha.jpg"):
            os.remove("captcha.jpg")
        try:
            response = session.request("GET", url, headers=HEADERS, timeout=6, params=querystring)

            if response.text:
                with open('captcha.jpg', 'wb') as f:
                    f.write(response.content)
            else:
                print("retry, response.text is empty")
        except Exception as ee:
            print(ee)

            # 识别

        def get_file_content(filepath):
            with open(filepath, 'rb') as fp:
                return fp.read()

        image = get_file_content('captcha.jpg')
        # 识别结果
        api_result = client.basicGeneral(image)
        print(api_result)
        try:
            if api_result['words_result'][0]:
                code = api_result['words_result'][0]['words']
                print(code)
                os.remove('captcha.jpg')
                return {'j_captcha': code, 'captchaId': captchaid}
        except Exception as e:
            print(e)

            return {'j_captcha': '1111', 'captchaId': captchaid}

    def zhixing_person_list(self, pname, cardnum, captchaid, current_page=1):
        result = self.recognize_image(captchaid)
        url = "http://zxgk.court.gov.cn/zhzxgk/newsearch"
        payload = {
            'currentPage': current_page,
            'searchCourtName': '全国法院（包含地方各级法院）',
            'selectCourtId': '0',
            'selectCourtArrange': '1',
            'pname': pname,
            'cardNum': cardnum,
            'j_captcha': result.get('j_captcha'),
            'countNameSelect': '',
            'captchaId': result.get('captchaId')
        }

        response = session.request("POST", url, data=payload, headers=HEADERS)
        while "验证码错误" in response.text:
            time.sleep(1)
            result = self.recognize_image(captchaid)
            try:
                payload['j_captcha'] = result.get('j_captcha')
            except Exception as e:
                print(e)
            response = session.request("POST", url, data=payload, headers=HEADERS)
        else:
            temps = re.search('1/\\d{1,4}', response.text).group()
            max_page = int(temps.replace('1/', ''))
            print("共{}页数据".format(max_page))
            all_info = []

            for page in range(1, max_page + 1):
                print("*" * 100)
                print("正在爬取关键词{}第{}页数".format(cardnum, page))
                print("*" * 100)
                payload['currentPage'] = page
                response = session.request("POST", url, data=payload, headers=HEADERS)
                while "验证码错误" in response.text:
                    result = self.recognize_image(captchaid)
                    payload['j_captcha'] = result.get('j_captcha')
                    response = session.request("POST", url, data=payload, headers=HEADERS)
                else:
                    html = etree.HTML(response.text)
                    trs = html.xpath('//table/tbody/tr')

                    for tr in trs[1:]:
                        tds = tr.xpath('.//td/text()')
                        print(tds)
                        name = tds[1]
                        case_no = tds[3]
                        print(name, result.get('j_captcha'), case_no, captchaid)
                        info = self.zhixing_person_detail(name, cardnum, result.get('j_captcha'), case_no, captchaid)
                        all_info.append(info)
                        time.sleep(1)

            return all_info

    def zhixing_person_detail(self, pname, cardnum, j_captcha_newdel,
                           casecode_newdel, captchaid_newdel):
        url = "http://zxgk.court.gov.cn/zhzxgk/newdetail?pnameNewDel={}&" \
              "cardNumNewDel={}&j_captchaNewDel={}&caseCodeNewDel={}&captchaIdNewDel=" \
              "{}".format(pname, cardnum, j_captcha_newdel, casecode_newdel, captchaid_newdel)
        print(url)
        response = requests.request("GET", url, headers=HEADERS)
        html = etree.HTML(response.text.encode('utf-8', 'ignore'))
        while "验证码错误" in response.text:
            print("验证码错误，正在重试")
            result = self.recognize_image(captchaid_newdel)
            self.zhixing_person_detail(pname, cardnum, result.get('j_captcha'), casecode_newdel, captchaid_newdel)
        else:
            info = []
            bzxr_trs = html.xpath('//table[@id="bzxr"]/tr')

            if bzxr_trs:
                print("被执行人")
                try:
                    name = html.xpath('//td[@id="pnameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    name = ''

                try:
                    card_id = html.xpath('//td[@id="partyCardNumDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    card_id = ''

                # try:
                #     sexy = html.xpath('//table[@id="bzxr"]/tr[3]/td/text()')[0]
                # except Exception as e:
                #     print(e)
                #     sexy = ''
                try:
                    sexy = html.xpath('//td[@id="Detail"]/text()')[0]
                except Exception as e:
                    print(e)
                    sexy = ''

                try:
                    court = html.xpath('//td[@id="execCourtNameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    court = ''

                try:
                    case_time = html.xpath('//td[@id="caseCreateTimeDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_time = ''

                try:
                    case_code = html.xpath('//td[@id="caseCodeDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_code = ''

                try:
                    target = html.xpath('//td[@id="execMoneyDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    target = ''

                bzxr_info = {"bzxr": {
                    "name": name,
                    "card_id": card_id,
                    "sexy": sexy,
                    "court": court,
                    "case_time": case_time,
                    "case_code": case_code,
                    "target": target
                }}
                info.append(bzxr_info)
            else:
                pass

            zb_trs = html.xpath('//table[@id="zb"]/tr')

            if zb_trs:
                print("终本案件")

                try:
                    case_code = html.xpath('//td[@id="ahDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_code = ''

                try:
                    name = html.xpath('//td[@id="xmDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    name = ''

                try:
                    sexy = html.xpath('//table[@id="zb"]/tr[3]/td/text()')[0]
                except Exception as e:
                    print(e)
                    sexy = ''

                try:
                    card_id = html.xpath('//td[@id="sfzhmDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    card_id = ''

                try:
                    court = html.xpath('//td[@id="zxfymcDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    court = ''

                try:
                    case_time = html.xpath('//td[@id="larqDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_time = ''

                try:
                    final_date = html.xpath('//td[@id="jarqDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    final_date = ''

                try:
                    target = html.xpath('//td[@id="sqzxbdjeDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    target = ''

                try:
                    money = html.xpath('//table[@id="zb"]/tr[9]/td/text()')[0]
                except Exception as e:
                    print(e)
                    money = ''

                zb_info = {"zb": {"case_code": case_code, "name": name, "sexy": sexy, "card_id": card_id,
                           "court": court, "case_time": case_time, "final_date": final_date, "target": target,
                                  "amount": money}}
                info.append(zb_info)
            else:
                pass

            xgl_trs = html.xpath('//table[@id="xgl"]/tr')

            if xgl_trs:
                print("限制消费人员")

                try:
                    name = html.xpath('//td[@id="inameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    name = ''

                try:
                    sexy = html.xpath('//td[@id="sexDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    sexy = ''

                try:
                    card_id = html.xpath('//td[@id="cardNumDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    card_id = ''

                try:
                    court = html.xpath('//td[@id="courtNameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    court = ''

                try:
                    area = html.xpath('//td[@id="areaNameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    area = ''

                try:
                    case_code = html.xpath('//td[@id="caseCodeDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_code = ''

                try:
                    case_time = html.xpath('//td[@id="regDateDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_time = ''

                xgl_info = {"xgl": {
                    "name": name,
                    "sexy": sexy,
                    "card_id": card_id,
                    "court": court,
                    "area": area,
                    "case_code": case_code,
                    "case_time": case_time
                }}
                info.append(xgl_info)
            else:
                pass

            sx_trs = html.xpath('//table[@id="sx"]/tr')

            if sx_trs:
                print("失信被执行人")

                try:
                    name = html.xpath('//td[@id="inameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    name = ''

                try:
                    sexy = html.xpath('//td[@id="sexDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    sexy = ''

                try:
                    card_id = html.xpath('//td[@id="cardNumDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    card_id = ''

                try:
                    court = html.xpath('//td[@id="courtNameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    court = ''

                try:
                    area = html.xpath('//td[@id="areaNameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    area = ''

                try:
                    gist_id = html.xpath('//td[@id="gistIdDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    gist_id = ''

                try:
                    case_time = html.xpath('//td[@id="regDateDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_time = ''

                try:
                    case_code = html.xpath('//td[@id="caseCodeDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_code = ''

                try:
                    gist_unit = html.xpath('//td[@id="gistUnitDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    gist_unit = ''

                try:
                    duty = html.xpath('//td[@id="dutyDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    duty = ''

                try:
                    performance = html.xpath('//td[@id="performanceDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    performance = ''

                try:
                    disrupt_typename = html.xpath('//td[@id="disruptTypeNameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    disrupt_typename = ''

                try:
                    publish_date = html.xpath('//td[@id="publishDateDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    publish_date = ''

                sx_info = {"sx": {
                    "name": name,
                    "sexy": sexy,
                    "card_id": card_id,
                    "court": court,
                    "area": area,
                    "gist_id": gist_id,
                    "case_time": case_time,
                    "case_code": case_code,
                    "gist_unit": gist_unit,
                    "duty": duty,
                    "performance": performance,
                    "disruptTypeName": disrupt_typename,
                    "publish_date": publish_date
                }}

                info.append(sx_info)

            else:
                pass

            return {casecode_newdel: info}

    def zhixing_company_list(self, cardnum, pname, captchaid, current_page=1):
        result = self.recognize_image(captchaid)
        url = "http://zxgk.court.gov.cn/zhzxgk/newsearch"
        payload = {
            'currentPage': current_page,
            'searchCourtName': '全国法院（包含地方各级法院）',
            'selectCourtId': '0',
            'selectCourtArrange': '1',
            'pname': pname,
            'cardNum': cardnum,
            'j_captcha': result.get('j_captcha'),
            'countNameSelect': '',
            'captchaId': result.get('captchaId')
        }

        response = session.request("POST", url, data=payload, headers=HEADERS)
        while "验证码错误" in response.text:
            time.sleep(1)
            result = self.recognize_image(captchaid)
            try:
                payload['j_captcha'] = result.get('j_captcha')
            except Exception as e:
                print(e)
            response = session.request("POST", url, data=payload, headers=HEADERS)
        else:
            temps = re.search('1/\\d{1,4}', response.text).group()
            max_page = int(temps.replace('1/', ''))
            print("共{}页数据".format(max_page))
            all_info = []

            for page in range(1, max_page + 1):
                print("*" * 100)
                print("正在爬取关键词{}第{}页数".format(cardnum, page))
                print("*" * 100)
                payload['currentPage'] = page
                response = session.request("POST", url, data=payload, headers=HEADERS)
                while "验证码错误" in response.text:
                    result = self.recognize_image(captchaid)
                    payload['j_captcha'] = result.get('j_captcha')
                    response = session.request("POST", url, data=payload, headers=HEADERS)
                else:
                    html = etree.HTML(response.text)
                    trs = html.xpath('//table/tbody/tr')

                    for tr in trs[1:]:
                        tds = tr.xpath('.//td/text()')
                        print(tds)
                        name = tds[1]
                        case_no = tds[3]
                        print(name, result.get('j_captcha'), case_no, captchaid)
                        info = self.zhixing_company_detail(name, cardnum, result.get('j_captcha'), case_no, captchaid)
                        all_info.append(info)
                        time.sleep(0.5)

            return all_info

    def zhixing_company_detail(self, pname, cardnum, j_captcha_newdel,
                               casecode_newdel, captchaid_newdel):
        url = "http://zxgk.court.gov.cn/zhzxgk/detailZhcx.do?pnameNewDel={}&" \
              "cardNumNewDel={}&j_captchaNewDel={}&caseCodeNewDel={}&captchaIdNewDel=" \
              "{}".format(pname, cardnum, j_captcha_newdel, casecode_newdel, captchaid_newdel)
        print(url)
        response = requests.request("GET", url, headers=HEADERS)
        html = etree.HTML(response.text)
        while "验证码错误" in response.text:
            print("验证码错误，正在重试")
            result = self.recognize_image(captchaid_newdel)
            self.zhixing_company_detail(pname, cardnum, result.get('j_captcha'), casecode_newdel, captchaid_newdel)
        else:
            info = []
            bzxr_trs = html.xpath('//div[text()="被执行人"]')

            if bzxr_trs:
                print("被执行人")
                try:
                    name = html.xpath('//td[@id="pnameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    name = ''

                try:
                    card_id = html.xpath('//td[@id="partyCardNumDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    card_id = ''

                try:
                    sexy = html.xpath('//td[@id="Detail"]/text()')[0]
                except Exception as e:
                    print(e)
                    sexy = ''

                try:
                    court = html.xpath('//td[@id="execCourtNameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    court = ''

                try:
                    case_time = html.xpath('//td[@id="caseCreateTimeDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_time = ''

                try:
                    case_code = html.xpath('//td[@id="caseCodeDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_code = ''

                try:
                    target = html.xpath('//td[@id="execMoneyDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    target = ''

                bzxr_info = {"bzxr": {
                    "name": name,
                    "card_id": card_id,
                    "sexy": sexy,
                    "court": court,
                    "case_time": case_time,
                    "case_code": case_code,
                    "target": target
                }}
                info.append(bzxr_info)
            else:
                pass

            zb_trs = html.xpath('//div[text()="终本案件"]')

            if zb_trs:
                print("终本案件")

                try:
                    case_code = html.xpath('//td[@id="ahDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_code = ''

                try:
                    name = html.xpath('//td[@id="xmDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    name = ''

                try:
                    card_id = html.xpath('//td[@id="sfzhmDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    card_id = ''

                try:
                    court = html.xpath('//td[@id="zxfymcDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    court = ''

                try:
                    case_time = html.xpath('//td[@id="larqDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_time = ''

                try:
                    final_date = html.xpath('//td[@id="jarqDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    final_date = ''

                try:
                    target = html.xpath('//td[@id="sqzxbdjeDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    target = ''

                try:
                    money = html.xpath('//td[@id="swzxbdjeDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    money = ''

                zb_info = {"zb": {"case_code": case_code, "name": name, "card_id": card_id,
                                  "court": court, "case_time": case_time, "final_date": final_date, "target": target,
                                  "amount": money}}
                info.append(zb_info)
            else:
                pass

            xgl_trs = html.xpath('//div[text()="限制消费人员"]')

            if xgl_trs:
                print("限制消费人员")

                try:
                    name = html.xpath('//td[@id="inameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    name = ''

                try:
                    sexy = html.xpath('//td[@id="sexDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    sexy = ''

                try:
                    card_id = html.xpath('//td[@id="cardNumDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    card_id = ''

                try:
                    court = html.xpath('//td[@id="courtNameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    court = ''

                try:
                    area = html.xpath('//td[@id="areaNameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    area = ''

                try:
                    case_code = html.xpath('//td[@id="caseCodeDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_code = ''

                try:
                    case_time = html.xpath('//td[@id="regDateDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_time = ''

                xgl_info = {"xgl": {
                    "name": name,
                    "sexy": sexy,
                    "card_id": card_id,
                    "court": court,
                    "area": area,
                    "case_code": case_code,
                    "case_time": case_time
                }}
                info.append(xgl_info)
            else:
                pass

            sx_trs = html.xpath('//div[text()="失信被执行人"]')

            if sx_trs:
                print("失信被执行人")

                try:
                    name = html.xpath('//td[@id="inameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    name = ''

                try:
                    card_id = html.xpath('//td[@id="cardNumDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    card_id = ''

                try:
                    businessEntityName = html.xpath('//td[@id="businessEntityDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    businessEntityName = ''

                try:
                    court = html.xpath('//td[@id="courtNameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    court = ''

                try:
                    area = html.xpath('//td[@id="areaNameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    area = ''

                try:
                    gist_id = html.xpath('//td[@id="gistIdDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    gist_id = ''

                try:
                    case_time = html.xpath('//td[@id="regDateDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_time = ''

                try:
                    case_code = html.xpath('//td[@id="caseCodeDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    case_code = ''

                try:
                    gist_unit = html.xpath('//td[@id="gistUnitDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    gist_unit = ''

                try:
                    duty = html.xpath('//td[@id="dutyDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    duty = ''

                try:
                    performance = html.xpath('//td[@id="performanceDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    performance = ''

                try:
                    disrupt_typename = html.xpath('//td[@id="disruptTypeNameDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    disrupt_typename = ''

                try:
                    publish_date = html.xpath('//td[@id="publishDateDetail"]/text()')[0]
                except Exception as e:
                    print(e)
                    publish_date = ''

                try:
                    businessEntity = html.xpath('//td[@id="publishDateDetail"]/../following-sibling::tr/td[2]/text()')[
                        0]
                except Exception as e:
                    print(e)
                    businessEntity = ''

                sx_info = {"sx": {
                    "name": name,
                    "businessEntityName": businessEntityName,
                    "card_id": card_id,
                    "court": court,
                    "area": area,
                    "gist_id": gist_id,
                    "case_time": case_time,
                    "case_code": case_code,
                    "gist_unit": gist_unit,
                    "duty": duty,
                    "performance": performance,
                    "disruptTypeName": disrupt_typename,
                    "publish_date": publish_date,
                    "businessEntity": businessEntity
                }}

                info.append(sx_info)

            else:
                pass

            return {casecode_newdel: info}

