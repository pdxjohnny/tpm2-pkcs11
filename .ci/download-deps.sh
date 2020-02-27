#!/usr/bin/env bash
# SPDX-License-Identifier: BSD-2-Clause

function get_deps() {

	# For freeradius
	apt-get install -y libtalloc-dev libnl-3-dev libnl-genl-3-dev

	# The list order is important and thus we can't use the keys of the dictionary as order is not preserved.
	local github_deps=("tpm2-tss" "tpm2-abrmd" "tpm2-tools")
	declare -A local config_flags=( ["tpm2-tss"]="--disable-doxygen-doc CFLAGS=-g" ["tpm2-abrmd"]="CFLAGS=-g" ["tpm2-tools"]="--disable-hardening CFLAGS=-g")
	declare -A local versions=( ["tpm2-tss"]="2.3.0" ["tpm2-abrmd"]="2.1.0" ["tpm2-tools"]="4.0.1")

	echo "pwd starting: `pwd`"
	pushd "$1"

	for p in ${github_deps[@]}; do
		configure_flags=${config_flags[$p]}
		echo "project: $p"
		echo "conf-flags: $configure_flags"
		if [ -d "$p" ]; then
			echo "Skipping project "$p", already downloaded"
			continue
		fi
		v=${versions[$p]}
		git clone --depth 1 --branch $v "https://github.com/tpm2-software/$p.git"

		pushd "$p"

		./bootstrap
		./configure $configure_flags
		make -j$(nproc) install

		# leave the git clone directory
		popd

	done;

	# leave the download location directory
	popd
	echo "pwd done: `pwd`"

}
