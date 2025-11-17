#pragma once

/**
 * Standard Message Header for all node-to-node communication.
 * Defined in the Software Architecture document.
 */
struct Header {
    // each message type has its own message ID, for example the Controller Input Message has an ID of 10.
    unsigned char message_id;

    //TODO units??? FIXME this does not have sub-second precision
    // standard Unix timestamp, seconds since the epoch.
    unsigned long timestamp;
};