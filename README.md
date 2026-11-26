# dmh_conveyor

[![support level: community](https://img.shields.io/badge/support%20level-community-lightgray.svg)](http://rosindustrial.org/news/2016/10/7/better-supporting-a-growing-ros-industrial-software-platform)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![repo size](https://img.shields.io/github/repo-size/takuya-ki/dmh_conveyor)

Controller and ROS driver for [Belcon Mini III series DMH](https://www.okurayusoki.co.jp/eng/product/conveyor/lightweight/belcon_mini/) conveyor of Okura Yusoki.

- `src`: Controller that drives the conveyor via Modbus, run on the Windows machine connected to the inverter controller
- `catkin_ws/src/conveyor`: ROS driver that sends commands to the controller from an Ubuntu machine

## Requirements

- Windows 10 machine connected to the inverter controller
  - Python 3.7.3
    - pyserial==3.5
    - pymodbus==2.5.3
- Ubuntu machine to send commands (optional)
  - [Ubuntu 18.04](https://ubuntu.com/certified/laptops?q=&limit=20&vendor=Lenovo&vendor=Dell&vendor=HP&release=18.04+LTS) with [ROS Melodic](http://wiki.ros.org/melodic/Installation/Ubuntu) or [Ubuntu 20.04](https://ubuntu.com/certified/laptops?q=&limit=20&vendor=Dell&vendor=Lenovo&vendor=HP&release=20.04+LTS) with [ROS Noetic](https://wiki.ros.org/noetic/Installation/Ubuntu)
  - [Byobu](https://www.byobu.org/)

## Installation

### Windows machine

1. Install driver for [DINV U4 cable](https://www.diatrend.com/IFcable/usb/dinv-u4.php)  
   Install USB serial converter from [here](https://www.diatrend.com/download/driver.htm)  
2. Install software  
```bash
git clone https://github.com/takuya-ki/dmh_conveyor.git --depth 1 && cd dmh_conveyor && pip install -r requirements.txt
```

### Setting of inverter controller

1. Set parameters as below (For the deteil of parameters, please refer to [manual](docs/manual.pdf).)  

|  Number  |  Value  |
| ---- | ---- |
|  Pr. 160  |  0  |
|  Pr. 117  |  1  |
|  Pr. 118  |  192  |
|  Pr. 120  |  2  |
|  Pr. 122  |  9999 (65535)  |
|  Pr. 123  |  9999 (65535)  |
|  Pr. 124  |  1  |
|  Pr. 343  |  0  |
|  Pr. 502  |  0  |
|  Pr. 549  |  1  |
|  Pr. 77  |  2  |
|  Pr. 79  |  0  |
|  Pr. 551  |  9999 (65535)  |
|  Pr. 340  |  1  |

2. Set NET mode

### Ubuntu machine (ROS)

```bash
git clone https://github.com/takuya-ki/dmh_conveyor.git --depth 1 && sudo apt install byobu && cd dmh_conveyor/catkin_ws && catkin build
```

## Usage examples

### Preparations

#### 1. Check the port numer with device manager (e.g. COM3)  
<img src=image/device_manager.png width=500>  

#### 2. Connect [DINV U4 cable](https://www.diatrend.com/IFcable/usb/dinv-u4.php) between the controller for inverter and your computer.
<img src=image/connection.jpg width=200>  

### Directly commanding on a Windows 10 machine (ip address: 169.0.0.1, subnet mask: 255:255:255:0)
#### 1. Change the network connection setting of the ethernet adaptor  
<img src=image/network_windows.png width=400>  

#### 2. Execute scripts (Check no objects on the conveyor!)  
```bash
python src/demo.py --num_repeat 1 --speed high --initial_direction reverse
```
```bash
python src/check_params.py --params 160,117,118,120,122,123,124,343,502,549,77,79,551,340
```
```bash
python src/commands.py --command_from local
```

### Sending commands from an Ubuntu machine (ip address: 169.0.0.2, subnet mask: 255:255:255:0)

1. Make a local area network via a network hub by connecting between computers and the hub  
<img src=image/network_ubuntu.png width=400>  

2. Execute scripts on the Windows 10 machine as below (Check no objects on the conveyor!)  
```bash
python src/commands.py --command_from external --ip 169.0.0.1 --sockport 50007
```

#### Programmed demonstration  
3. Execute scripts on the Ubuntu machine as below (Check no objects on the conveyor!)  
```bash
python src/demo_external.py --num_repeat 1 --speed high --initial_direction reverse --ip 169.0.0.1 --sockport 50007
```

#### User's input commands  
3. Execute scripts on the Ubuntu machine as below (Check no objects on the conveyor!)  
```bash
python src/commands_external.py --ip 169.0.0.1 --sockport 50007
```

#### ROS driver  
3. Start a command server on the Ubuntu machine

```bash
roscore
```
```bash
source catkin_ws/devel/setup.bash && rosrun conveyor conveyor_driver.py _/conveyor/ip:=169.0.0.1
```
```bash
rosservice call /conveyor/set_command "<refer to below>"  
```

##### Available commands  
- nl: normal rotation with low speed  
- nm: normal rotation with middle speed  
- nh: normal rotation with high speed  
- rl: reverse rotation with low speed  
- rm: reverse rotation with middle speed  
- rh: reverse rotation with high speed  
- nXX (rYY): drive with a set of rotation and speed [Hz/100] values  
- stop: stop the motion  
- complete: finish the program  

## Author / Contributor

[Takuya Kiyokawa](https://takuya-ki.github.io/)

## License

This software is released under the MIT License, see [LICENSE](./LICENSE).
