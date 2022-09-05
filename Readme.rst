.. figure:: ./docs/ackack.jpg
   :width: 200px

   (Creative Commons Attribution-Noncommercial-No Derivative Works 3.0 License, Author Wonder Waffle https://www.deviantart.com/wonder-waffle/art/ACK-ACK-Mars-Attacks-359710975 )



|pypi| |release| |downloads| |python_versions| |pypi_versions| |actions|

.. |pypi| image:: https://img.shields.io/pypi/l/ackack
.. |release| image:: https://img.shields.io/librariesio/release/pypi/ackack
.. |downloads| image:: https://img.shields.io/pypi/dm/ackack
.. |python_versions| image:: https://img.shields.io/pypi/pyversions/ackack
.. |pypi_versions| image:: https://img.shields.io/pypi/v/ackack
.. |actions| image:: https://github.com/XayOn/ackack/workflows/build.yml/badge.svg 


**Have fun with your vaccuum robot!**

AckAck is a simple control API to manually controll weback vacuum robots.
Paired with its web interface, and a RTPS (in my case, I'm using an old yi ants
camera with `yi-hack <https://github.com/fritz-smh/yi-hack>`_)

It was born to monitor my cats when I'm on vacation :wink:

.. image:: ./docs/screenshot.png


Keys
----

Use your arrow keys to move the robot left, right, go front or turn backwards.
Enter will start cleaning and backspace will stop.


Environment variables
---------------------

You'll need to setup your weback username and password.
Usually, this will be your phone + the password you use on the control app.
Besides that, only RTSP_URL is required.


===============  =========================================
KEY               Description
===============  =========================================
ACKACK_RTSP_URI  Yi camera's RTSP stream URL 
ACKACK_USERNAME  Your weback's username (phone number)
ACKACK_PASS      Your weback's password
BASE             Base URL, for reverse proxies
FORGETFUL        Use forgetful to recognize faces/objects
FORGETFUL_URL    Forgetful's full face search URL
===============  =========================================


For example:

.. code:: bash 

    ACKACK_RTSP_URI=rtsp://192.168.1.121:554/ch0_1.h264 \
    ACKACK_USER="+34-123123123" \
    ACKACK_PASS="yourpass" \
    ACKACK_FORGETFUL=true \
    ACKACK_FORGETFUL_URI=http://localhost:8001/faces/search/ \
    poetry run uvicorn --host="0.0.0.0" ackack:app --port=8081


Installation
------------

Docker
++++++

With docker, just setup the specified env vars and launch the image.
You can use the following docker-compose.yml example.
Setting base_url is useful in reverse proxy scenarios (like traefik).

.. code:: yaml

    version: "3.3"
    services:
      ackack:
        image: XayOn/ackack
        restart: unless-stopped
        ports:
          - 8080:8080
        environment:
          ACKACK_RTSP_URI: http://192.168.1...
          ACKACK_USERNAME: +33-123123123
          ACKACK_PASS: yourpassword 
          ACKACK_FORGETFUL=true
          ACKACK_FORGETFUL_URI=http://localhost:8001/faces/search/
          BASE: /ackack


Manual setup
++++++++++++

Install the project, set your environment variables, run uvicorn.
Requires ffmpeg. Check your distro's instructions on how to install ffmpeg.
Docker image comes with ffmpeg built-in

.. code:: bash

   pip install ackack
   ACKACK_USERNAME="+34-XXXX" ACKACK_PASS="XXXX" ACKACK_RTSP_URI=XXX poetry run uvicorn ackack:app


How does it work? / Acknowledgments
-------------------------------------

Ackack works as a standalone web interface to control your WeBack robot.

Its weback interface is based on agustin-e's work on homeassistant
integration: https://github.com/agustin-e/weback-home-assistant-component

Finally it uses ffmpeg to re-encode into a hls-compatible stream the yi
camera's RTSP, and serves a websocket-based interface to put everything
togheter..
