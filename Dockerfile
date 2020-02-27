FROM tpm2software/tpm2-tss

ENV CC gcc
ENV PYTHON_INTERPRETER python3.7
ENV TRAVIS_BUILD_DIR /workspace/tpm2-pkcs11

RUN apt-get update && apt-get install -y \
    libyaml-dev \
    openjdk-8-jdk-headless \
    junit4 && \
  ln -s /usr/share/java/junit4.jar /usr/share/java/junit.jar

ENV CLASSPATH /usr/share/java/junit.jar

COPY . /workspace/tpm2-pkcs11

RUN /workspace/tpm2-pkcs11/.ci/docker-prelude.sh

RUN /workspace/tpm2-pkcs11/.ci/docker.run
