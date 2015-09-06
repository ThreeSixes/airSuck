#!/usr/bin/python

"""
fakePlane2state by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).

This script creates two fake planes that fly in a pattern for testing purposes near the Portland, OR area.

"""

############
# Imports. #
############

import redis
import time
import json
import threading
import datetime
from airSuckUtil import airSuckUtil
from pprint import pprint

planes = {
    "planeA": {"addr": "000000", "idInfo": "LOLK293", "alt": 23000, "aSquawk": "1337",
        "path": [
            [-122.6244282253729,45.87777468084978],
            [-122.6702580811518,45.85225255348922],
            [-122.7030639976105,45.83078399052413],
            [-122.7432228717486,45.81028017452736],
            [-122.768490547341,45.779764959478],
            [-122.793899040158,45.7582448744234],
            [-122.8248911801784,45.73059123203424],
            [-122.8618465109774,45.71089636755359],
            [-122.8889373194507,45.69680832434836],
            [-122.9453383905105,45.68655510272042],
            [-122.9964540037353,45.67808066390402],
            [-123.0342195977975,45.66862195432697],
            [-123.0760957178762,45.65300752964632],
            [-123.1161362211911,45.62428147543732],
            [-123.1382965620439,45.59267823157025],
            [-123.1369456270555,45.56038139305127],
            [-123.1163320494008,45.51229329496551],
            [-123.0606690254897,45.49000499135133],
            [-122.9971229018395,45.48095142571001],
            [-122.8973466649545,45.47539257060718],
            [-122.8091428148705,45.46456745290308],
            [-122.7657759019643,45.45711383109457],
            [-122.719779631672,45.43955584172345],
            [-122.6711026595529,45.4171034125728],
            [-122.627777197282,45.40256705882809],
            [-122.5446416573429,45.39553359491209],
            [-122.4714168366544,45.39437611912778],
            [-122.4024673195631,45.39414196770699],
            [-122.3194494342309,45.40003710993401],
            [-122.2481171952747,45.40875977058361],
            [-122.1925238908529,45.42131636794134],
            [-122.1329359172377,45.44084451773312],
            [-122.0535980032638,45.46343153355544],
            [-121.9732017435364,45.47683583141579],
            [-121.8707540591467,45.47751221966776],
            [-121.829107626173,45.47659260640112],
            [-121.7514971441601,45.47714338938824],
            [-121.6785397022963,45.45956852289531],
            [-121.6068374092748,45.4378806686662],
            [-121.5571305360061,45.4151565372612],
            [-121.4976086618157,45.37561664184496],
            [-121.4816530079593,45.31605970525256],
            [-121.5212967767378,45.26835149236175],
            [-121.6170565826623,45.23839348485986],
            [-121.7481294468697,45.2381151792011],
            [-121.8185258523,45.26935025363882],
            [-121.8937675807389,45.31663332025648],
            [-121.9663146523693,45.37819895024439],
            [-121.9925958792687,45.43680987511404],
            [-122.0184543838966,45.51180850996971],
            [-122.0433347405656,45.60060502374598],
            [-122.0518846831239,45.65199196600777],
            [-122.0718897069964,45.70690865476063],
            [-122.1113184237573,45.76613102475005],
            [-122.1710297897333,45.8103659814832],
            [-122.2247306924591,45.84922918718203],
            [-122.2929513317541,45.87923504706025],
            [-122.3889160014035,45.89790161827874],
            [-122.4715336793379,45.90238252005491],
            [-122.5438540229024,45.90163971584846],
            [-122.6244282253729,45.87777468084978]
        ]
    },
    "planeB": {"addr": "ffffff", "idInfo": "WEE2162", "alt": 45000, "aSquawk": "7007",
        "path" :[
            [-121.5600282086012,45.71781882240106],
            [-121.5518097103086,45.72929012371073],
	    [-121.5615966875099,45.75405004123984],
            [-121.5941378737492,45.76730375677963],
            [-121.6024973365813,45.7694843870879],
	    [-121.6574777982479,45.77980815665623],
	    [-121.6635662152098,45.77975833001542],
            [-121.7297359871597,45.77937033578198],
            [-121.7833309674757,45.77813614653139],
            [-121.7892427465709,45.77813019786155],
            [-121.8328596463765,45.7809551108778],
            [-121.8329414558797,45.7819708706749],
            [-121.868267985742,45.79252129034939],
            [-121.8874010077942,45.80966579339254],
            [-121.9043186897832,45.83447454801998],
            [-121.9286354768591,45.85925720715827],
            [-121.9452035337941,45.8960074272909],
            [-121.9468244813942,45.91175238139293],
            [-121.9442077826126,45.94419511202284],
            [-121.9402353021501,45.96051478143732],
            [-121.9365137297043,45.97538385387666],
            [-121.9309473012885,45.9981365404587],
            [-121.9357575844895,46.01352004418513],
            [-121.9520182405953,46.03290894667477],
            [-121.9834785938106,46.04885216002887],
            [-122.0221534491378,46.05068611104577],
            [-122.0687357802131,46.04629896054585],
            [-122.1351706480246,46.05520123722507],
            [-122.1804285584717,46.05782112432355],
            [-122.2120337425135,46.05563707050499],
            [-122.2615215927621,46.04743604003188],
            [-122.280621347662,46.03498700946208],
            [-122.3195912304195,46.01260203360462],
            [-122.3237588656875,45.98983751046505],
            [-122.3430335623409,45.96796283470893],
            [-122.3594768219716,45.96254467698252],
            [-122.3912670531345,45.96345998670514],
            [-122.4353164749774,45.97768152627913],
            [-122.4687035070754,45.98470579197144],
            [-122.5078925496286,45.98527220777102],
            [-122.5363188595338,45.97141418819852],
            [-122.5586419479716,45.95550282271164],
            [-122.5790983182802,45.94552085350198],
            [-122.6093925359146,45.93496558973688],
            [-122.6497135737842,45.9321739321843],
            [-122.6850076913221,45.93311559559923],
            [-122.7166343825886,45.92750709980913],
            [-122.7226814633283,45.92743402693996],
            [-122.7555229973858,45.91337168374313],
            [-122.7762711594451,45.89945607568652],
            [-122.77778268519,45.89943679964356],
            [-122.7878446709537,45.88250264195776],
            [-122.7839525073115,45.85419863173608],
            [-122.786335584544,45.83317076494222],
            [-122.7887572778783,45.813195735104],
            [-122.7715007608656,45.79138082735414],
            [-122.7633369844844,45.77050022235037],
            [-122.758218266298,45.7516735618416],
            [-122.7655020347984,45.73131387656782],
            [-122.764666397989,45.70209170723943],
            [-122.7597252639675,45.68197998040322],
            [-122.7474937469548,45.65994096788253],
            [-122.7195909763276,45.64416101716309],
            [-122.690446381594,45.6344440378891],
            [-122.6728554278456,45.6245815270163],
            [-122.6538885057873,45.61675067484963],
            [-122.6321349587762,45.61197696668103],
            [-122.6090604734939,45.61124552390764],
            [-122.5725781923138,45.60149466326387],
            [-122.5292966974168,45.59100870513176],
            [-122.4946294979126,45.58834234092781],
            [-122.4497103150442,45.57176317999431],
            [-122.4252735663285,45.57302139800862],
            [-122.3793226206513,45.57652155859662],
            [-122.3519219524283,45.57178350121807],
            [-122.3343117213779,45.55484090425739],
            [-122.3024137469862,45.54595729633913],
            [-122.2694569085862,45.54734207968898],
            [-122.242237499898,45.55157333483896],
            [-122.2150192554119,45.55561033527739],
            [-122.1822689478212,45.57022507928266],
            [-122.1609198082231,45.58254540835078],
            [-122.1207393737451,45.58692808622278],
            [-122.0878440425111,45.5951909959047],
            [-122.0549176387697,45.60861863155048],
            [-122.0104478062188,45.62109010342734],
            [-121.9804143643868,45.63133349909445],
            [-121.9474769050392,45.64567130555065],
            [-121.9131162166095,45.66405135747458],
            [-121.8759815081311,45.68538130350673],
            [-121.8358191713291,45.70478025736416],
            [-121.7952909139528,45.70410593988216],
            [-121.7548434747683,45.70031094784944],
            [-121.7316914238344,45.69439612601579],
            [-121.6984823773181,45.69457725741318],
            [-121.6569265467749,45.69867061130451],
            [-121.6220413411448,45.70400292048734],
            [-121.5600282086012,45.71781882240106]
        ]
    },
        "planeC": {"addr": "111111", "idInfo": "NOPE", "alt": 40000, "aSquawk": "0666",
        "path":[
            [-122.7819382367395,45.2755262660390],
            [-122.7750111189807,45.24271915707939],
            [-122.7473122059587,45.19304917963442],
            [-122.7118054145914,45.15493783490472],
            [-122.6642491239348,45.13002437074105],
            [-122.5846835875,45.11694894124484],
            [-122.5178995732353,45.11777367002372],
            [-122.446950917591,45.13186919120719],
            [-122.3905961227114,45.16431919586981],
            [-122.3364334147009,45.18777578625057],
            [-122.2743622031347,45.22124196420266],
            [-122.2383425873117,45.24300128952716],
            [-122.18224208227,45.27932968652332],
            [-122.1625722762707,45.31226215353888],
            [-122.1311276233182,45.36217737157924],
            [-122.1339157765151,45.4047808890824],
            [-122.1407157687643,45.44888309965745],
            [-122.1451649006791,45.48454250973311],
            [-122.1519820677489,45.52424146422454],
            [-122.1529659142317,45.56263911207313],
            [-122.1474693296117,45.58838955144847],
            [-122.1333889166811,45.6140279478187],
            [-122.1156970034517,45.64699627620194],
            [-122.1038692652908,45.67959530015547],
            [-122.0983098556841,45.71100234864552],
            [-122.0804815822724,45.74376484492917],
            [-122.0728476880347,45.77906873952427],
            [-122.0692227277626,45.80746554528196],
            [-122.0721398700185,45.86651128239333],
            [-122.0789993192612,45.91202571197413],
            [-122.0876876698739,45.94085404092973],
            [-122.1025287979003,45.97473524991673],
            [-122.12770989703,46.01294856451722],
            [-122.1443590210502,46.02721350391064],
            [-122.1940309865826,46.04730915542616],
            [-122.2337774907209,46.05851073286142],
            [-122.2604128708556,46.0594261801553],
            [-122.321878149114,46.04614317121111],
            [-122.3582884802264,46.03938738570675],
            [-122.3825379141762,46.02756757017412],
            [-122.4230000517709,45.99736594200461],
            [-122.4496823951346,45.96090203149697],
            [-122.4674172258622,45.93347903453105],
            [-122.4848167442997,45.89602580262789],
            [-122.4945462429629,45.87731207418985],
            [-122.4978956741058,45.83886570832327],
            [-122.5009189883067,45.79317756819276],
            [-122.5023398204647,45.76182605498805],
            [-122.5118626509804,45.73033559173552],
            [-122.5274768943259,45.69734099166655],
            [-122.5492612943109,45.66711707245304],
            [-122.5687548999809,45.62834226826067],
            [-122.5921442472334,45.58237524818701],
            [-122.6055416530494,45.54651526009916],
            [-122.6102253356458,45.48934096409639],
            [-122.6096665594213,45.46649847121231],
            [-122.6207771855012,45.42065062291694],
            [-122.642358911651,45.38751508292281],
            [-122.6720092650129,45.3542744439206],
            [-122.707561841471,45.31955650959156],
            [-122.7477820651035,45.30328536362587],
            [-122.7819382367395,45.27552626603909]
        ]
    }
}

#################
# Configuration #
#################

# Which queue do we subscribe to?
targetHost = "brick"
destPubSub = "airStateFeed"

# How long should it take to expire planes in seconds.
expireTime = 300

# How long to wait in order to play the next point.
stepDelay = 2

##############################
# Classes for handling data. #
##############################

class SubListener(threading.Thread):
    """
    Play the fake plene loops.
    """
    def __init__(self, r, destPubSub, planes):
        threading.Thread.__init__(self)
        self.destPubSub = destPubSub
        self.redis = r
        
        return

    def worker(self):
        while True:
            # Loop though plane A
            for coords in planes['planeA']['path']:
                self.redis.publish(self.destPubSub, json.dumps({'type': 'airSSR', 'addr': planes['planeA']['addr'], 'idInfo': planes['planeA']['idInfo'], 'aSquawk': planes['planeA']['aSquawk'], 'alt': planes['planeA']['alt'], 'lon': coords[0], 'lat': coords[1]}))
                # Wait a bit before continuing.
                time.sleep(stepDelay)
            
            # Loop through plane B
            for coords in planes['planeB']['path']:
                self.redis.publish(self.destPubSub, json.dumps({'type': 'airSSR', 'addr': planes['planeB']['addr'], 'idInfo': planes['planeB']['idInfo'], 'aSquawk': planes['planeB']['aSquawk'], 'alt': planes['planeB']['alt'], 'lon': coords[0], 'lat': coords[1]}))
                # Wait a bit before continuing.
                time.sleep(stepDelay)
            
            # Loop through plane C
            for coords in planes['planeC']['path']:
                self.redis.publish(self.destPubSub, json.dumps({'type': 'airSSR', 'addr': planes['planeC']['addr'], 'idInfo': planes['planeC']['idInfo'], 'aSquawk': planes['planeC']['aSquawk'], 'alt': planes['planeC']['alt'], 'lon': coords[0], 'lat': coords[1]}))
                # Wait a bit before continuing.
                time.sleep(stepDelay)
    
    def run(self):
        self.worker()
        
if __name__ == "__main__":
    print("Fake plane generator starting...")
    
    # Set up Redis queues.
    r = redis.Redis(host=targetHost)
    
    # Start up our ADS-B parser
    client = SubListener(r, destPubSub, planes)
    client.daemon = True
    # .. and go.
    client.start()
    
    try:
        while True: time.sleep(10)
    except KeyboardInterrupt:
        # Die nicely.
        quit()
    except Exception as e:
        print("Caught unhandled exception")
        pprint(e)