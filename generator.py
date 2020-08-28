from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

import LDAPgen
import smtplib
import configparser
import excelgen
import random
import os
import logging
import logging.config
import datetime
import socket
import time

logging.config.fileConfig(fname='logging.ini')
loger = logging.getLogger('dev')

def configure(config_name):
    config = configparser.ConfigParser()
    config.read(config_name)

    group_list = config["LDAP"]["group_list"].split(',')
    mail_servers = config["Mail"]["mail_host"].split(';')
    mail_ports = config["Mail"]["mail_port"].split(';')
    dns_servers = config["LDAP"]["ldap_url"].split(';')

    return config, group_list, mail_servers, mail_ports, dns_servers


def get_emails_and_files(config, users, group_list):
    email_information = {}

    try:
        for i in range(0, len(config["Directions"]) // 2):
            to_parse = config["Directions"]["direction." + str(i)].split("->")
            files = os.listdir(config["Directions"]["dir." + str(i)])
            if len(to_parse) == 2:
                for file in files:
                    if group_list.__contains__(to_parse[0]):
                        if to_parse[0] == to_parse[1]:
                            sender_num = random.randint(0, len(users[to_parse[0]]) // 2 - 1)
                        else:
                            sender_num = random.randint(0, len(users[to_parse[0]]) - 1)
                        sender = users[to_parse[0]][sender_num]['email'].decode('utf-8').lower()
                    else:
                        sender = to_parse[0].lower()

                    if group_list.__contains__(to_parse[1]):
                        if to_parse[0] == to_parse[1]:
                            recipient_num = random.randint(len(users[to_parse[0]]) // 2, len(users[to_parse[0]]) - 1)
                        else:
                            recipient_num = random.randint(0, len(users[to_parse[1]]) - 1)
                        recipient = users[to_parse[1]][recipient_num]['email'].decode('utf-8').lower()
                    else:
                        recipient = to_parse[1].lower()

                    email_information.update({(sender + recipient + file):
                                                  {'sender': sender,
                                                   'recipient': recipient,
                                                   'file': config["Directions"]["dir." + str(i)] + '\\' + file,
                                                   'filename': file,
                                                   'sender_group': to_parse[0],
                                                   'recipient_group': to_parse[1]}})
            else:
                raise RuntimeError("Wrong directions for {} in config.ini".format(config["Directions"]["direction." +
                                                                                                       str(i)]))
    except RuntimeError:
        logging.exception('Wrong directions.')

    return email_information


def get_emails_and_files_from_template(config, users, group_list):
    email_information = {}
    template = excelgen.get_template(config["Template"]["filename"])
    for i in range(3, len(template) + 3):
        if group_list.__contains__(template[i]['sender']):
            if template[i]['sender'] == template[i]['recipient']:
                sender_num = random.randint(0, len(users[template[i]['sender']]) // 2 - 1)
            else:
                sender_num = random.randint(0, len(users[template[i]['sender']]) - 1)
            sender = users[template[i]['sender']][sender_num]['email'].decode('utf-8').lower()
        else:
            sender = template[i]['sender'].lower()

        if group_list.__contains__(template[i]['recipient']):
            if template[i]['sender'] == template[i]['recipient']:
                recipient_num = random.randint(len(users[template[i]['sender']]) // 2,
                                               len(users[template[i]['sender']]) - 1)
            else:
                recipient_num = random.randint(0, len(users[template[i]['recipient']]) - 1)
            recipient = users[template[i]['recipient']][recipient_num]['email'].decode('utf-8').lower()
        else:
            recipient = template[i]['recipient'].lower()

        file = template[i]['filename']
        email_information.update({(sender + recipient + file): {'sender': sender,
                                                                'recipient': recipient,
                                                                'file': file,
                                                                'filename': template[i]['filename'],
                                                                'sender_group': template[i]['sender'],
                                                                'recipient_group': template[i]['recipient']}})

    return email_information, template


def send_messages(config, users, group_list, mail_host, mail_port):
    try:
        if config["Mail"]["generation_type"] == "config":
            email_information = get_emails_and_files(config, users, group_list)
        elif config["Mail"]["generation_type"] == "template":
            email_information, template = get_emails_and_files_from_template(config, users, group_list)
        else:
            raise RuntimeError('Wrong "generation_type" in config.ini')
    except RuntimeError:
        logging.exception('Wrong generation_type.')

    try:
        mail_server = smtplib.SMTP(mail_host, mail_port)
        mail_server.starttls()
        mail_server.login(config["LDAP"]["ad_username"], config["LDAP"]["ad_password"])
        loger.info('Connection established to ' + mail_host + ':' + mail_port)
        i = 1
        for email in email_information:
            message = MIMEMultipart()
            message["From"] = email_information[email]['sender']
            message["To"] = email_information[email]['recipient']
            message["Subject"] = str(email_information[email]['sender_group'] +
                                 "->" +
                                email_information[email]['recipient_group'] +
                                email_information[email]['filename'])
#                "{}{}{};{}".format(email_information[email]['sender_group'],
#                                                    '->',
#                                                    email_information[email]['recipient_group'],
#                                                    email_information[email]['filename'])
            # message.attach(MIMEText("Hello there", "plain"))
            if email_information[email]['file']:
                with open(email_information[email]['file'], "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {email_information[email]['file']}",
                )
                message.attach(part)

            text = message.as_string()
            mail_server.sendmail(email_information[email]['sender'], email_information[email]['recipient'], text)
            loger.info('Sende massage ' + str(i) + ': '
                         + email_information[email]['sender'] + '->' + email_information[email]['recipient'])
            loger.info('Attached file: ' + email_information[email]['filename'])
            i+=1
            time.sleep(float(config["Mail"]["timeout"]))
        mail_server.quit()
    except smtplib.SMTPServerDisconnected:
        loger.exception('Wrong mail_port for mail_host ' + mail_host + '.')
    except socket.gaierror:
        loger.exception('Wrong mail_host ' + mail_host + '.')


if __name__ == "__main__":

#    file_log = logging.FileHandler('generator_logger.log')
#    console_out = logging.StreamHandler()
#    logging.basicConfig(handlers=(file_log, console_out),
#                        format='[%(asctime)s %(levelname)s]: %(message)s',
#                        datefmt='%m.%d.%Y %H:%M:%S.ss',
#                        level=logging.INFO)
 #   logging.basicConfig(filename="generator_logger.log", level=logging.INFO)
    loger.info('The app is running.')

    config, group_list, mail_servers, mail_ports, dns_servers = configure("config.ini")

    try:
        if len(mail_ports) == len(mail_servers) == len(dns_servers):
            for i in range(0, len(mail_servers)):
                users = LDAPgen.get_users(config, group_list, dns_servers[i])
                send_messages(config, users, group_list, mail_servers[i], mail_ports[i])
        else:
            raise RuntimeError()
    except RuntimeError:
        logging.exception('Number of "mail_host", "mail_ports" and "ldap_url" '
                                                               'must be equal.')
    loger.info('The application was completed successfully.')
