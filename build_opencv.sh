if [ -n "$(ls -A opencv/build)" ];
then
    # We're using a cached version of our OpenCV build
    echo "Cache found - using that."
    cd opencv
    git init
    git remote add origin https://github.com/opencv/opencv.git
    git fetch origin --tags
    git checkout 3.1.0
    cd ../opencv_contrib
    git init
    git remote add origin https://github.com/opencv/opencv_contrib.git
    git fetch origin --tags
    git checkout 3.1.0
else
    # No OpenCV cache – clone and make the files
    echo "No cache found - cloning and making files."
    rm -r opencv
    git clone https://github.com/opencv/opencv_contrib.git
    cd opencv_contrib
    git checkout 3.1.0
    cd ..
    git clone https://github.com/opencv/opencv.git
    cd opencv
    git fetch origin --tags
    git checkout 3.1.0
    mkdir build
    cd build
    cmake -D CMAKE_BUILD_TYPE=RELEASE \
          -D CMAKE_INSTALL_PREFIX=/usr/local \
          -D WITH_TBB=ON \
          -D PYTHON3_EXECUTABLE=/home/travis/virtualenv/python3.6.3/bin/python \
          -D PYTHON_INCLUDE_DIR=/home/travis/virtualenv/python3.6.3/include/python3.6m \
          -D BUILD_NEW_PYTHON_SUPPORT=ON \
          -D BUILD_OPENCV_PYTHON3=ON \
          -D WITH_V4L=ON \
          -D INSTALL_C_EXAMPLES=OFF \
          -D INSTALL_PYTHON_EXAMPLES=ON \
          -D BUILD_EXAMPLES=ON \
          -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules \
          -D WITH_QT=ON \
          -D WITH_OPENGL=ON ..
    make -j8
fi
