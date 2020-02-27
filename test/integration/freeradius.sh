#!/usr/bin/env bash
# SPDX-License-Identifier: BSD-2-Clause

set -exo pipefail

KILL_PIDS=()
TEMP_DIRS=()

cleanup() {
  if [ "x${NO_RM_TEMP}" != "x" ]; then
    return
  fi
  for pid in ${KILL_PIDS[@]}; do
    kill -9 "${pid}"
    rm -rf "${temp_dir}"
  done
  for temp_dir in ${TEMP_DIRS[@]}; do
    rm -rf "${temp_dir}"
  done
}

# Clean up temporary directories and children on exit
trap cleanup EXIT

export TPM2_PKCS11_LOG_LEVEL=${TPM2_PKCS11_LOG_LEVEL:-"2"}

TEST_DIR="$(mktemp -d)"
TEMP_DIRS+=("${TEST_DIR}")
cd "${TEST_DIR}"


# Clone hostapd
curl -sSL 'https://w1.fi/cgit/hostap/snapshot/hostap_2_9.tar.gz' | tar xvz
cd hostap_2_9/wpa_supplicant/
# Build eapol_test
sed -e 's/#CONFIG_EAPOL_TEST=y/CONFIG_EAPOL_TEST=y/g' < defconfig > .config
make -j $(($(nproc)*4)) eapol_test

# Clone FreeRADIUS
git clone --depth=1 -b release_3_0_20 \
  https://github.com/FreeRADIUS/freeradius-server.git
cd freeradius-server
# Build FreeRADIUS
./configure
make -j $(($(nproc)*4))
# Create FreeRADIUS certs
cd ./raddb/certs
./bootstrap
make
# Copy FreeRADIUS ca cert to root of test dir
cp ./raddb/certs/ca.pem "${TEST_DIR}"


cd "${TEST_DIR}"

tpm2_clear
tpm2_ptool init
tpm2_ptool addtoken --pid=1 --sopin=mysopin --userpin=myuserpin --label=label
tpm2_ptool addkey --algorithm=rsa2048 --label=label --userpin=myuserpin
tpm2_ptool config --key tcti --value "device:/dev/tpmrm0" --label label
p11-kit list-modules
TOKEN=$(p11tool --list-token-urls | grep "token=label")
export GNUTLS_PIN=myuserpin
export GNUTLS_SO_PIN=mysopin
p11tool --login --list-all "${TOKEN}" --outfile p11tool.out

KEY=$(cat p11tool.out | grep private | awk '{ print $2 }')
SUBJ="/C=FR/ST=Radius/L=Somewhere/O=Example Inc./CN=testing/emailAddress=testing@123.com"
openssl req -new -engine pkcs11 -keyform engine -key "${KEY};pin-value=myuserpin" -subj "${SUBJ}" -out client.csr

# ssid="ATLAS"
cat <<EOF > wpa_supplicant.conf
network={
        key_mgmt=WPA-EAP
        eap=TLS
        ca_cert="./ca.pem"
        identity="testing"
        client_cert="./client.crt"
        private_key="${KEY};pin-value=myuserpin"
}
EOF

cp client.csr ./freeradius-server/raddb/certs/

cd ./freeradius-server/raddb/certs/

backup=("client.crt")
for filename in ${backup[@]}; do
  mkdir -p $filename.bak
  if [ -f $filename ]; then
    cp $filename "$filename.bak/$(date).$filename"
  fi
done

rm -f client.crt

echo 'unique_subject = no' > index.txt.attr

openssl ca -batch \
  -keyfile ./ca.key -cert ./ca.pem \
  -in ./client.csr -out ./client.crt \
  -extensions xpclient_ext -extfile ./xpextensions \
  -config ./client.cnf -passin pass:whatever

cp client.crt "${TEST_DIR}"

cd "${TEST_DIR}"

export LD_LIBRARY_PATH="${TEST_DIR}/build/lib/.libs:$LD_LIBRARY_PATH"

"${TEST_DIR}/freeradius-server/build/bin/radiusd" -X \
  -d "${TEST_DIR}/freeradius-server/raddb/" \
  -D "${TEST_DIR}/freeradius-server/share/" &
FREERADIUS_PID=$?
KILL_PIDS+=("${FREERADIUS_PID}")

eapol_test -c wpa_supplicant.conf -s testing
