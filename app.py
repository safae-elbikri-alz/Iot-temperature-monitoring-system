import paho.mqtt.client as mqtt
from flask import Flask, render_template ,jsonify
import json, sqlite3, psycopg2, psycopg2.extras
import urllib

app = Flask(__name__)
WAIT_SECONDS = 1
MAXTEMP=40

result = urllib.parse.urlparse("postgres://stanzrdluwcobx:90e71ac192c31e89e3d01acb0bb15983e1d8935c610c624b4f3aa5c280399555@ec2-3-230-106-126.compute-1.amazonaws.com:5432/ddugulfgvnsrnv")
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname

pins = {
       3 : {'name' : 'vert', 'board' : 'esp8266', 'topic' : 'esp8266/4', 'state' : 'False'},
       4 : {'name' : 'orange', 'board' : 'esp8266', 'topic' : 'esp8266/5', 'state' : 'False'},
       5 : {'name' : 'rouge', 'board' : 'esp8266', 'topic' : 'esp8266/6', 'state' : 'False'},
       }

@app.route('/')
def main():
    return render_template('main.html')

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def on_connect(client, userdata, flags, rc):
    client.subscribe("/esp8266/1/dhtreadings")
    client.subscribe("/esp8266/2/dhtreadings")
    client.subscribe("/esp8266/3/dhtreadings")

def on_message(client, userdata, message):
    if message.topic == "/esp8266/1/dhtreadings" or message.topic == "/esp8266/2/dhtreadings" or message.topic == "/esp8266/3/dhtreadings" :
        
        dhtreadings_json = json.loads(message.payload.decode("utf-8"))
        # conn=sqlite3.connect('sensordata.db')
        conn = psycopg2.connect(
            host=hostname,
            database=database,
            user=username,
            password=password
        )
        c=conn.cursor()
        if message.topic == "/esp8266/1/dhtreadings" : device="esp8266/1"
        if message.topic == "/esp8266/2/dhtreadings" : device="esp8266/2"
        if message.topic == "/esp8266/3/dhtreadings" : device="esp8266/3"
        c.execute("""INSERT INTO dhtreadings (temperature, humidity, currentdate, currentime, device) 
                VALUES(%s, %s, CURRENT_DATE, CURRENT_TIME, %s)""", (dhtreadings_json['temperature'],
                dhtreadings_json['humidity'], device) )
        conn.commit()
        conn.close()

@app.route('/data',methods=['GET', 'POST'])
def dataTemp():
    # conn = sqlite3.connect("sensordata.db")
    conn = psycopg2.connect(
        host=hostname,
        database=database,
        user=username,
        password=password
    )
    c = conn.cursor()
    c.execute("""SELECT count(*) from dhtreadings""")
    res = c.fetchone()
    c.execute("""SELECT id from dhtreadings limit 1""")
    nbr = c.fetchone()
    if(res[0]-100 > 0):
        threshold = res[0]-101
        threshold += nbr[0]
        c.execute("""DELETE FROM dhtreadings WHERE id < %s""", (str(threshold),))
        conn.commit()
    conn.close()
    return dataTemperature()

def dataTemperature():
    temperature1=[]
    temperature2=[]
    temperature3=[]
    # conn=sqlite3.connect('sensordata.db')
    conn = psycopg2.connect(
        host=hostname,
        database=database,
        user=username,
        password=password
    )
    # conn.row_factory = dict_factory
    c=conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    c.execute("SELECT temperature FROM dhtreadings where device='esp8266/1' ORDER BY id DESC LIMIT 10")
    readings1 = c.fetchall()

    c.execute("SELECT temperature FROM dhtreadings where device='esp8266/2' ORDER BY id DESC LIMIT 10")
    readings2 = c.fetchall()

    c.execute("SELECT temperature FROM dhtreadings where device='esp8266/3' ORDER BY id DESC LIMIT 10")
    readings3 = c.fetchall()
    
    conn.close()

    for row in readings1:
        temperature1.append(float(row["temperature"]))
    
    for row in readings2:
        temperature2.append(float(row["temperature"]))

    for row in readings3:
        temperature3.append(float(row["temperature"]))
    
    moyen1=0
    moyen2=0
    moyen3=0
    moyenG=0

    for i in range(min(min(len(temperature1),len(temperature2)),len(temperature3))):
        moyen1 += temperature1[i]
        moyen2 += temperature2[i]
        moyen3 += temperature3[i]
    
    moyen1 /= 10
    moyen2 /= 10
    moyen3 /= 10
    moyenG = (moyen1 + moyen2 + moyen3)/3
    leds=[0,0,0]
    if moyenG <= 25 :
            mqttc.publish(pins[3]['topic'],"1")
            mqttc.publish(pins[4]['topic'],"0")
            mqttc.publish(pins[5]['topic'],"0")
            leds[0]=1
            leds[1]=0
            leds[2]=0
            pins[3]['state'] = 'True'
            pins[4]['state'] = 'False' 
            pins[5]['state'] = 'False' 
    elif moyenG > 25 and moyenG <26 : 
            mqttc.publish(pins[4]['topic'],"1")
            mqttc.publish(pins[3]['topic'],"0")
            mqttc.publish(pins[5]['topic'],"0")
            leds[0]=0
            leds[1]=1
            leds[2]=0
            pins[4]['state'] = 'True' 
            pins[3]['state'] = 'False'
            pins[5]['state'] = 'False' 
    elif moyenG >= 26 : 
            mqttc.publish(pins[5]['topic'],"1")
            mqttc.publish(pins[4]['topic'],"0")
            mqttc.publish(pins[3]['topic'],"0")
            leds[0]=0
            leds[1]=0
            leds[2]=1
            pins[5]['state'] = 'True' 
            pins[3]['state'] = 'False' 
            pins[4]['state'] = 'False'

    return jsonify(temperature1=temperature1,
                    temperature2=temperature2,
                    temperature3=temperature3,
                    moyen1=moyen1,
                    moyen2=moyen2,
                    moyen3=moyen3,
                    moyenG=moyenG,
                    leds=leds)
    
mqttc=mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect("mqtt.eclipse.org",1883,60)
mqttc.loop_start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8181, debug=True)






