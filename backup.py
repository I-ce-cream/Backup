import os
import datetime
import smtplib
import time
import configparser
from pathlib import Path
from email.mime.text import MIMEText
from email.header import Header

config = configparser.ConfigParser()
config.read("./backup.ini")

def main():

    global config
    ret = ''

    for key in config['PATH']:
        get_return = get_file_state(key,Path(config['PUBLIC_PATH'][key],config['PATH'][key]))

        if get_return == 'ERROR':
            ret = 'Unable to connect to 192.168.80.42\r\n'
            code = 0
            break
        else:
            ret += get_return
            code = 1

    return ret,code


def get_file_state(key,value):

    global config
    ret = ''
    file_path = str(value).format(OBJECT = key,TIME=datetime.datetime.now().strftime('%Y%m'))
    ret += file_path + '\r\n'

    if os.path.exists(file_path):

        last_mt = config.get('MODIFICATION_TIME',key+'_last_mt')
        last_size = config.get('SIZE',key+'_last_size')
        current_mt = config.get('MODIFICATION_TIME', key + '_current_mt')
        current_size = config.get('SIZE', key + '_current_size')
        size = str(round(os.path.getsize(file_path)/float(1024 * 1024),2)) + ' MB'
        mt_d = time.strftime('%Y%m%d', time.localtime(os.stat(file_path).st_mtime))
        nt_d = datetime.datetime.now().strftime('%Y%m%d')
        mt_s = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.stat(file_path).st_mtime))

        if current_mt != mt_s :
            ret += 'Last modification time   : ' + current_mt + '\r\n'
            ret += 'Current modification time: ' + mt_s + '\r\n'
            ret += 'Last size   : ' + current_size + '\r\n'
            ret += 'Current size: ' + size + '\r\n'

            config.set('MODIFICATION_TIME', key + '_last_mt',current_mt)
            config.set('MODIFICATION_TIME', key + '_current_mt', mt_s)
            config.set('SIZE', key + '_last_size', current_size)
            config.set('SIZE', key + '_current_size', size)

            with open("./backup.ini","w") as f:
                config.write(f)
        else:
            ret += 'Last modification time   : ' + last_mt + '\r\n'
            ret += 'Current modification time: ' + mt_s + '\r\n'
            ret += 'Last size   : ' + last_size + '\r\n'
            ret += 'Current size: ' + size + '\r\n'


        if mt_d != nt_d: ret += nt_d + ' No Backup\r\n'

        ret += '\r\n'
    else:
        ret = 'ERROR'

    return ret

def send_mail(ret,code):

    global config

    mail_host = config.get('MAIL','mail_host')  # 设置服务器
    mail_user = config.get('MAIL','mail_user')  # 用户名
    mail_pass = config.get('MAIL','mail_pass') # 口令

    sender = config.get('MAIL', 'sender')
    receivers = (config.get('MAIL', 'receivers')).split(',') if code == 1 else (config.get('MAIL', 'receivers_admin')).split(',') # 接收邮件，可设置为你的QQ邮箱或者其他邮箱,列表形式

    message = MIMEText(ret, 'plain', 'utf-8')
    message['From'] = sender
    message['To'] = ','.join(receivers)
    message['Subject'] = Header('备份信息', 'utf-8')

    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(mail_host, 25)  # 25 为 SMTP 端口号
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("邮件发送成功")

    except smtplib.SMTPException:
        print("Error: 无法发送邮件")

if __name__ == "__main__":
    ret, code = main()
    send_mail(ret,code)
