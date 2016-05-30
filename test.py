#import itchat, pprint
#from datetime import datetime
#from threading import Thread

#tbot = telegram.Bot(token="121040558:AAHNAfHCLl70V3RBw0im5wtn7MeLpiVEhsI")

#itchat.auto_login()

#@itchat.msg_register()
#def m(msg):
#    r = 'Wechat\nFrom: %s\nStatusNotifyUserName: %s\n%s: %s' % (
#        msg['FromUserName'], msg['StatusNotifyUserName'], msg['Type'], msg['Text'])
#    print(datetime.now().strftime("%c"), r)
#    tbot.sendMessage(chat_id=57995782, text=r)
#    #requests.post("https://api.telegram.org/bot121040558:AAHNAfHCLl70V3RBw0im5wtn7MeLpiVEhsI/sendMessage", {"chat_id": "57995782", "text": r}, proxies={"https": "socks5://127.0.0.1:8087"})

#a = itchat.send()

#pprint.pprint(a)

##itchat.run()


