FROM ubuntu:jammy-20230308

ENV DEBIAN_FRONTEND="noninteractive"

#RUN apt-get -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update -y && apt upgrade -y && \
RUN apt-get update -y && apt upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        wget \
        curl \
        unzip \
        tree \
        libxt-dev && \
    apt-get clean && \
    apt-get autoremove && \
    rm -rf /var/lib/apt/lists/*

# FSL 6.0.5.1
RUN apt-get update -y && apt upgrade -y && \
    apt-get install -y --no-install-recommends \
        bc \
        dc \
        file \
        libfontconfig1 \
        libfreetype6 \
        libgl1-mesa-dev \
        libgl1-mesa-dri \
        libglu1-mesa-dev \
        libgomp1 \
        libice6 \
        libxcursor1 \
        libxft2 \
        libxinerama1 \
        libxrandr2 \
        libxrender1 \
        libxt6 \
        libquadmath0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Downloading FSL ..." \
    && mkdir -p /opt/fsl-6.0.5.1 \
    && curl -fsSL --retry 5 https://fsl.fmrib.ox.ac.uk/fsldownloads/fsl-6.0.5.1-centos7_64.tar.gz \
    | tar -xz -C /opt/fsl-6.0.5.1 --strip-components 1 \
    --exclude "fsl/config" \
    --exclude "fsl/data/atlases" \
    --exclude "fsl/data/first" \
    --exclude "fsl/data/mist" \
    --exclude "fsl/data/possum" \
    --exclude "fsl/data/standard/bianca" \
    --exclude "fsl/data/standard/tissuepriors" \
    --exclude "fsl/doc" \
    --exclude "fsl/etc/default_flobs.flobs" \
    --exclude "fsl/etc/fslconf" \
    --exclude "fsl/etc/js" \
    --exclude "fsl/etc/luts" \
    --exclude "fsl/etc/matlab" \
    --exclude "fsl/extras" \
    --exclude "fsl/include" \
    --exclude "fsl/python" \
    --exclude "fsl/refdoc" \
    --exclude "fsl/src" \
    --exclude "fsl/tcl" \
    --exclude "fsl/bin/FSLeyes" \
    && find /opt/fsl-6.0.5.1/bin -type f -not \( \
        -name "applywarp" -or \
        -name "bet" -or \
        -name "bet2" -or \
        -name "convert_xfm" -or \
        -name "fast" -or \
        -name "flirt" -or \
        -name "fsl_regfilt" -or \
        -name "fslhd" -or \
        -name "fslinfo" -or \
        -name "fslmaths" -or \
        -name "fslmerge" -or \
        -name "fslroi" -or \
        -name "fslsplit" -or \
        -name "fslstats" -or \
        -name "imtest" -or \
        -name "mcflirt" -or \
        -name "melodic" -or \
        -name "prelude" -or \
        -name "remove_ext" -or \
        -name "susan" -or \
        -name "topup" -or \
        -name "zeropad" \) -delete \
    && find /opt/fsl-6.0.5.1/data/standard -type f -not -name "MNI152_T1_2mm_brain.nii.gz" -delete
ENV FSLDIR="/opt/fsl-6.0.5.1" \
    PATH="/opt/fsl-6.0.5.1/bin:$PATH" \
    FSLOUTPUTTYPE="NIFTI_GZ" \
    FSLMULTIFILEQUIT="TRUE" \
    FSLLOCKDIR="" \
    FSLMACHINELIST="" \
    FSLREMOTECALL="" \
    FSLGECUDAQ="cuda.q" \
    LD_LIBRARY_PATH="/opt/fsl-6.0.5.1/lib:$LD_LIBRARY_PATH"

# AFNI latest (neurodocker build)
ENV PATH="/opt/afni-latest:$PATH" \
    AFNI_PLUGINPATH="/opt/afni-latest"
RUN apt-get update -y && apt upgrade -y && \
    apt-get install -y --no-install-recommends \
        tcsh xfonts-base libssl-dev \
        gsl-bin netpbm gnome-tweaks \
        libjpeg62 xvfb xterm \
        gedit evince eog \
        libglu1-mesa-dev libglw1-mesa \
        libxm4 build-essential \
        libcurl4-openssl-dev libxml2-dev \
        libgfortran-11-dev libgomp1 \
        gnome-terminal nautilus \
        firefox xfonts-100dpi \
        r-base-dev cmake \
        libgdal-dev libopenblas-dev \
        libnode-dev libudunits2-dev && \
    ln -s /usr/lib/x86_64-linux-gnu/libgsl.so.27 /usr/lib/x86_64-linux-gnu/libgsl.so.19 && \
    curl -O https://afni.nimh.nih.gov/pub/dist/bin/misc/@update.afni.binaries && \
    tcsh @update.afni.binaries -package linux_ubuntu_16_64 -do_extras -bindir /opt/afni-latest

# Matlab r2022b
ARG MATLAB_RELEASE=r2022b
RUN wget -q https://www.mathworks.com/mpm/glnxa64/mpm && \
    chmod +x mpm && \
    ./mpm install \
        --release=${MATLAB_RELEASE} \
        --destination=/opt/matlab \
        --products MATLAB Signal_Processing_Toolbox Image_Processing_Toolbox MATLAB_Compiler && \
    rm -f mpm /tmp/mathworks_root.log

# Compiled NORDIC
COPY ["matlab/nordic_compiled", "/opt/nordic_compiled"]

# Python 3.10 and pipenv
RUN apt-get update -y && apt upgrade -y && \
    apt-get install -y --no-install-recommends \
        python3.10 \
        python3-pip && \
    pip install pipenv

WORKDIR /opt/pynordic
COPY ["Pipfile.lock", "Pipfile", "."]
ADD ["pynordic", "/opt/pynordic/pynordic"]
RUN ["pipenv", "install", "--deploy", "--system", "--ignore-pipfile"]

ENTRYPOINT ["/opt/nordic_compiled/run_nordic_main.sh", "/opt/matlab"]
