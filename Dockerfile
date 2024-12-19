FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# RUN apt-get update


#RUN apt-get update


RUN sed -i 's|http://httpredir.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org|http://archive.debian.org/debian-security|g' /etc/apt/sources.list && \
    apt-get update -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false && apt-get -y upgrade


ENV FASTANI_URL="https://github.com/ParBLiSS/FastANI/releases/download/v1.1/fastani-Linux64-v1.1.zip"

# Fetch and compile FastANI
RUN curl $FASTANI_URL -L --output /opt/fastani.zip && \
    unzip /opt/fastani.zip -d /opt && \
    rm /opt/fastani.zip && \
    ln -s /opt/fastANI /usr/local/bin/fastANI

RUN apt-get update && apt-get install -y  r-base wget vim \
    && Rscript -e 'install.packages("genoPlotR", repos="http://R-Forge.R-project.org")'





RUN pip install -U pip


# Install pip deps
COPY requirements.txt /kb/module/requirements.txt
WORKDIR /kb/module
RUN pip install -r requirements.txt




# -----------------------------------------

RUN pip install pandas
COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module
WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
