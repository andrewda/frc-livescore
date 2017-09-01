if [ -n "$(ls -A opencv/build)" ];
then
    # We're using a cached version of our OpenCV build
    echo "Cache found - using that."
    cd opencv;
    git init;
    git remote add origin https://github.com/opencv/opencv.git;
    git fetch origin --tags;
    git checkout tags/2.4.13;
else
    # No OpenCV cache – clone and make the files
    echo "No cache found - cloning and making files."
    rm -r opencv;
    git clone https://github.com/opencv/opencv.git;
    cd opencv;
    git fetch origin --tags;
    git checkout tags/2.4.13;
    mkdir build;
    cd build;
    cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D WITH_TBB=ON -D BUILD_NEW_PYTHON_SUPPORT=ON -D WITH_V4L=ON -D INSTALL_C_EXAMPLES=ON -D INSTALL_PYTHON_EXAMPLES=ON -D BUILD_EXAMPLES=ON -D WITH_QT=ON -D WITH_OPENGL=ON ..
    make -j8;
fi
