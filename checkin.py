#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import os
from bs4 import BeautifulSoup
import requests
import time
import re
from urllib.parse import quote
import http.cookiejar as HC
from PIL import Image
import json

os.chdir(sys.path[0])
config = json.load(open("config.json", "r", encoding="UTF-8"))
#print(config)
push_config = config['push_config']
stuName = config['stuName']
course_list = config['course_list']
address = config['address']
log_config = config['log_config']

"""
    
    需要修改的地方, 请在config.json修改：
    1.课程参数：
    course_list = [
        {
            'name':  # 你的姓名
            'url':  # 课程的任务页面/活动首页
            'course_name':  # 课程名称，用于单课程签到指令和提示输出
        }
    ]
    
    2.位置信息
    address = {
        "latitude": "-1",  # 纬度
        'longitude': "-1",  # 经度
        'addr': "",  # 位置名称
        'ifTiJiao': "0"  # 是否开启提交位置信息，'0'关闭, '1'开启
    }
    
    3.拍照签到的图片
    请在该文件的目录下存放名字为up_img.jpg的图片
    如有拍照签到会自动上传该图片，否则会自动上传wyz！

"""

# <=========我是分割线========>

post_data = {
    'name': "",
    'puid': "",
    'courseId': "",
    'classId': "",
    'fid': "",
    'activeId': "",
}

header = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/80.0.3987.122 Safari/537.36',
    'Sec-Fetch-Dest': 'document',
    'Upgrade-Insecure-Requests': '1',
}

r_session = requests.session()


def save_html(text, filename):
    """保存html文件"""
    with open('%s.html' % filename, 'x') as f:
        f.write(text)
        print('文件%s.html已保存' % filename)


def check_is_login():
    """
    检测是否登录成功, 返回bool
    """
    request_url = 'http://i.mooc.chaoxing.com/space/'
    # print(request_url)
    response = r_session.get(url=request_url, headers=header)
    b_soup = BeautifulSoup(response.text, 'html.parser')
    title = b_soup.title.string
    if title == '用户登录':
        return False
    else:
        return True


def get_login_status(login_headers, login_data):
    """
    获取登录信息并转换成字典
    二维码未扫描返回:{"mes":"未登录","type":"3","status":false}
    二维码扫描未登录返回:{"uid":"","nickname":"","mes":"已扫描","type":"4","status":false}
    二维码扫描且登录返回: {"mes":"验证通过","status":true}
    二维码过期: {"mes":"二维码已失效","type":"2","status":false}
    二维码扫描取消登录： {"mes":"用户手机端取消登录","type":"6","status":false}
    """
    check_url = "http://passport2.chaoxing.com/getauthstatus"
    response = r_session.post(url=check_url, headers=login_headers, data=login_data)
    text = response.text
    text = text.replace('true', 'True')
    text = text.replace('false', 'False')
    dic = eval(text)
    return dic


def get_login_code(login_headers):
    login_url = 'http://passport2.chaoxing.com/cloudscanlogin?' \
                'mobiletip=%e7%94%b5%e8%84%91%e7%ab%af%e7%99%bb%e5%bd%95%e7%a1%ae%e8%ae%a4' \
                '&pcrefer=http://i.chaoxing.com'
    response = r_session.get(url=login_url, headers=login_headers)
    text = response.text
    b_soup = BeautifulSoup(text, 'html.parser')
    uuid = b_soup.find_all('input', id='uuid')[0]['value']
    enc = b_soup.find_all('input', id='enc')[0]['value']
    login_data = {'uuid': uuid, 'enc': enc}
    scanning_url = "http://passport2.chaoxing.com/createqr?uuid=" + uuid \
                   + "&xxtrefer=&type=1&mobiletip=%E7%94%B5%E8%84%91%E7%AB%AF%E7%99%BB%E5%BD%95%E7%A1%AE%E8%AE%A4"
    print("二维码扫描网址：" + scanning_url)
    response = r_session.get(url=scanning_url, headers=login_headers)
    try:
        with open('code_img.png', 'xb') as f:
            f.write(response.content)
    except:
        with open('code_img.png', 'wb') as f:
            f.write(response.content)
    Image.open('code_img.png').show()
    # qrcode_terminal.draw(scanning_url)
    input("扫描登陆后请确认(y):")
    return get_login_status(login_headers, login_data)


def re_login(login_headers):
    login_status = get_login_code(login_headers)
    if login_status['status']:
        print("登录成功")
        r_session.cookies.save()  # 将当前cookie保存上
    else:
        if login_status['type'] == '4':
            print("登录失败," + login_status['mes'] + "却未登录")
        else:
            print("登录失败," + login_status['mes'])


def login():
    """登陆函数"""
    # 登录地址
    login_headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/80.0.3987.122 Safari/537.36',
        'Upgrade-Insecure-Requests': '1',
        'Host': 'passport2.chaoxing.com',
        'Referer': 'https://passport2.chaoxing.com/login?fid=2182&refer=http://i.mooc.chaoxing.com',
        'Origin': 'https://passport2.chaoxing.com',
    }
    r_session.cookies = HC.LWPCookieJar(filename='cookies')  # 读取或生成一个cookie

    try:
        r_session.cookies.load(ignore_discard=True)
        if not check_is_login():
            print('cookie信息已过期，请重新登录')
            write_log("登陆已过期")
            raise Exception("{} 登录已过期".format(stuName))
            # re_login(login_headers)
        else:
            print('已登录')
            write_log("已登录")
    except:
        print('请登录')
        raise Exception("{} 未登录".format(stuName))
        # re_login(login_headers)


def upload_img(filename):
    url = 'https://pan-yz.chaoxing.com/upload?_token=5d2e8d0aaa92e3701398035f530c4155'
    mobile_header = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 10; MI 8 MIUI/20.2.27)'
                      ' com.chaoxing.mobile/ChaoXingStudy_3_4.3.6_android_phone_496_27 (@Kalimdor)'
                      '_994222229cb94d688c462b7257600006',
        'Host': 'pan-yz.chaoxing.com'
    }
    img = {}
    try:
        img = {"file": ("123.jpg", open(filename, "rb"))}
    except:
        print("找不到图片")
        print("http://pks3.ananas.chaoxing.com/star3/312_412c/5712278eff455f9bcd76a85cd95c5de3.jpg")
        return "5712278eff455f9bcd76a85cd95c5de3"  # wyz
    i_data = {'puid': "80421235"}
    response = r_session.post(url=url, headers=mobile_header, data=i_data, files=img)
    # print(response.text)
    print("照片预览：http://pks3.ananas.chaoxing.com/star3/312_412c/" + response.json().get('objectId') + ".jpg")
    return response.json().get('objectId')


def get_post_data(text):
    b_soup = BeautifulSoup(text, 'html.parser')
    post_data['puid'] = b_soup.find_all('input', id='puid')[0]['value']
    post_data['courseId'] = b_soup.find_all('input', id='courseId')[0]['value']
    post_data['classId'] = b_soup.find_all('input', id='classId')[0]['value']
    post_data['fid'] = b_soup.find_all('input', id='fid')[0]['value']


active_list = []


def get_active_id(text):
    """获取签到活动id"""
    b_soup = BeautifulSoup(text, 'html.parser')
    start_list = b_soup.find_all('div', id='startList')
    for x in start_list:
        y = x.find_all('div')
        for i in range(len(y)):
            try:
                rawid = y[i]['onclick']
                # active[0] 活动id  active[1] 活动种类。
                active = re.findall(r'activeDetail\((\d+),(\d+),.*?\)', rawid)[0]
                # 筛选签到活动,2为签到活动，42为问题
                if active[1] == '2':
                    active_list.append(active[0])
            except Exception as ret:
                pass


def normal_check(base_url):
    """普通签到"""
    args = "/widget/sign/pcStuSignController/preSign?" \
           + "activeId=" + post_data['activeId'] \
           + "&classId=" + post_data['classId'] \
           + "&fid=" + post_data['fid'] \
           + "&courseId=" + post_data['courseId']
    response = r_session.get(url=base_url + args, headers=header)
    return response


def hand_check(base_url):
    """手势签到"""
    args = "/widget/sign/pcStuSignController/signIn?" \
           + "&courseId=" + post_data['courseId'] \
           + "&classId=" + post_data['classId'] \
           + "&activeId=" + post_data['activeId']
    response = r_session.get(url=base_url + args, headers=header)
    return response


def qcode_check(base_url):
    """二维码签到"""
    args = "/pptSign/stuSignajax?" \
           + "name=" + quote(post_data['name']) \
           + "&activeId=" + post_data['activeId'] \
           + "&uid=" + post_data['puid'] \
           + "&clientip=&useragent=&latitude=-1&longitude=-1" \
           + "&fid=" + post_data['fid'] + "&appType=15"
    response = r_session.get(url=base_url + args, headers=header)
    return response


def addr_check(base_url):
    """位置签到"""
    args = "/pptSign/stuSignajax?" \
           + "name=" + quote(post_data['name']) \
           + "&address=" + address["addr"] \
           + "&activeId=" + post_data['activeId'] \
           + "&uid=" + post_data['puid'] \
           + "&clientip=" + "" \
           + "&latitude=" + address["latitude"] \
           + "&longitude=" + address["longitude"] \
           + "&fid=" + post_data['fid'] \
           + "&appType=" + '15' \
           + "&ifTiJiao=" + "1"
    response = r_session.get(url=base_url + args, headers=header)
    return response


def tphoto_check(base_url):
    """拍照签到"""
    objectid = upload_img("up_img.jpg")
    args = "/pptSign/stuSignajax?" \
           + "activeId=" + post_data['activeId'] \
           + "&uid=" + post_data['puid'] \
           + "&clientip=&useragent=&latitude=-1&longitude=-1" \
           + "&appType=15" \
           + "&fid=" + post_data['fid'] \
           + "&objectId=" + objectid \
           + "&name=" + quote(post_data['name'])
    response = r_session.get(url=base_url + args, headers=header)
    return response


def check_in():
    """post 签到"""
    allRes = []  # 所有签到任务的结果
    if not active_list:
        print("没有签到任务")
        write_log("没有签到任务")
        return allRes
    # 循环签到各个任务
    for active_id in active_list:
        res = {"type": "未知", "success": False}  # 单个签到任务的结果
        post_data['activeId'] = active_id
        base_url = 'https://mobilelearn.chaoxing.com'
        # 打开签到页
        response = normal_check(base_url)
        if re.findall(r'签到成功', response.text):
            print("==========>%s已签到成功" % active_id)
            write_log("==========>%s已签到成功" % active_id)
            res = {"type": "普通签到", "success": True}

        elif re.findall(r'手势图案', response.text):
            # 手势签到
            res['type'] = "手势签到"
            response = hand_check(base_url)
            if re.findall(r'签到成功', response.text):
                print("==========>%s手势签到成功" % active_id)
                write_log("==========>%s手势签到成功" % active_id)
                res['success'] = True


        elif re.findall(r'手机扫码', response.text):
            # 二维码签到
            res['type'] = "二维码签到"
            response = qcode_check(base_url)
            if re.findall(r'success', response.text):
                print("==========>%s二维码签到成功" % active_id)
                write_log("==========>%s二维码签到成功" % active_id)
                res['success'] = True

        elif re.findall(r'位置信息', response.text):
            # 位置签到
            res['type'] = "位置签到"
            response = addr_check(base_url)
            if re.findall(r'success', response.text):
                print("==========>%s位置签到成功" % active_id)
                write_log("==========>%s位置签到成功" % active_id)
                res['success'] = True

        elif re.findall(r'手机拍照', response.text):
            # 拍照签到
            res['type'] = "拍照签到"
            response = tphoto_check(base_url)
            if re.findall(r'success', response.text):
                print("==========>%s拍照签到成功" % active_id)
                write_log("==========>%s拍照签到成功" % active_id)
                res['success'] = True
        else:
            print('==========>%s签到失败,未知原因，详情请查看%s.html' % (active_id, active_id))
            write_log('==========>%s签到失败,未知原因，详情请查看%s.html' % (active_id, active_id))
            save_html(response.text, active_id)

        allRes.append(res)
        time.sleep(3)

    return allRes


def open_course_page(course):
    """打开课程活动页"""
    course_name = course['course_name']
    print('正在检查%s课程签到任务' % course['course_name'])
    write_log('正在检查%s课程签到任务' % course['course_name'])
    current_time = str(time.strftime("%m-%d %H:%M:%S", time.localtime()))
    request_url = course['url']
    response = r_session.get(url=request_url, headers=header)
    text = response.text
    active_list.clear()  # 获得id前清空
    get_post_data(text)  # 获取post_data
    get_active_id(text)  # 获取签到任务
    check_in_res = check_in()  # 签到

    # 检验并回传签到结果
    if len(check_in_res) == 0:
        push_result(course_name, False, "该课程当前没有签到任务")
        write_log(course_name + " 没有签到任务")
        return
    else:
        for res in check_in_res:
            if res['success']:
                push_result(course_name, True, "已完成以下签到: \n{}".format(json.dumps(check_in_res)))
                return

        push_result(course_name, False, "以下签到均失败: \n{}".format(json.dumps(check_in_res)))


def push_result(course_name: str, success: bool, message: str):
    title = "{} {} 签到{}".format(stuName, course_name, "成功" if success else "失败")
    push_body = {"appToken": push_config['app_token'],
                 "summary": title,
                 "content": message,
                 "contentType": 1,
                 "uids": [push_config['push_UID']]}
    push_header = {"Content-Type": "application/json"}
    if push_config['enable_push']:
        requests.post(url="http://wxpusher.zjiecode.com/api/send/message", data=json.dumps(push_body),
                      headers=push_header)

def write_log(context):
    if log_config['enable_log']:
        try:
            log_file = open(log_config['log_dir'], "a+", encoding="UTF-8")
            current_time = str(time.strftime("%y-%m-%d %H:%M:%S", time.localtime()))
            log_file.write("{}\t{}\n".format(current_time, context))
            log_file.close()
        except Exception as e:
            print("Log保存出错: " + str(e))

def main():
    #print(sys.argv)
    '''
    Parameter:
    -l Login 登录或重新登陆
    -a All 签到所有课程(可能封号，谨慎使用)
    -c [课程名] 签到指定课程
    '''

    course_name = "未知课程"

    try:
        #登录
        if len(sys.argv) == 1 or len(sys.argv) > 3:
            raise Exception("参数错误")

        elif sys.argv[1] == "-l":
            write_log("执行登录")
            login_headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/80.0.3987.122 Safari/537.36',
                'Upgrade-Insecure-Requests': '1',
                'Host': 'passport2.chaoxing.com',
                'Referer': 'https://passport2.chaoxing.com/login?fid=2182&refer=http://i.mooc.chaoxing.com',
                'Origin': 'https://passport2.chaoxing.com',
            }
            r_session.cookies = HC.LWPCookieJar(filename='cookies')  # 读取或生成一个cookie
            re_login(login_headers)

        elif sys.argv[1] == "-a":
            write_log("签到所有课程")
            #遍历所有课程
            login()
            for course in course_list:
                open_course_page(course)
                print('-' * 50)
                time.sleep(5)

        elif sys.argv[1] == "-c":
            write_log("签到{} 课程".format(sys.argv[2]))
            #签到指定课程
            if len(sys.argv) != 3:
                raise Exception("参数错误")
            course_name = sys.argv[2]
            for course in course_list:
                if course['course_name'] == course_name:
                    login()
                    open_course_page(course)
                    break

        else:
            raise Exception ("参数错误")

    except Exception as e:
        push_result(course_name, False, str(e))
        print(e)

def test_main():
    course_name = "未知课程"
    # 登录
    if len(sys.argv) == 1 or len(sys.argv) > 3:
        raise Exception("参数错误")

    elif sys.argv[1] == "-l":
        login_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/80.0.3987.122 Safari/537.36',
            'Upgrade-Insecure-Requests': '1',
            'Host': 'passport2.chaoxing.com',
            'Referer': 'https://passport2.chaoxing.com/login?fid=2182&refer=http://i.mooc.chaoxing.com',
            'Origin': 'https://passport2.chaoxing.com',
        }
        r_session.cookies = HC.LWPCookieJar(filename='cookies')  # 读取或生成一个cookie
        re_login(login_headers)

    elif sys.argv[1] == "-a":
        # 遍历所有课程
        login()
        for course in course_list:
            open_course_page(course)
            print('-' * 50)
            time.sleep(5)

    elif sys.argv[1] == "-c":
        # 签到指定课程
        if len(sys.argv) != 3:
            raise Exception("参数错误")
        course_name = sys.argv[2]
        for course in course_list:
            if course['course_name'] == course_name:
                login()
                open_course_page(course)
                break

if __name__ == '__main__':
    main()
    # push_result("中国传统戏曲鉴赏", False, "波波是clj")
