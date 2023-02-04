## Locate services

### why?
find . -name comm | grep -v task | xargs -I {} grep -E 'RELEASE|tvservice|micomservice|lginput2|testapp' {} /dev/null
    ./1586/comm:tvservice

### Better
#### lginput2_pid
    ps aux | grep lginput2 | grep -v grep | awk '{print $2}'


## Inject
export EZPY=`python -c "import sys; print(':'.join(sys.path))"`
./ezinject/ezinject  21202 ./ezinject/libpyloader.so /usr/lib/libpython2.7.so.1.0 /usr/lib/python2.7 $EZPY magic_mapper.py
