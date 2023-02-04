## Setup buildroot
- sudo apt install ncurses-dev
- git clone git@github.com:openlgtv/buildroot-nc4.git
- cd buildroot-nc4
- make webos_tv_defconfig
- make
- output/host/bin/arm-webos-linux-gnueabi-gcc -o hello /tmp/hello.c

## Links
- https://github.com/openlgtv/buildroot-nc4
- http://billauer.co.il/blog/2013/05/buildroot-cross-compiler-arm/
