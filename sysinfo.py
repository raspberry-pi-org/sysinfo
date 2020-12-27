'''
Author: GoogTech
Date: 2020-12-27 10:36:50
LastEditTime: 2020-12-27 13:37:04
Description: Get The System Information Of RasPi Then Ouput Voice Prompt And Send It To Your WeChat.
'''
import os
import time
import requests
import subprocess
from config import *
from aip import AipSpeech
from apscheduler.schedulers.blocking import BlockingScheduler


# Return CPU temperature as a character string
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return (res.replace("temp=", "").replace("'C\n", ""))


# Return RAM information (unit=kb) in a list
# Index 0: total RAM
# Index 1: used RAM
# Index 2: free RAM
def getRAMinfo():
    p = os.popen('free')
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i == 2:
            return (line.split()[1:4])


# Return % of CPU used by user as a character string
def getCPUuse():
    return (str(
        os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip()))


# Return information about disk space as a list (unit included)
# Index 0: total disk space
# Index 1: used disk space
# Index 2: remaining disk space
# Index 3: percentage of disk used
def getDiskSpace():
    p = os.popen("df -h /")
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i == 2:
            return (line.split()[1:5])


# Return ip address
def getIpAddress():
    p = os.popen("hostname -I")
    return p.readline().strip()


# Return local time
def getLocalTime():
    p = time.strftime("%p %H %M", time.localtime(time.time()))
    t = p.split()[1] + '点' + p.split()[2] + '分'
    return '上午' + t if t.split()[0] == 'AM' else '下午' + t


# Show system information
def show_sysinfo():
    print('Hello,现在是' + Local_time)
    print('')
    print('当前树莓派的IP地址为: ' + IP_address)
    print('')
    print('当前CPU的温度为: ' + CPU_temp + '℃')
    print('CPU的使用率为: ' + CPU_usage + '%')
    print('')
    print('系统RAM的总量为: ' + str(RAM_total) + 'MB')
    print('当前RAM已使用: ' + str(RAM_used) + 'MB')
    print('空闲的RAM为: ' + str(RAM_free) + 'MB')
    print('')
    print('系统盘的容量为: ' + str(DISK_total) + 'B')
    print('当前系统盘已使用: ' + str(DISK_used) + 'B')
    print('系统盘的使用率为: ' + str(DISK_perc))
    sysinfo_forecast_txt = \
                    'Hello,现在是%s。' \
                    '当前树莓派的IP地址为:%s。' \
                    '当前CPU的温度为:%s, ' \
                    'CPU的使用率为:%s。' \
                    '系统RAM的总量为:%s, ' \
                    '当前RAM已使用:%s, ' \
                    '空闲的RAM为:%s。' \
                    '系统盘的容量为:%s, ' \
                    '当前系统盘已使用:%s, ' \
                    '系统盘的使用率为:%s。' % \
                    (
                        Local_time,
                        IP_address,
                        CPU_temp + '℃',
                        CPU_usage + '%',
                        str(RAM_total) + 'MB',
                        str(RAM_used) + 'MB',
                        str(RAM_free) + 'MB',
                        str(DISK_total) + 'B',
                        str(DISK_used) + 'B',
                        str(DISK_perc),
                    )
    return sysinfo_forecast_txt


# Voice prompt by Baidu API
def Voice_broadcast(sysinfo_forcast_txt):
    sys_info = sysinfo_forcast_txt
    # 将树莓派系统信息推送到微信
    if SendToWeChat(sysinfo_forcast_txt):
        sys_info = sys_info + \
        '最后, 以上树莓派系统信息已通过「Server 酱」推送到了你的微信~'
    else:
        sys_info = sys_info + \
        '注意: 以上树莓派系统信息无法通过「Server 酱」推送到你的微信!'
    # 百度语音合成, 参数配置详见: https://ai.baidu.com/ai-doc/SPEECH/Qk38y8lrl
    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
    result = client.synthesis(sys_info, 'zh', 1, {'vol': 5, 'per': 0})
    if not isinstance(result, dict):
        with open(BAIDU_TTS_MP3, 'wb') as f:
            f.write(result)
        f.close()
    subprocess.getoutput('mplayer .tts.mp3')


# Return system information to WeChat By ServerChan
def SendToWeChat(weather_forecast_txt):
    # text 为推送的 title, desp 为推送的 description
    title = "树莓派系统信息来咯~"
    content = weather_forecast_txt
    data = {"text": title, "desp": content}
    # 发送( 同样内容的消息一分钟只能发送一次, 服务器只保留一周的消息记录 )
    return True if requests.post(SERVER_API,
                                 data=data).status_code == 200 else False


# run this program
def run():
    sysinfo_forecast_txt = show_sysinfo()
    print("\n\n" + sysinfo_forecast_txt)
    Voice_broadcast(sysinfo_forecast_txt)


# CPU informatiom
CPU_temp = getCPUtemperature()
CPU_usage = getCPUuse()

# RAM information
# Output is in kb, here I convert it in Mb for readability
RAM_stats = getRAMinfo()
RAM_total = round(int(RAM_stats[0]) / 1000, 1)
RAM_used = round(int(RAM_stats[1]) / 1000, 1)
RAM_free = round(int(RAM_stats[2]) / 1000, 1)

# Disk information
DISK_stats = getDiskSpace()
DISK_total = DISK_stats[0]
DISK_used = DISK_stats[1]
DISK_perc = DISK_stats[3]

# Ip address
IP_address = getIpAddress()

# Local time
Local_time = getLocalTime()

if __name__ == '__main__':
    # 定时执行程序, 每天在时间区间 [08:00 ~ 22:00] 内整点语音提示
    scheduler = BlockingScheduler()
    # scheduler.add_job(run,
    #                   'cron',
    #                   hour='08-22',
    #                   minute='00',
    #                   second='00',
    #                   id='sysinfo')

    # 从开始时间到结束时间, 每隔俩小时运行一次, 即共进行了 8 次整点语音提示
    scheduler.add_job(run,
                      'interval',
                      hours=2,
                      start_date='2020-12-01 08:00:00',
                      end_date='2021-12-12 22:00:00')

    scheduler.start()