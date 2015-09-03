//  config.js by ThreeSixes (https://github.com/ThreeSixes)
//
//  This file serves as a config file for stateNode.js.
//
//  This project is licensed under GPLv3. See COPYING for dtails.
//
//  This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).

// Configuration elements
exports.getConfig = function() {
    return {
        webPort: 8090, // Port we want node.js to serve HTTP on.
        keepaliveInterval: (30 * 1000), // Set default interval to 30 sec
        redisHost: "<hostname here>", // Redis host with the state pub/sub queue.
        redisPort: 6379, // Redis TCP port
        redisQueue: 'airStateFeed' // Name of the pub/sub queue.
    };
}
