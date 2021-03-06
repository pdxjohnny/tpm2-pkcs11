# python stdlib dependencies
import binascii
import os
import sys
import yaml

# local imports
from .command import Command
from .command import commandlet
from .db import Db
from .utils import TemporaryDirectory
from .utils import hash_pass
from .utils import check_pin
from .utils import rand_str
from .utils import getwrapper
from .utils import load_sobject
from .utils import load_sealobject
from .utils import get_ec_params
from .utils import asn1_format_ec_point_uncompressed

from .tpm2 import Tpm2

from .pkcs11t import *


class NewKeyCommandBase(Command):
    '''
    creates a key to a token within a tpm2-pkcs11 store.
    '''

    def generate_options(self, group_parser):
        group_parser.add_argument(
            '--id',
            help='The key id. Defaults to a random 8 bytes of hex.\n',
            default=binascii.hexlify(os.urandom(8)).decode())
        pinopts = group_parser.add_mutually_exclusive_group(required=True)
        pinopts.add_argument('--sopin', help='The Administrator pin.\n'),
        pinopts.add_argument('--userpin', help='The User pin.\n'),

    # Implemented by derived class
    def new_key_create(self, sobjctx, sobjauth, objauth, tpm2, path, alg,
                       privkey):
        raise NotImplementedError('Implement: new_key')

    @staticmethod
    def new_key_init(label, sopin, userpin, db, tpm2):

        token = db.gettoken(label)

        # Get the primary object encrypted auth value and sokey information
        # to decode it. Based on the incoming pin
        is_so = sopin != None
        pin = sopin if is_so else userpin

        pobjauth = check_pin(token, pin, is_so)

        # At this point we have recovered the ACTUAL auth value for the primary object, so now we
        # can load up the seal objects
        pobj, sealctx, sealauth = load_sealobject(token, tpm2, db, pobjauth,
                                                  pin, is_so)

        # Now that the sealobject is loaded, we need to unseal the wrapping key
        # object auth or the key when the TPM doesn't support encryptdecrypt
        wrappingkeyauth = tpm2.unseal(sealctx, sealauth)

        wrapper = getwrapper(token, db, tpm2, pobjauth, wrappingkeyauth)

        sobjctx, sobjauth = load_sobject(token, db, tpm2, wrapper, pobj,
                                         pobjauth)

        #create an auth value for the tertiary object.
        objauth = hash_pass(rand_str(32))['hash']

        encobjauth = wrapper.wrap(objauth)

        return (sobjctx, sobjauth, encobjauth, objauth)

    @staticmethod
    def new_key_save(alg, keylabel, tid, label, tertiarypriv, tertiarypub,
                     tertiarypubdata, encobjauth, objauth, db, tpm2):
        token = db.gettoken(label)

        #
        # Cache the objects attributes from the public structure and other sources
        # and populate the db with the data. This allows use of the public data
        # without needed to load any objects which requires a pin to do.
        #
        y = yaml.safe_load(tertiarypubdata)

        pubattrs = None
        privattrs = None

        if alg.startswith('rsa'):
            pubattrs = [
                {
                    CKA_KEY_TYPE: CKK_RSA
                },
                {
                    CKA_CLASS: CKO_PUBLIC_KEY
                },
            ]

            privattrs = [
                {
                    CKA_KEY_TYPE: CKK_RSA
                },
                {
                    CKA_CLASS: CKO_PRIVATE_KEY
                },
                {
                    CKA_MODULUS_BITS : y['bits']
                },
            ]

            moddetails = [
                {
                    CKA_MODULUS: y['rsa']
                },
                {
                    CKA_MODULUS_BITS : y['bits']
                },
                {
                    CKA_PUBLIC_EXPONENT: 65537
                }
            ]

            pubattrs.extend(moddetails)
            privattrs.extend(moddetails)

            pubmech = [
                { CKM_RSA_X_509: "" },
                { CKM_RSA_PKCS_OAEP: {
                    "hashalg": CKM_SHA_1,
                    "mgf": CKG_MGF1_SHA1
                  }
                },
                { CKM_RSA_PKCS_OAEP: {
                    "hashalg": CKM_SHA256,
                    "mgf": CKG_MGF1_SHA256
                  }
                },
                { CKM_RSA_PKCS: "" }
            ]

            privmech = [
                { CKM_RSA_X_509: "" },
                { CKM_RSA_PKCS_OAEP: {
                    "hashalg": CKM_SHA_1,
                    "mgf": CKG_MGF1_SHA1
                  }
                },
                { CKM_RSA_PKCS_OAEP: {
                    "hashalg": CKM_SHA256,
                    "mgf": CKG_MGF1_SHA256
                  }
                },
                { CKM_RSA_PKCS: "" }
            ]
        elif alg.startswith('ecc'):

            ecparams = get_ec_params(alg)
            ecpoint = asn1_format_ec_point_uncompressed(y['x'], y['y'])

            pubattrs = [
                { CKA_KEY_TYPE: CKK_EC },
                { CKA_CLASS: CKO_PUBLIC_KEY },
                { CKA_EC_PARAMS: ecparams },
                { CKA_EC_POINT: ecpoint },
            ]

            privattrs = [
                { CKA_KEY_TYPE: CKK_EC },
                { CKA_CLASS: CKO_PRIVATE_KEY},
                { CKA_EC_PARAMS: ecparams },
                { CKA_EC_POINT: ecpoint },
            ]

            pubmech = [
                {CKM_ECDSA: ""}
            ]
            privmech = pubmech
        elif alg.startswith('aes'):
            privattrs = [
                { CKA_CLASS: CKO_SECRET_KEY},
                { CKA_KEY_TYPE: CKK_AES },
                { CKA_VALUE_LEN: y['sym-keybits'] / 8}
            ]

            privmech = [{CKM_AES_CBC: ""},]
        else:
            sys.exit('Cannot handle algorithm: "{}"'.format(alg))

        # add the id
        privattrs.append({CKA_ID: binascii.hexlify(tid.encode()).decode()})
        if pubattrs:
            pubattrs.append({CKA_ID: binascii.hexlify(tid.encode()).decode()})

        privattrs.append({CKA_TOKEN: True })
        privattrs.append({CKA_SENSITIVE: True })
        privattrs.append({CKA_ALWAYS_SENSITIVE: True })
        privattrs.append({CKA_EXTRACTABLE: False })
        privattrs.append({CKA_NEVER_EXTRACTABLE: True })

        # Add keylabel for ALL objects if set
        if keylabel is not None:
            privattrs.append({CKA_LABEL: binascii.hexlify(keylabel.encode()).decode()})
            if pubattrs:
                pubattrs.append({CKA_LABEL: binascii.hexlify(keylabel.encode()).decode()})

        # Now get the secondary object from db
        sobj = db.getsecondary(token['id'])

        # Store private to database
        privrowid = db.addtertiary(sobj['id'], tertiarypriv, tertiarypub,
                               encobjauth, privmech, privattrs)

        # if it's asymmetric, add a public object too
        if pubattrs:
            pubrowid = db.addtertiary(sobj['id'], None, tertiarypub,
                               encobjauth, pubmech, pubattrs)


        # if the keylabel is not set, use the tertiary object tid as the keylabel
        # Normally we would use a transaction to make this atomic, but Pythons
        # sqlite3 transaction handling is quite odd. So when the keylabel is None, just insert
        # into the db without that attribute, retrieve the primary key, and then issue an
        # update. A possible race exists if someone is looking for the key by label between
        # these operations.
        # See:
        #   - https://stackoverflow.com/questions/107005/predict-next-auto-inserted-row-tid-sqlite
        if keylabel is None:
            keylabel = str(privrowid)
            privattrs.append({CKA_LABEL: binascii.hexlify(keylabel.encode()).decode()})
            db.updatetertiaryattrs(privrowid, privattrs)
            if pubattrs:
                pubattrs.append({CKA_LABEL: binascii.hexlify(keylabel.encode()).decode()})
                db.updatetertiaryattrs(pubrowid, pubattrs)

        db.commit()

        return keylabel

    def __call__(self, args):
        path = args['path']

        with Db(path) as db:

            with TemporaryDirectory() as d:
                tpm2 = Tpm2(d)

                label = args['label']
                sopin = args['sopin']
                userpin = args['userpin']
                alg = args['algorithm']
                key_label = args['key_label']
                tid = args['id']

                privkey = None
                try:
                    privkey = args['privkey']
                except:
                    privkey = None
                else:
                    path = args['path']

                path = args['path']

                sobjctx, sobjauth, encobjauth, objauth = NewKeyCommandBase.new_key_init(
                    label, sopin, userpin, db, tpm2)

                tertiarypriv, tertiarypub, tertiarypubdata = self.new_key_create(
                    sobjctx, sobjauth, objauth, tpm2, path, alg, privkey)

                final_key_label = NewKeyCommandBase.new_key_save(
                    alg, key_label, tid, label, tertiarypriv, tertiarypub,
                    tertiarypubdata, encobjauth, objauth, db, tpm2)

                return final_key_label


@commandlet("import")
class ImportCommand(NewKeyCommandBase):
    '''
    Imports a rsa key to a token within a tpm2-pkcs11 store.
    '''

    # adhere to an interface
    # pylint: disable=no-self-use
    def generate_options(self, group_parser):
        super(ImportCommand, self).generate_options(group_parser)
        group_parser.add_argument(
            '--privkey',
            help='Full path of the private key to be imported.\n',
            required=True)
        group_parser.add_argument(
            '--label',
            help='The tokens label to import the key too.\n',
            required=True)
        group_parser.add_argument(
            '--key-label',
            help='The label of the key imported. Defaults to an integer value.\n'
        )
        group_parser.add_argument(
            '--algorithm',
            help='The type of the key.\n',
            choices=['rsa'],
            required=True)

    # Imports a new key
    def new_key_create(self, sobjctx, sobjauth, objauth, tpm2, path, alg,
                       privkey):
        if alg != 'rsa':
            sys.exit('Unknown algorithm or algorithm not supported, got "%s"' %
                     alg)

        if privkey == None:
            sys.exit("Invalid private key path")

        tertiarypriv, tertiarypub, tertiarypubdata = tpm2.importkey(
            sobjctx, sobjauth, objauth, privkey=privkey, alg=alg)

        return (tertiarypriv, tertiarypub, tertiarypubdata)

    def __call__(self, args):
        keylabel = super(self.__class__, self).__call__(args)
        print('Imported key as label: "{keylabel}"'.format(keylabel=keylabel))


@commandlet("addkey")
class AddKeyCommand(NewKeyCommandBase):
    '''
    Adds a key to a token within a tpm2-pkcs11 store.
    '''

    # adhere to an interface
    # pylint: disable=no-self-use
    def generate_options(self, group_parser):
        super(self.__class__, self).generate_options(group_parser)
        group_parser.add_argument(
            '--label',
            help='The tokens label to add a key too.\n',
            required=True)
        group_parser.add_argument(
            '--algorithm',
            help='The type of the key.\n',
            choices=[
                'rsa1024', 'rsa2048', 'aes128', 'aes256', 'ecc224', 'ecc256',
                'ecc384', 'ecc521'
            ],
            required=True)
        group_parser.add_argument(
            '--key-label',
            help='The key label to identify the key. Defaults to an integer value.\n'
        )

    # Creates a new key
    def new_key_create(self, sobjctx, sobjauth, objauth, tpm2, path, alg,
                       privkey):

        tertiarypriv, tertiarypub, tertiarypubdata = tpm2.create(
            sobjctx, sobjauth, objauth, alg=alg)

        return (tertiarypriv, tertiarypub, tertiarypubdata)

    def __call__(self, args):
        keylabel = super(self.__class__, self).__call__(args)
        print('Added key as label: "{keylabel}"'.format(keylabel=keylabel))
