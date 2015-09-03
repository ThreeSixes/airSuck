//  config.js by ThreeSixes (https://github.com/ThreeSixes)
//
//  This project is licensed under GPLv3. See COPYING for dtails.
//
//  This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).

// Configuration elements
exports.getConfig = function() {
    return { webPort: 8090, // Port we want node.js to serve HTTP on.
        redisPort: 6379, // Redis TCP port
        redisHost: "<hostname here>", // Redis host with the state pub/sub queue.
        redisQueue: 'airStateFeed' // Name of the pub/sub queue.
        };
}
