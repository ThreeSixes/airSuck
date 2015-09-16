//  config.js by ThreeSixes (https://github.com/ThreeSixes)
//
//  This file serves as a config file for stateNode.js and client.js.
//
//  This project is licensed under GPLv3. See COPYING for dtails.
//
//  This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).

// Configuration elements
exports.getConfig = function() {
    return {
        server: { // Server configuration starts here.
            enabled: true, // Even if the process starts, do we want this to run?
            webPort: 8090, // Port we want node.js to serve HTTP on.
            keepaliveInterval: (30 * 1000), // Set default interval to 30 sec
            redisHost: "<insert hostname here>", // Redis host with the state pub/sub queue.
            redisPort: 6379, // Redis TCP port
            redisQueue: "airStateFeed" // Name of the pub/sub queue.
        }, client1090: { // Dump1090 client configuration.
            enabled: true, // Even if the process starts do we want the dump1090 client to run?
            srcName: "<insert unique name here>", // Name of source that should appear in the database.
            dump1090Host: "<insert hostname here>", // Hostname or IP running the dump1090 service.
            dump1090Port: 30002, // "Binary" dump1090 data port number.
            connectDelay: (5 * 1000) // Global reconnect attempt delay (for the dump1090 process and the destination server)
        }
    };
}
