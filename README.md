Prepare ubuntu

    sudo apt-get install autoconf libssl-dev libxml2-dev libxslt1-dev libjpeg-dev libffi-dev libudev-dev zlib1g-dev pkg-config
    sudo apt-get install -y libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libavresample-dev libavfilter-dev
    sudo apt-get install python3-venv

Install venv

    python3.7 -m venv venv
    source /media/MySpace/home/yanoosh/Workspace/home-assistant-docker/venv/bin/activate.fish

Install home assistant

    python3 -m pip install homeassistant

