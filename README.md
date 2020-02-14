# Heating radiator

Components are used to manage water distribution via electric thermal actuator to heating radiator.

Actuator has one very bad characteristic: it starts working with delay and the same situation is with stopping. Solution is periodic hit of electric current: 30s on and 4m pause and again until temperature will be as expected.

Configuration allows to set minimum work time which is required to start working a head and maximum time of work to not overheat a device. Both attributes are limited by cycle duration.

## Configuration

### Minimal

      small_room:
        temperature:
          sensors: sensor.ard_1_temperature_1
          target: 22.5
        turn_on:
          service: switch.turn_on
          entity_id: switch.ard_1_switcher_0
        turn_off:
          service: switch.turn_off
          entity_id: switch.ard_1_switcher_0

### Extended

      small_room:
        temperature:
          sensors: sensor.ard_1_temperature_1
          target: 22.5
          minimum: 20
          max_deviation: 2
        work_interval:
          duration: "00:05:00"
          minimum: "00:00:10"
          maximum: "00:01:00"
        presence: binary_sensor.occupancy_small_room
        turn_on:
          service: switch.turn_on
          entity_id: switch.ard_1_switcher_0
        turn_off:
          service: switch.turn_off
          entity_id: switch.ard_1_switcher_0

## Development

Component development requires libraries for editor and place where new features can be run.

### Libraries

Prepare ubuntu

    sudo apt-get install autoconf libssl-dev libxml2-dev libxslt1-dev libjpeg-dev libffi-dev libudev-dev zlib1g-dev pkg-config
    sudo apt-get install -y libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libavresample-dev libavfilter-dev
    sudo apt-get install python3-venv

Install venv - virtual environments for project and place for home assistant libs

    python3.7 -m venv venv
    source venv/bin/activate.fish

Install home assistant libraries - local installation not need special permission and use `sudo`

    python3 -m pip install homeassistant
    
    
### Docker
    
Install home assistant in docker (https://www.home-assistant.io/docs/installation/docker/)

    docker run --init -d --name="home-assistant" -v /PATH_TO_YOUR_CONFIG:/config --net=host homeassistant/home-assistant:stable



