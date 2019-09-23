import os
import datetime
import smtplib
import time
import configparser
from pathlib import Path
from email.mime.text import MIMEText
from email.header import Header
import logging
import sys

config = configparser.ConfigParser()
config.read("./backup.ini")
# config.read(Path('E:\\','BackupCheck','backup.ini'))

logging.basicConfig(filename="backup.log", filemode="a", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG)

def main():

    global config

    logger = logging.getLogger(sys._getframe().f_code.co_name)
    logger.info("读取备份信息")
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

    logger.info("读取信息结束")
    return ret,code


def get_file_state(key,value):

    global config

    logger = logging.getLogger(sys._getframe().f_code.co_name)

    ret = ''
    file_path = str(value).format(OBJECT = key,TIME=datetime.datetime.now().strftime('%Y%m'))
    ret += file_path + '\r\n'

    if os.path.exists(file_path):
        logger.info(key.upper()+" 路径访问成功: "+file_path)

        last_mt = config.get('MODIFICATION_TIME',key+'_last_mt')
        last_size = config.get('SIZE',key+'_last_size')
        current_mt = config.get('MODIFICATION_TIME', key + '_current_mt')
        current_size = config.get('SIZE', key + '_current_size')
        size = str(round(os.path.getsize(file_path)/float(1024 * 1024),2)) + ' MB'
        mt_d = time.strftime('%Y%m%d', time.localtime(os.stat(file_path).st_mtime))
        nt_d = datetime.datetime.now().strftime('%Y%m%d')
        mt_s = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.stat(file_path).st_mtime))

        if mt_d != nt_d:
            ret += nt_d + ' No Backup\r\n'
            logger.info(key.upper() + " 本日没有进行备份")
        else:
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

            logger.info(key.upper() + " 备份信息更新")

        ret += '\r\n'
    else:
        logger.info("路径无法访问: " + file_path)
        ret = 'ERROR'

    return ret

def send_mail(ret,code):

    global config

    logger = logging.getLogger(sys._getframe().f_code.co_name)

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
        logger.info("邮件发送成功 Receivers："+ ','.join(receivers))

    except smtplib.SMTPException:
        print("Error: 无法发送邮件")
        logger.info("邮件发送失败,检查邮箱配置信息")

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("<<备份检查开始----------------------------------------------------------------------------------------------------")
    ret, code = main()
    send_mail(ret,code)
    logger.info("备份检查结束---------------------------------------------------------------------------------------------------->>")
