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
            logMode: "console", // Set the logging mode for stateNode. Supports "console", "syslog", and "none"
            enabled: true, // Even if the process starts, do we want this to run?
            webPort: 8090, // Port we want node.js to serve HTTP on.
            keepaliveInterval: (30 * 1000), // Set default interval to 30 sec
            redisHost: "<insert hostname here>", // Redis host with the state pub/sub queue.
            redisPort: 6379, // Redis TCP port
            redisQueue: "airSuckStatePub" // Name of the pub/sub queue.
        }
    };
}
