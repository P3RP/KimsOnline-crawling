# -*- encoding:utf-8 -*-

import os
import time
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium import webdriver
from openpyxl import Workbook
from openpyxl import load_workbook
from bs4 import BeautifulSoup
import requests
import json
import re
import logging.handlers


def my_debug():
    input("정지")
    driver.quit()
    exit()

# ========================
# USER
# GET USER INFO
def get_user_info(file_name):
    try:
        with open('./' + file_name) as file:
            logger.info("[COMPLETE] User File 확인")
            info = file.readlines()
        user_info_list = info[0:2]
        return [info.strip() for info in user_info_list]
    except FileNotFoundError:
        logger.error("[ERROR] User File 확인 실패")
        exit()


# ========================
# EXCEL
# MAKE EXCEL
def make_excel(data_list, name):
    """
        :호출예시 make_excel([ [1,2,3,4], [5,6,7,8] ]) or make_excel(2dArray)
        :param data_list:  [ data1, data2, data3, data4 ] 꼴의 1차원 list를 가지는 2차원 list
        :return: 없
    """
    # === CONFIG
    FILENAME = name + ".xlsx"

    # === SAVE EXCEL
    wb = Workbook()
    ws1 = wb.worksheets[0]
    header1 = ['댓글 아이디(완전한 이메일 형태)', '내용', '크롤링 URL', '작성시각', '현재시각']
    ws1.column_dimensions['A'].width = 30
    ws1.column_dimensions['B'].width = 70
    ws1.column_dimensions['C'].width = 50
    ws1.column_dimensions['D'].width = 20
    ws1.column_dimensions['E'].width = 20
    ws1.append(header1)

    # DATA SAVE
    for comment_data in data_list:
        ws1.append(comment_data)
    # END
    wb.save(FILENAME)
    #logger.info("[COMPLETE] [{}] Excel 생성 완료".format(name))


def temp_excel(list):
    wb = Workbook()
    ws1 = wb.worksheets[0]
    for data in list:
        ws1.append([data])

    wb.save("temp.xlsx")


# SET BLANK
def set_blank(list):
    while len(list) < 10:
        list.append('빈칸')
    return list


# SET INFO IN LIST
def set_info(data_list, drug_info, idx):
    for col in range(len(drug_info)):
        data_list[col][idx] = drug_info[col]


# ========================
# HEALTH KR
def get_drug_info_heal(code):
    url_n = 'http://localapi.health.kr:8090/totalProduceN.localapi?search_word={0}&search_flag=all&sunb_count=&callback=jQuery162012134783020118656_1534985622077&_=1534985622155'.format(code)
    resp_n = requests.get(url_n).text
    data_n = resp_n.replace('jQuery162012134783020118656_1534985622077([', '').replace('])', '').strip()

    url_y = 'http://localapi.health.kr:8090/totalProduceY.localapi?search_word={0}&search_flag=all&sunb_count=&callback=jQuery162012134783020118656_1534985622077&_=1534985622155'.format(code)
    resp_y = requests.get(url_y).text
    data_y = resp_y.replace('jQuery162012134783020118656_1534985622077([', '').replace('])', '').strip()

    if data_n != '':
        return detail_heal(json.loads(data_n)['drug_code'])
    elif data_y != '':
        return detail_heal(json.loads(data_y)['drug_code'])
    else:
        return list()


def detail_heal(drug_code):
    url = 'http://localapi.health.kr:8090/result_drug.localapi?drug_cd={0}&callback=jQuery16208637879955482337_1534990549348&_=1534990549525'.format(drug_code)
    resp = requests.get(url).text
    data = resp.replace('jQuery16208637879955482337_1534990549348([', '').replace('])', '').strip()

    return json.loads(data)['mediguide'].split('brbr')


# ========================
# DRUGINFO
def login_drug(user_info):
    global driver

    driver.get('https://www.druginfo.co.kr')
    driver.find_element_by_xpath('/html/body/table/tbody/tr/td[3]/table/tbody/tr[6]/td/table/tbody/tr/td[3]/table/tbody/tr/td/form/table/tbody/tr[2]/td[2]/table/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/label/input').send_keys(user_info[0])
    driver.find_element_by_xpath('/html/body/table/tbody/tr/td[3]/table/tbody/tr[6]/td/table/tbody/tr/td[3]/table/tbody/tr/td/form/table/tbody/tr[2]/td[2]/table/tbody/tr[1]/td[1]/table/tbody/tr[3]/td/input[1]').send_keys(user_info[1])
    driver.find_element_by_xpath('/html/body/table/tbody/tr/td[3]/table/tbody/tr[6]/td/table/tbody/tr/td[3]/table/tbody/tr/td/form/table/tbody/tr[2]/td[2]/table/tbody/tr[1]/td[2]/input').click()


def get_drug_info_drug(product_code):
    global driver

    result = list()
    # for product in product_codes:
    search_url = 'https://www.druginfo.co.kr/search2/search.aspx?q='
    url = search_url + product_code
    html = requests.get(url).text
    bs = BeautifulSoup(html, 'lxml')

    try:
        trs = bs.find('div', id='main').find('div', class_='table-res').find('table').find_all('tr')
        for tr in trs:
            a_tag = tr.find('a', class_='product-link')
            if a_tag is not None:
                # result.append(detail(a_tag['href']))
                return detail_drug(a_tag['href'])
    except Exception as exc:
        print('약품 없음.')
        # result.append('약품 없음.')
        return '약품 없음.'

    return result


def detail_drug(href):
    global driver

    url = 'https://www.druginfo.co.kr' + href
    driver.get(url)
    driver.implicitly_wait(3)
    bs = BeautifulSoup(driver.page_source, 'lxml')

    trs = bs.find('div', id='contents-group4').find('table').find_all('tr')
    for tr in trs:
        try:
            if '복약지도' == tr.find('td', class_='pdt-head-cell-left').get_text():
                return tr.find('td', class_='pdt-cell').get_text().strip().split('\n')
        except Exception as exc:
            continue


# ==========================
# KIMSONLINE
# LOGIN
def login_kims(user_info):
    # MOVE TO URL
    driver.get('https://www.kimsonline.co.kr/')
    time.sleep(0.3)

    # LOG IN IN KIMS ONLINE
    driver.find_element_by_xpath('//*[@id="user_id"]').send_keys(user_info[0])
    driver.find_element_by_xpath('//*[@id="user_pw"]').send_keys(user_info[1])
    driver.find_element_by_xpath('//*[@id="frmLogin"]/div[3]/div[2]/a').click()


# GET DRUG LIST
def get_drug_list_kims(file):
    try:
        drug_file = load_workbook(file)
        logger.info("[COMPLETE] Drug File 확인")
        drug_sheet = drug_file.worksheets[0]
        temp = 0
        temp_list = []
        for drug_row in drug_sheet.rows:
            if temp == 0:
                temp += 1
                continue
            temp_list.append(drug_row[2].value)
        return temp_list

    except FileNotFoundError:
        logger.error("[ERROR] Drug File 확인 실패")
        exit()


# GET DRUG INFO IN KIMSONLINE
def get_drug_info_kims(drug_code):
    drug_data = []

    driver.get('https://www.kimsonline.co.kr/')
    time.sleep(0.3)

    # MOVE FOR SEARCHING DRUG
    driver.find_element_by_xpath('//*[@id="gnb"]/li[1]/a').click()
    driver.implicitly_wait(3)
    time.sleep(0.2)

    # SEARCH DRUG
    driver.find_element_by_xpath('//*[@id="txtKDCode"]').send_keys(drug_code)
    driver.find_element_by_xpath('//*[@id="contents"]/div/div[6]/a[1]').click()
    driver.implicitly_wait(3)
    time.sleep(0.2)

    # SELECT DRUG
    driver.find_element_by_xpath('//*[@id="tabMarketS"]/ul/li/div[2]/div[1]/a').click()
    driver.implicitly_wait(3)
    time.sleep(0.2)

    # SELECT MENU
    driver.find_element_by_xpath('//*[@id="contents"]/div/div[5]/ul/li[4]').click()
    driver.implicitly_wait(3)
    time.sleep(0.2)

    # GET DRUG INFO
    bs4 = BeautifulSoup(driver.page_source, 'lxml')
    drug_info = bs4.find('div', id='ctl01_area_mediguide_brief').find_all('div', class_='mt10')
    print('==================== 1 ======================')
    print('효능')
    print(drug_info[0].get_text().strip().split('\n')[0])
    drug_data.append(drug_info[0].get_text().strip().split('\n')[0])
    print('==================== 2 ======================')
    print('복약 지도')
    for medi_guide in drug_info[1].get_text().strip().split('\n')[0:-1]:
        print(medi_guide)
        drug_data.append(medi_guide)
    return drug_data

'http://www.kimsonline.co.kr/drugcenter/search/detailsearchlist?Page=1&kdcode=643505661'
'http://www.kimsonline.co.kr/drugcenter/search/detailsearchlist?kdcode=641905940'


if __name__ == '__main__':
    # Logger
    logger = logging.getLogger('notice')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[SYSTEM] %(asctime)s :: %(message)s')
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    # Variables
    drug_list = ['641905940', '641905450', '643505661']

    # Get user info for Drug Info and Kims Online
    user_info_drug = get_user_info('user_drug.txt')
    user_info_kims = get_user_info('user_kims.txt')

    # Get drug list
    # drug_list = get_drug_list('drug.xlsx')

    # Initiate driver
    driver = webdriver.Chrome('./chromedriver.exe')
    driver.maximize_window()
    driver.implicitly_wait(3)

    # Log In in Drug Info and Kims Online
    login_kims(user_info_kims)
    login_drug(user_info_drug)

    for drug in drug_list:
        data_list = [[None] * 7 for i in range(10)]

        set_info(data_list, get_drug_info_heal(drug), 4)
        set_info(data_list, get_drug_info_drug(drug), 5)
        set_info(data_list, get_drug_info_kims(drug), 6)
        print(data_list)
        my_debug()

    # # Move to URL
    # driver.get('https://www.kimsonline.co.kr/')
    # time.sleep(0.3)

    # # Log in
    # driver.find_element_by_xpath('//*[@id="user_id"]').send_keys(user_info[0])
    # driver.find_element_by_xpath('//*[@id="user_pw"]').send_keys(user_info[1])
    #
    # driver.find_element_by_xpath('//*[@id="frmLogin"]/div[3]/div[2]/a').click()
    # driver.implicitly_wait(3)
    # time.sleep(0.3)
    #
    # for drug in drug_list:
    #     temp_data = []
    #
    #     # Move for searching drug
    #     driver.find_element_by_xpath('//*[@id="gnb"]/li[1]/a').click()
    #     driver.implicitly_wait(3)
    #     time.sleep(0.2)
    #
    #     # Search drug
    #     driver.find_element_by_xpath('//*[@id="txtKDCode"]').send_keys(drug)
    #     driver.find_element_by_xpath('//*[@id="contents"]/div/div[6]/a[1]').click()
    #     driver.implicitly_wait(3)
    #     time.sleep(0.2)
    #
    #     # Select drug
    #     driver.find_element_by_xpath('//*[@id="tabMarketS"]/ul/li/div[2]/div[1]/a').click()
    #     driver.implicitly_wait(3)
    #     time.sleep(0.2)
    #
    #     # Select Menu
    #     driver.find_element_by_xpath('//*[@id="contents"]/div/div[5]/ul/li[4]').click()
    #     driver.implicitly_wait(3)
    #     time.sleep(0.2)
    #
    #     # Get drug info
    #     bs4 = BeautifulSoup(driver.page_source, 'lxml')
    #     drug_info = bs4.find('div', id='ctl01_area_mediguide_brief').find_all('div', class_='mt10')
    #     print('==================== 1 ======================')
    #     print('효능')
    #     print(drug_info[0].get_text().strip().split('\n')[0])
    #     temp_data.append(drug_info[0].get_text().strip().split('\n')[0])
    #     print('==================== 2 ======================')
    #     print('복약 지도')
    #     for guide in drug_info[1].get_text().strip().split('\n')[0:-1]:
    #         print(guide)
    #         temp_data.append(guide)
    #     print(temp_data)
    #     data_list.append(temp_data)
    #
    #     input("asda")
    #     exit()

    # Quit driver
    driver.quit()

    print('\n전체 리스트')
    print(data_list)

    # data_fix_list = []
    # for data in data_list:
    #     for fix_data in set_blank(data):
    #         data_fix_list.append(fix_data)
    #
    # print(data_fix_list)
    #
    # temp_excel(data_fix_list)

    '''
    주성분 코드 예시 : 515203ATB
    약품 코드 예시 : 641905940
    
    제품명 : //*[@id="txtProductName"]
    제품 코드 : //*[@id="txtKDCode"]
    성분명 : //*[@id="txtGenName"]
    제약사 : //*[@id="txtComName"]
    주성분 코드 : //*[@id="txtMainGenCode"]
    
    검색 버튼 : //*[@id="contents"]/div/div[6]/a[1]
    
    제품 선택 : //*[@id="tabMarketS"]/ul/li/div[2]/div[1]/a
    
    복약 지도 버튼 : //*[@id="contents"]/div/div[5]/ul/li[4]
    '''
