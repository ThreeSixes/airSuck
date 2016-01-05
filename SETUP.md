#Single-system Ubuntu install and configuration for ADS-B
####This installation is for a single system only. You can easily configure AIRSuck to connect to multiple dump1090 instances using the dump1090 connector and mutlipe AIS targets using the AIS connector. If the airSuckClient is installed and configured on many machines one airSuck server can recieve traffic from them.

##If you want to use airSuck to pick up ADS-B from aircraft, etc. run first few steps here.
####Note: If you want AIS support you'll need to know the IP address and TCP port of one or more AIS sources.

####First, you'll need an [RTL-SDR compatible with dump1090](http://amzn.com/B00P2UOU72).

###Install MalcolmRobb's dump1090 fork. You'll also need to install a couple dependencies first.
```shell
$ sudo apt-get install librtlsdr-dev librtlsdr0 libusb-dev
$ git clone https://github.com/MalcolmRobb/dump1090.git
$ cd dump1090
$ make
$ cd ..
$ sudo mv dump1090 /opt
```
###Now install airSuck and its dependencies.

####Next install the necessary dependencies for airSuck.
```shell
$ sudo apt-get install python supervisor monogodb-server redis-server nodejs npm python-redis
```

Then install the necessary nodeJS packages for stateNode.js
```shell
$ sudo npm install express
$ sudo npm install node-syslog
$ sudo npm install redis
$ sudo npm install socket.io
$ sudo npm install socket.io-emitter
```
Once all of the dependencies have been satisfied we can use git to pull airSuck. By default airSuck expects to be in /opt so we'll install it there.
```shell
$ cd /opt/
$ sudo git clone https://github.com/ThreeSixes/airSuck.git
```

Copy relevant airSuck config files into place.
```shell
$ cd /opt/airSuck
$ sudo cp config/config.py .
$ sudo cp config/nodeConfig.js node/
```

Copy supvervisor config files into place. These files keep various components of airSuck running.
```shell
$ cd /opt/airSuck
$ sudo cp supvervisor/airSuck-airSuckServer.py /etc/supervisor/conf.d/
$ sudo cp supvervisor/airSuck-airSuckClient.py /etc/supervisor/conf.d/
$ sudo cp supvervisor/airSuck-ssrStateEngine.py /etc/supervisor/conf.d/
$ sudo cp supvervisor/airSuck-mongoDump.py /etc/supervisor/conf.d/
$ sudo cp supvervisor/airSuck-stateMongoDump.py /etc/supervisor/conf.d/
$ sudo cp supvervisor/airSuck-mongoDump.py /etc/supervisor/conf.d/
$ sudo cp supvervisor/airSuck-stateNode.py /etc/supervisor/conf.d/
```

Editing config.py - since this a single-host installation minimal configuration will be required.
WARNING: This configuration file is actually Python code which depends on the arrangment of the whitespace at the beginning of each line. Don't remove spaces or tabs before configuration variables.

```shell
$ sudo nano /opt/airSuck/config.py
```

In config.py edit the genHost variable to contain the name of your computer like so:
```python
genName = "myComputer"
```
Change both genRedisHost and genMongoHost to 127.0.0.1 since you're running Redis and MongoDB on your own machine. It shouldn't be necessary to edit the ports unless you're running Redis or MongoDB on a non-default port.
```python
genRedisHost = "127.0.0.1"
genMongoHost = "127.0.0.1"
```

Now we'll configure the airSuckCliient.py script under airSuckClientSettings.

Change the connSrvHost line to 127.0.0.1 like so:
```python
'connSrvHost': "127.0.0.1",
```
Optionally you can also activate position reporting. This will help airSuck plot your location in Google Maps, and will also enable local CPR decoding for aircraft, etc.
If you choose to enable it follow these steps:

Change reportPos to True:
```python
'reportPos': True,
```
Change the myPos variables to the location of the computer running dump1090 and airSuck.
In this example I'm using the GPS coordinates of a park in Portland, OR. You can obtain your location by using Google Maps and right-clicking the spot you're in, then clicking "What's here?" or using a GPS.
My example yields a latitude and longitude of 45.520851 and -122.625855 respectively. Replace the first 0.0 with your latitude, and the second 0.0 in the array with your longitude like so:
```python
'myPos': [45.520851, -122.625855, "manual"],
```
We can now edit node/nodeConfig.js. Only one variable needs to be modified:

```shell
$ sudo nano /opt/airSuck/config.py
```

Change redisHost to 127.0.0.1.
```javascript
redisHost: "127.0.0.1",
```
Plug in your RTL-SDR and antenna to the machine running airSuck.

Assuming all went well previously we can start supervisor
```shell
$ /etc/init.d/supervisor start
```
If that fails try this:
```shell
$ /etc/init.d/supervisor restart
```
Once supervisor restarts you can point your browser to http://127.0.0.1:8090 to see a map and list of ADS-B targets.

Troubleshooting:

1) Check supevisor to make sure everything is running.
If the browser isn't showing data you can check the status of the software using:

```shell
$ sudo supervisorctl
```
You'll see a list of airSuck processes. If any of them are listed in a state other than RUNNING it means something went wrong. Check the log files under /etc/supervisor/ for more details about the error message.

2) If in the browser you're not seeing aircraft in the list or on the screen make sure there are aircraft overhead and that you have a relatively clear view of the sky. Radio reception is key. You can also edit config.py and add the --aggressive flag to the dump1090Args section of the airSuckClient config.

3) Determine your RTL-SDR's PPM correction using KAL and add the --ppm argument with the value from Kal to the dump1090Args section of the airSuckClient config in config.py