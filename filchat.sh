xhost +local:root  # Autorise l'accès au serveur X11 local
docker run -it --rm -e DISPLAY=$DISPLAY -e QT_QPA_PLATFORM=xcb -v /tmp/.X11-unix:/tmp/.X11-unix filchat:latest
