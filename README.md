# AutoCheckin 学习通自动签到-服务器版
Fork自：https://github.com/Huangyan0804/AutoCheckin

**！！！支持普通签到，手势签到，二维码签到，拍照签到，位置签到**
学习通自动签到，针对早起不能学生，**需要自行提供参数**。

在原有签到功能基础上：
* 优化 修改调用参数，将签到与登录功能分离
* 优化 将登陆过期、未登录按异常处理
* 优化 将签到参数从代码中移除，保存在config.json中
* 新增 通过WxPusher推送执行结果
* 新增 日志记录功能


**已知cookie的有效时间为一个月，请放心使用**

**登录方式**：首次登录使用二维码登录，登录成功后，自动保存cookie，**下次无需重新登录，直到登陆过期**

## 一、参数修改：

请在config.json中修改以下参数

### 1.学生姓名（选填）

将用于推送签到结果和日志记录，便于多人共用一个服务器时定位问题
```json
  "stuName": "您的姓名"
```
### 2.课程参数：

```json
   "course_list": [
        {
            'url': "" // 课程的任务页面/活动首页
            'course_name':  // 课程名称，用于单课程签到指令和提示输出
        }
    ]
```
#### 课程URL为进入课程后右上角的任务

![1](images/2020-03-15-160930.png)

### 3.地址参数：
将用于位置签到时提交的地址

```json
 "address": {
    "latitude": "-1",//纬度
    "longitude": "-1",//经度
    "addr": "",//地址文字
    "ifTiJiao": "0"//是否提交地址
  }
```

### 4.拍照签到的图片
请在该文件的目录下存放名字为up_img.jpg的图片
如有拍照签到会自动上传该图片，否则会自动上传wyz！

### 5.WxPusher参数
WxPusher是一个建立在微信上的推送API，官方网站：https://wxpusher.zjiecode.com/

在这里可以设置WxPusher相关参数

```json
  "push_config": {"app_token": "AT_",//WxPusher的token
               "push_UID": "UID_",//接收消息的WxPusher UID
               "enable_push": true}//是否启用推送
```

### 6.日志保存设置
```json
"log_config": {
    "log_dir": "./checkin.log",//日志保存位置
    "enable_log": true//开启日志功能
  }
```


## 二、执行代码方式

分所有课程检测和单课程检测：

- 登陆方法

  ```bash
  python3 checkin.py -l
  ```

- 单课程签到调用方法：

  ```bash
  python3 checkin.py -c course_name
  ```

  **curse_name为上面修改的参数中curse_list里的curse_name**

- 所有课程签到调用方法：

  ```bash
  python3 checkin.py -a
  ```

  检测所有课程是否有签到任务。慎用，使用次数过多可能会被学习通拉入黑名单。


##  三、让Python脚本定时启动

准备好定时启动的脚本auto.py

用root权限编辑以下文件

```bash
sudo vim /etc/crontab
```

在文件末尾添加以下命令

```
2 * * * * root /usr/bin/python3.5 ~/auto.py > ~/auto.log

```

以上代码的意思是每隔两分钟执行一次脚本并打印日志。

**三、crontab编写解释**

基本格式

```
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed

```

**四、举例说明**

1、每分钟执行一次

```
* * * * * user command
```

2、每隔2小时执行一次

```
* */2 * * * user command (/表示频率)
```

3、每天8:30分执行一次

```
	
30 8 * * * user command
```

4、每小时的30和50分各执行一次

```
30,50 * * * * user command（,表示并列）
```

4、每个月的3号到6号的8:30执行一次

```
30 8 3-6 * * user command （-表示范围）
```

5、每个星期一的8:30执行一次

```
30 8 * * 1 user command （周的范围为0-7,0和7代表周日）
```

