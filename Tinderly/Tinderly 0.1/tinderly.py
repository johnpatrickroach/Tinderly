# encoding: utf8                                                                                                                                           1,1           Top# encoding: utf8
import argparse
import configparser
from datetime import datetime
import json
from random import randint
import requests
import re
import sys
import robobrowser
from time import sleep
import datetime
import pynder
from messages import messages
from messagesbot import messagesbot
from messagesfake import messagesfake
from messagesreal import messagesreal

#### START SESSIONS ####

def log(msg):
    print '[' + str(datetime.datetime.now()) + ']' + ' ' + msg

def get_access_token(email, password, ua, url):
    s = robobrowser.RoboBrowser(user_agent=ua, parser="lxml")
    s.open(url)
    ## submit login form
    f = s.get_form()
    f["pass"] = password
    f["email"] = email
    s.submit_form(f)
    ## click the 'ok' button on the dialog informing you that you have already authenticated with the Tinder app
    f = s.get_form()
    s.submit_form(f, submit=f.submit_fields['__CONFIRM__'])
    ## get access token from the http response
    access_token = re.search(r"access_token=([\w\d]+)", s.response.content.decode()).groups()[0]
    return access_token

requests.packages.urllib3.disable_warnings()  # Find way around this...

config = configparser.ConfigParser(interpolation=None)
config.read('config.ini')

auth = str(config['DEFAULT']['FACEBOOK_AUTH_TOKEN'])

session = None

try:
    log("Trying to start Tinder session.")
    session = pynder.Session(str(config['DEFAULT']['FACEBOOK_ID']), auth)
except pynder.errors.RequestError:
    log("Pynder Error. Trying to get new auth.")
    auth = get_access_token(str(config['DEFAULT']['FB_EMAIL']), str(config['DEFAULT']['FB_PASSWORD']), str(config['DEFAULT']['MOBILE_USER_AGENT']), str(config['DEFAULT']['FB_AUTH']))
    config['DEFAULT']['FACEBOOK_AUTH_TOKEN'] = auth
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    config.read('config.ini')
    try:
        session = pynder.Session(str(config['DEFAULT']['FACEBOOK_ID']), auth)
    except pynder.errors.RequestError:
        log("Pynder Error. New auth did NOT work.")
        quit()

#### DEFINE FUNCTIONS ####

def like_or_nope():
    if randint(1, 100) == 31:
        return 'nope'
    else:
        return 'like'

def check_swipes():
    swipes_remaining = session.likes_remaining
    if swipes_remaining == 0:
        return 'Send messages'

def handle_likes():
    global session
    if session is not None:
        users = session.nearby_users()
        log(str(len(users)) + ' users to swipe')
        for u in users:
            try:
                log('Checking swipes remaining.')
                status = check_swipes()
                if status == 'Send messages':
                    log('Out of swipes. Moving along to send messages.')
                    break
                else:
                    try:
                        action = like_or_nope()
                        if action == 'like':
                            u.like()
                            log('Liked ' + u.name)
                            sleep(randint(3,15))
                        else:
                            u.dislike()
                            log('Disliked ' + u.name)
                            sleep(randint(3,15))
                    except ValueError:
                        log("ValueError")
                        break
                    except pynder.errors.RequestError:
                        log("Pynder Error. Trying to get new auth.")
                        auth = get_access_token(str(config['DEFAULT']['FB_EMAIL']), str(config['DEFAULT']['FB_PASSWORD']), str(config['DEFAULT']['MOBILE_USER_AGENT']), str(config['DEFAULT']['FB_AUTH']))
                        config['DEFAULT']['FACEBOOK_AUTH_TOKEN'] = auth
                        with open('config.ini', 'w') as configfile:
                            config.write(configfile)
                        config.read('config.ini')
                        try:
                            session = pynder.Session(str(config['DEFAULT']['FACEBOOK_ID']), auth)
                        except pynder.errors.RequestError:
                            log("Pynder Error. New auth did NOT work.")
                            break
                        continue
                    except:
                        log("Generic Exception. Don't know what issue is....")
                        break
            except ValueError:
                log("ValueError")
                break
            except pynder.errors.RequestError:
                log("Pynder Error. Trying to get new auth.")
                auth = get_access_token(str(config['DEFAULT']['FB_EMAIL']), str(config['DEFAULT']['FB_PASSWORD']), str(config['DEFAULT']['MOBILE_USER_AGENT']), str(config['DEFAULT']['FB_AUTH']))
                config['DEFAULT']['FACEBOOK_AUTH_TOKEN'] = auth
                with open('config.ini', 'w') as configfile:
                    config.write(configfile)
                config.read('config.ini')
                try:
                    session = pynder.Session(str(config['DEFAULT']['FACEBOOK_ID']), auth)
                except pynder.errors.RequestError:
                    log("Pynder Error. New auth did NOT work.")
                    break
                continue
            except:
                log("Generic Exception. Don't know what issue is....")
                break
    else:
        log("Sessions is None.")
        quit()

def send(match, message_no):
    for m in messages[message_no]:
        session._api._post('/user/matches/' + match['id'],
                            {"message": m})
        sleep(randint(3,10))
    log('Sent message ' + str(message_no) + ' to ' + match['person']['name'])

def sendbot(match, message_no_bot):
    for mb in messagesbot[message_no_bot]:
        session._api._post('/user/matches/' + match['id'],
                            {"message": mb})
        sleep(randint(3,10))
    log('Sent message ' + str(message_no_bot) + ' to ' + match['person']['name'])

def sendfake(match, message_no_fake):
    for mf in messagesfake[message_no_fake]:
        session._api._post('/user/matches/' + match['id'],
                            {"message": mf})
        sleep(randint(3,10))
    log('Sent message ' + str(message_no_fake) + ' to ' + match['person']['name'])

def sendreal(match, message_no_real):
    for mr in messagesreal[message_no_real]:
        session._api._post('/user/matches/' + match['id'],
                            {"message": mr})
        sleep(randint(3,10))
    log('Sent message ' + str(message_no_real) + ' to ' + match['person']['name'])

def message(match):
    ms = match['messages']
    myself = session.profile.id
    if not ms:
        send(match, 0)
        return
    said = False
    saidbot = False
    saidfake = False
    saidreal = False
    count = 0
    name = match['person']['name']
    for m in ms:
        if m['from'] == myself:
            count += 1
            said = False
        elif 'bot' in m['message'].lower():
            count += 1
            saidbot = True
        elif 'fake' in m['message'].lower():
            count += 1
            saidfake = True
        elif 'real person' in m['message'].lower():
            count += 1
            saidreal = True
        else:
            said = True
    if count >= len(messages):
        log('Finished conversation with ' + name)
        return
    if said:
        log('said = True')
        try:
            send(match,count)
        except Exception as err:
            log('Error sending message: %s' % err)
    elif saidbot:
        log('saidbot = True')
        try:
            sendbot(match,0)
        except Exception as err:
            log('Error sending message: %s' % err)
    elif saidfake:
        log('saidfake = True')
        try:
            sendfake(match,0)
        except Exception as err:
            log('Error sending message: %s' % err)
    elif saidreal:
        log('saidreal = True')
        try:
            sendreal(match,0)
        except Exception as err:
            log('Error sending message: %s' % err)
    else:
        log('No new messages from ' + name)

def handle_matches():
    log(str(len(session._api.matches())) + ' matches')
    matches = session._api.matches()
    for m in matches:
        message(m)


#### MAIN ####

while True:
    log('Handling likes.')
    handle_likes()
    log('Handling messages.')
    handle_matches()
    log('Resting for a few minutes...')
    sleep(randint(300,600))
