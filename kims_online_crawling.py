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


# GET DRUG LIST
def get_drug_list(file):
    try:
        drug_file = load_workbook(file)
        logger.info("[COMPLETE] Drug File 확인")
        drug_sheet = drug_file.worksheets[0]
        return drug_sheet.rows
    except FileNotFoundError:
        logger.error("[ERROR] Drug File 확인 실패")
        exit()


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
    data_list = []

    # Get user info
    user_info = get_user_info('user.txt')

    # Get drug list
    # drug_list = get_drug_list('drug.xlsx')

    # Initiate driver
    driver = webdriver.Chrome('./chromedriver.exe')
    driver.maximize_window()
    driver.implicitly_wait(3)

    # Move to URL
    driver.get('https://www.kimsonline.co.kr/')
    time.sleep(0.3)

    # Log in
    driver.find_element_by_xpath('//*[@id="user_id"]').send_keys(user_info[0])
    driver.find_element_by_xpath('//*[@id="user_pw"]').send_keys(user_info[1])

    driver.find_element_by_xpath('//*[@id="frmLogin"]/div[3]/div[2]/a').click()
    driver.implicitly_wait(3)
    time.sleep(0.3)

    for drug in drug_list:
        temp_data = []

        # Move for searching drug
        driver.find_element_by_xpath('//*[@id="gnb"]/li[1]/a').click()
        driver.implicitly_wait(3)
        time.sleep(0.2)

        # Search drug
        driver.find_element_by_xpath('//*[@id="txtKDCode"]').send_keys(drug)
        driver.find_element_by_xpath('//*[@id="contents"]/div/div[6]/a[1]').click()
        driver.implicitly_wait(3)
        time.sleep(0.2)

        # Select drug
        driver.find_element_by_xpath('//*[@id="tabMarketS"]/ul/li/div[2]/div[1]/a').click()
        driver.implicitly_wait(3)
        time.sleep(0.2)

        # Select Menu
        driver.find_element_by_xpath('//*[@id="contents"]/div/div[5]/ul/li[4]').click()
        driver.implicitly_wait(3)
        time.sleep(0.2)

        # Get drug info
        bs4 = BeautifulSoup(driver.page_source, 'lxml')
        drug_info = bs4.find('div', id='ctl01_area_mediguide_brief').find_all('div', class_='mt10')
        print('==================== 1 ======================')
        print('효능')
        print(drug_info[0].get_text().strip().split('\n')[0])
        temp_data.append(drug_info[0].get_text().strip().split('\n')[0])
        print('==================== 2 ======================')
        print('복약 지도')
        for guide in drug_info[1].get_text().strip().split('\n')[0:-1]:
            print(guide)
            temp_data.append(guide)
        print(temp_data)
        data_list.append(temp_data)

    # Quit driver
    driver.quit()

    print('\n전체 리스트')
    print(data_list)

    data_fix_list = []
    for data in data_list:
        for fix_data in set_blank(data):
            data_fix_list.append(fix_data)

    print(data_fix_list)

    temp_excel(data_fix_list)

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
