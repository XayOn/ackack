ffmpeg -i $RTSP_URL -y -c:a aac -b:a 160000 -ac 2 -s 854x480 -c:v libx264 -b:v 800000 -hls_time 10 -hls_list_size 10 -start_number 1 static/playlist.m3u8 &
export pid=$!
/opt/venv/bin/uvicorn --host="0.0.0.0" ackack:app
kill -9 $pid
