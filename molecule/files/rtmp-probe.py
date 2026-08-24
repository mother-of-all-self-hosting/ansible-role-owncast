#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Slavi Pantaleev
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Probes an Owncast RTMP ingest endpoint and reports what it did, as JSON.
#
# Usage: rtmp-probe.py <host> <port> <stream-key>
#
# Owncast only accepts a broadcast once the publisher has completed the RTMP
# handshake, negotiated a connection and named a stream key that the server
# recognizes. Driving those three steps is what separates "something is
# listening on 1935" from "the ingest server is working and enforcing its
# stream key". A real broadcaster (ffmpeg, OBS) would go on to push video;
# this probe stops at the point where the server has committed to accepting
# or rejecting the broadcast, which is all we need and keeps the test cheap.
#
# The probe never fails on a rejected stream key - rejection is a perfectly
# valid outcome to assert on - so it always exits 0 when it managed to reach
# the server, and the caller decides which outcome it wanted.

import json
import re
import socket
import struct
import sys
import time

CHUNK_SIZE = 128
RTMP_VERSION = 3
HANDSHAKE_PAYLOAD_SIZE = 1536

MSG_TYPE_COMMAND_AMF0 = 20


def amf_string(value):
    encoded = value.encode("utf-8")
    return b"\x02" + struct.pack(">H", len(encoded)) + encoded


def amf_number(value):
    return b"\x00" + struct.pack(">d", float(value))


def amf_null():
    return b"\x05"


def amf_object(properties):
    out = b"\x03"
    for key, value in properties.items():
        encoded_key = key.encode("utf-8")
        out += struct.pack(">H", len(encoded_key)) + encoded_key + value
    # The object end marker: an empty key followed by the end type.
    return out + b"\x00\x00\x09"


def chunked(chunk_stream_id, message_type, message_stream_id, payload):
    """Splits a message into RTMP chunks the way a publisher would send it."""
    out = b""
    offset = 0
    first = True

    while offset < len(payload):
        piece = payload[offset:offset + CHUNK_SIZE]

        if first:
            # Type 0 chunk header: a full header, since nothing precedes it.
            out += bytes([chunk_stream_id])
            out += struct.pack(">I", 0)[1:]  # timestamp, 3 bytes
            out += struct.pack(">I", len(payload))[1:]  # message length, 3 bytes
            out += bytes([message_type])
            out += struct.pack("<I", message_stream_id)  # little-endian, per spec
            first = False
        else:
            # Type 3 chunk header: a continuation of the message above.
            out += bytes([0xC0 | chunk_stream_id])

        out += piece
        offset += len(piece)

    return out


def receive_exactly(sock, count):
    buffer = b""
    while len(buffer) < count:
        received = sock.recv(count - len(buffer))
        if not received:
            raise RuntimeError("the server closed the connection")
        buffer += received
    return buffer


def probe(host, port, stream_key, timeout=15):
    result = {
        "handshake_completed": False,
        "connect_accepted": False,
        "publish_accepted": False,
        "closed_by_server": False,
        "status_codes": [],
        "error": None,
    }

    try:
        sock = socket.create_connection((host, port), timeout=timeout)
    except OSError as error:
        result["error"] = "could not connect: {}".format(error)
        return result

    sock.settimeout(timeout)

    try:
        # C0 announces the protocol version, C1 is a block the server echoes back.
        sock.sendall(
            bytes([RTMP_VERSION]) + struct.pack(">II", 0, 0) + bytes(HANDSHAKE_PAYLOAD_SIZE - 8)
        )

        s0_and_s1 = receive_exactly(sock, 1 + HANDSHAKE_PAYLOAD_SIZE)
        if s0_and_s1[0] != RTMP_VERSION:
            result["error"] = "not an RTMP server: it answered version {}".format(s0_and_s1[0])
            return result

        receive_exactly(sock, HANDSHAKE_PAYLOAD_SIZE)  # S2
        sock.sendall(s0_and_s1[1:])  # C2 echoes S1 back
        result["handshake_completed"] = True

        connect = amf_string("connect") + amf_number(1) + amf_object({
            "app": amf_string("live"),
            "type": amf_string("nonprivate"),
            "flashVer": amf_string("FMLE/3.0 (compatible; molecule)"),
            "tcUrl": amf_string("rtmp://{}:{}/live".format(host, port)),
        })
        sock.sendall(chunked(3, MSG_TYPE_COMMAND_AMF0, 0, connect))

        create_stream = amf_string("createStream") + amf_number(2) + amf_null()
        sock.sendall(chunked(3, MSG_TYPE_COMMAND_AMF0, 0, create_stream))

        publish = (
            amf_string("publish") + amf_number(3) + amf_null()
            + amf_string(stream_key) + amf_string("live")
        )
        sock.sendall(chunked(4, MSG_TYPE_COMMAND_AMF0, 1, publish))

        # Owncast answers a good stream key with a NetStream.Publish.Start status
        # and hangs up on a bad one, so we read until one of the two happens.
        deadline = time.monotonic() + timeout
        answer = b""

        while time.monotonic() < deadline:
            try:
                received = sock.recv(4096)
            except socket.timeout:
                break

            if not received:
                result["closed_by_server"] = True
                break

            answer += received

            if b"NetStream.Publish.Start" in answer:
                break

        result["connect_accepted"] = b"NetConnection.Connect.Success" in answer
        result["publish_accepted"] = b"NetStream.Publish.Start" in answer
        # The status codes the server sent back, so that a probe which failed
        # for an unexpected reason says so rather than just reporting "no".
        result["status_codes"] = sorted(set(
            match.decode("ascii")
            for match in re.findall(rb"Net(?:Stream|Connection)\.[A-Za-z.]+", answer)
        ))
    except (OSError, RuntimeError) as error:
        result["error"] = str(error)
    finally:
        sock.close()

    return result


def main():
    if len(sys.argv) != 4:
        sys.stderr.write("Usage: rtmp-probe.py <host> <port> <stream-key>\n")
        return 2

    host, port, stream_key = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    print(json.dumps(probe(host, port, stream_key)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
