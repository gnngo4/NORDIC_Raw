FROM ubuntu:jammy-20230308

ENV DEBIAN_FRONTEND="noninteractive"

RUN apt-get update -y && apt upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        wget \
        unzip \
        tree \
        libxt-dev && \
    apt-get clean && \
    apt-get autoremove && \
    rm -rf /var/lib/apt/lists/*

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

# FSL 6.0.5.1 (neurodocker build)
ENV FSLDIR="/opt/fsl-6.0.5.1" \
    PATH="/opt/fsl-6.0.5.1/bin:$PATH" \
    FSLOUTPUTTYPE="NIFTI_GZ" \
    FSLMULTIFILEQUIT="TRUE" \
    FSLTCLSH="/opt/fsl-6.0.5.1/bin/fsltclsh" \
    FSLWISH="/opt/fsl-6.0.5.1/bin/fslwish" \
    FSLLOCKDIR="" \
    FSLMACHINELIST="" \
    FSLREMOTECALL="" \
    FSLGECUDAQ="cuda.q"
RUN apt-get update -qq \
    && apt-get install -y -q --no-install-recommends \
           bc \
           ca-certificates \
           curl \
           dc \
           file \
           libfontconfig1 \
           libfreetype6 \
           libgl1-mesa-dev \
           libgl1-mesa-dri \
           libglu1-mesa-dev \
           libgomp1 \
           libice6 \
           libopenblas-base \
           libxcursor1 \
           libxft2 \
           libxinerama1 \
           libxrandr2 \
           libxrender1 \
           libxt6 \
           nano \
           sudo \
           wget \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Downloading FSL ..." \
    && mkdir -p /opt/fsl-6.0.5.1 \
    && curl -fL https://fsl.fmrib.ox.ac.uk/fsldownloads/fsl-6.0.5.1-centos7_64.tar.gz \
    | tar -xz -C /opt/fsl-6.0.5.1 --strip-components 1 \
    && echo "Installing FSL conda environment ..." \
    && bash /opt/fsl-6.0.5.1/etc/fslconf/fslpython_install.sh -f /opt/fsl-6.0.5.1


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
