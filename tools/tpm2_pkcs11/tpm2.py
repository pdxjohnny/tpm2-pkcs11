from __future__ import print_function

import os
import sys
from tempfile import mkstemp, NamedTemporaryFile
import uuid

from subprocess import Popen, PIPE

# from .tools import Tpm2Tools

class Tpm2(object):
    def __init__(self, tmp):
        self._tmp = tmp

    def createprimary(self, ownerauth, objauth):
        if True:
            ctx = os.path.join(self._tmp, "context.out")
            cmd = [
                'tpm2_createprimary', '-p', '%s' % objauth, '-c', ctx, '-g',
                'sha256', '-G', 'rsa'
            ]

            if ownerauth and len(ownerauth) > 0:
                cmd.extend(['-P', ownerauth])

            print(" ".join(cmd), file=open("/tmp/f", "w"))
            os.system("gdb " + cmd[0])
            # p = Popen(cmd, env=os.environ)
            # _, stderr = p.communicate()
            # if (p.wait()):
            #     raise RuntimeError("Could not execute tpm2_createprimary: %s" %
            #                        stderr)
            return ctx

        # tpm2_createprimary context arguments:
        # - p: key_auth_str = str(objauth)
        # - c: context_file = ctx
        # - g: halg = "sha256"
        # - G: alg = "rsa"
        # if ownerauth and len(ownerauth) > 0:
        #   - P: parent.auth_str = ownerauth
        # Tpm2Tools.createprimary(
        #     key_auth_str=str(objauth),
        #     context_file=ctx,
        #     halg="sha256",
        #     alg="rsa",
        #     parent_auth_str=ownerauth if ownerauth and len(ownerauth) > 0 else None,
        #     )

        with ExitStack() as stack:

            symmetric = TPMT_SYM_DEF(
                algorithm = TPM2_ALG_NULL,
                keyBits = TPMU_SYM_KEY_BITS(
                    aes = 0,
                    sm4 = 0,
                    camellia = 0,
                    sym = 0,
                    exclusiveOr = 0,
                ),
                mode = TPMU_SYM_MODE(
                    aes = 0,
                    sm4 = 0,
                    camellia = 0,
                    sym = 0,
                ),
            ),

            symmetric_ptr = stack.enter_context(symmetric.ptr())

            session = stack.enter_context(
                esys_ctx.auth_session(
                    tpmKey = ESYS_TR_NONE,
                    bind = ESYS_TR_NONE,
                    shandle1 = ESYS_TR_NONE,
                    shandle2 = ESYS_TR_NONE,
                    shandle3 = ESYS_TR_NONE,
                    nonceCaller = None,
                    sessionType = TPM2_SE_HMAC,
                    symmetric = symmetric_ptr,
                    authHash = TPM2_ALG_SHA256,
                ),
            )

    def evictcontrol(self, ownerauth, ctx):

        tr_file = os.path.join(self._tmp, "primary.handle")

        cmd = ['tpm2_evictcontrol', '-c', str(ctx), '-o', tr_file]

        if ownerauth and len(ownerauth) > 0:
            cmd.extend(['-P', ownerauth])

        p = Popen(cmd, stdout=PIPE, stderr=PIPE, env=os.environ)
        stdout, stderr = p.communicate()
        if (p.wait()):
            raise RuntimeError("Could not execute tpm2_evictcontrol: %s",
                               stderr)
        return tr_file

    def readpublic(self, handle):

        tr_file = os.path.join(self._tmp, "primary.handle")

        cmd = ['tpm2_readpublic', '-c', str(handle), '-t', tr_file]

        p = Popen(cmd, stdout=PIPE, stderr=PIPE, env=os.environ)
        stdout, stderr = p.communicate()
        if (p.wait()):
            raise RuntimeError("Could not execute tpm2_readpublic: %s",
                               stderr)
        return tr_file

    def load(self, pctx, pauth, priv, pub):

        if priv != None and not isinstance(priv, str):
            sealprivf = NamedTemporaryFile()
            sealprivf.write(priv)
            sealprivf.flush()
            priv = sealprivf.name

        if not isinstance(pub, str):
            sealpubf = NamedTemporaryFile()
            sealpubf.write(pub)
            sealpubf.flush()
            pub = sealpubf.name

        ctx = os.path.join(self._tmp, uuid.uuid4().hex + '.out')

        #tpm2_load -C $file_primary_key_ctx  -u $file_load_key_pub  -r $file_load_key_priv -n $file_load_key_name -c $file_load_key_ctx
        if priv != None:
            cmd = [
                'tpm2_load', '-C', str(pctx), '-P', pauth, '-u', pub, '-r',
                priv, '-n', '/dev/null', '-c', ctx
            ]
        else:
            cmd = ['tpm2_loadexternal', '-u', pub, '-c', ctx]

        p = Popen(cmd, stdout=PIPE, stderr=PIPE, env=os.environ)
        _, stderr = p.communicate()
        rc = p.wait()
        if rc:
            raise RuntimeError("Could not execute tpm2_load: %s", stderr)
        return ctx

    def unseal(self, ctx, auth):

        # tpm2_unseal -Q -c $file_unseal_key_ctx
        cmd = ['tpm2_unseal', '-c', ctx, '-p', auth]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, env=os.environ)
        stdout, stderr = p.communicate()
        rc = p.wait()
        if rc:
            raise RuntimeError("Could not execute tpm2_unseal: %s", stderr)
        return stdout

    def _encryptdecrypt(self, ctx, auth, data, decrypt=False):

        cmd = ['tpm2_encryptdecrypt', '-c', ctx, '-p', auth]

        if decrypt:
            cmd.extend(['-d'])

        p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE, env=os.environ)
        stdout, stderr = p.communicate(input=data)
        rc = p.wait()
        if rc:
            raise RuntimeError("Could not execute tpm2_encryptdecrypt: %s",
                               stderr)
        return stdout

    def encrypt(self, ctx, auth, data):
        return self._encryptdecrypt(ctx, auth, data)

    def decrypt(self, ctx, auth, data):
        return self._encryptdecrypt(ctx, auth, data, decrypt=True)

    def create(self,
               phandle,
               pauth,
               objauth,
               objattrs=None,
               seal=None,
               alg=None):
        # tpm2_create -Q -C context.out -g $gAlg -G $GAlg -u key.pub -r key.priv
        _, priv = mkstemp(prefix='', suffix='.priv', dir=self._tmp)
        _, pub = mkstemp(prefix='', suffix='.pub', dir=self._tmp)

        cmd = ['tpm2_create', '-C', str(phandle), '-u', pub, '-r', priv]

        if pauth and len(pauth) > 0:
            cmd.extend(['-P', '%s' % pauth])

        if objauth and len(objauth) > 0:
            cmd.extend(['-p', objauth])

        if objattrs != None:
            cmd.extend(['-a', objattrs])

        if seal != None:
            cmd.extend(['-i', '-'])

        if alg != None:
            cmd.extend(['-G', alg])

        p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE, env=os.environ)
        stdout, stderr = p.communicate(input=seal)
        rc = p.wait()
        if (rc != 0):
            os.remove(pub)
            os.remove(priv)
            raise RuntimeError("Could not execute tpm2_create: %s" %
                               str(stderr))

        return priv, pub, stdout

    def getcap(self, cap):

        # tpm2_getcap -Q -l $cap
        cmd = ['tpm2_getcap', cap]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, env=os.environ)
        stdout, stderr = p.communicate()
        rc = p.wait()
        if rc:
            raise RuntimeError("Could not execute tpm2_getcap: %s", stderr)
        return stdout

    def importkey(self,
                  phandle,
                  pauth,
                  objauth,
                  privkey,
                  objattrs=None,
                  seal=None,
                  alg=None):

        if privkey and len(privkey) > 0:
            exists = os.path.isfile(privkey)
            if not exists:
                raise RuntimeError("File '%s' path is invalid or is missing",
                                   privkey)
        else:
            sys.exit("Invalid file path")

        _, priv = mkstemp(prefix='', suffix='.priv', dir=self._tmp)
        _, pub = mkstemp(prefix='', suffix='.pub', dir=self._tmp)

        parent_path = str(phandle)
        cmd = [
            'tpm2_import', '-V', '-C', parent_path, '-i', privkey, '-u', pub,
            '-r', priv
        ]

        if pauth and len(pauth) > 0:
            cmd.extend(['-P', pauth])

        if objauth and len(objauth) > 0:
            cmd.extend(['-p', objauth])

        if objattrs != None:
            cmd.extend(['-a', objattrs])

        if seal != None:
            cmd.extend(['-i', '-'])

        if alg != None:
            cmd.extend(['-G', alg])

        p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE, env=os.environ)
        stdout, stderr = p.communicate(input=seal)
        rc = p.wait()
        if (rc != 0):
            os.remove(pub)
            os.remove(priv)
            print("command: %s" % str(" ".join(cmd)))
            raise RuntimeError("Could not execute tpm2_import: %s" %
                               str(stderr))

        return priv, pub, stdout

    def changeauth(self, pctx, objctx, oldobjauth, newobjauth):

        newpriv = os.path.join(self._tmp, uuid.uuid4().hex + '.priv')

        #tpm2_load -C $file_primary_key_ctx  -u $file_load_key_pub  -r $file_load_key_priv -n $file_load_key_name -o $file_load_key_ctx
        cmd = [
            'tpm2_changeauth',
            '-C',
            str(pctx),
            '-c',
            str(objctx),
            '-p',
            oldobjauth,
            '-r',
            newpriv,
            newobjauth,
        ]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, env=os.environ)
        _, stderr = p.communicate()
        rc = p.wait()
        if rc:
            raise RuntimeError("Could not execute tpm2_load: %s", stderr)

        return newpriv
