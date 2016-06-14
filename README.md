# EH Forwarder Bot
A (extensible) tunnel bot between chat protocols  
![Python 3.x](https://img.shields.io/badge/Python-3.x-blue.svg)

## Progress
- [ ] Structural stuff
    - [x] Inter-channel communication
    - [x] Queue processing
    - [x] Multimedia
    - [ ] Inter-channel commands
- [ ] Telgeram Master Channel
    - [x] Basic Text processing
    - [ ] Controlling slaves by command
    - [x] Chat association
    - [x] Multimedia
    - [x] Generate chat head
- [ ] Wechat Slave Channel
    - [x] Basic Text/Link processing
    - [x] Multimedia
    - [ ] Add friends (Cards & Requests)
- [ ] WhatsApp Slave Channel
- [ ] Line Slave Channel
- [ ] QQ Slave Channel
- [ ] IRC Slave Channel
- [ ] Documentations
- [ ] and more...

## Dependencies

### Non-Python dependencies
* gcc (for building `pillow`)
* libmagic (for mime type detection)
* libopus (Required by `eh-telegram-master` for voice encoding)
* ffmpeg with libopus support (Required by `eh-telegram-master` for voice encoding)
* Everything required by `pillow`, including:
    * `libjpeg, zlib, libwebp, (libtiff, libfreetype, openjpeg, tk, littlecms)`

#### Install non-Python dependencies

For more information regarding installation of Pillow, plaese visit [Pillow documentation](https://pillow.readthedocs.io/en/3.0.x/installation.html)

##### OS X / macOS

Install [Homebrew](https://brew.sh), then:

```bash
brew install libtiff libjpeg webp little-cms2
brew install libmagic
brew install ffmpeg --with-opus
```

##### Debian/Ubuntu/Mint/etc.

```bash
sudo apt-get install python3-dev python3-setuptools
sudo apt-get install libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev
sudo apt-get install libmagic-dev ffmpeg
```

### Python dependencies
Refer to `requirements.txt`.

#### To install
```bash
pip3 install -r requirements.txt
```