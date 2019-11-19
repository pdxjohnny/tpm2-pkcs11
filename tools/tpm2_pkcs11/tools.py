from contextlib import ExitStack

from tpm2_pytss.binding import *

CREATEPRIMARY_DEFAULT_ATTRS = \
     TPMA_OBJECT_RESTRICTED|TPMA_OBJECT_DECRYPT \
    |TPMA_OBJECT_FIXEDTPM|TPMA_OBJECT_FIXEDPARENT \
    |TPMA_OBJECT_SENSITIVEDATAORIGIN|TPMA_OBJECT_USERWITHAUTH

CREATEPRIMARY_DEFAULT_PRIMARY_KEY_ALG = "rsa2048:null:aes128cfb"

class tpm2_hierarchy_pdata_in(NamedTuple):
    hierarchy: TPMI_RH_PROVISION
    sensitive: TPM2B_SENSITIVE_CREATE
    public: TPM2B_PUBLIC
    outside_info: TPM2B_DATA
    creation_pcr: TPML_PCR_SELECTION
    object_handle: ESYS_TR

class tpm2_hierarchy_pdata_out_creation(NamedTuple):
    data: TPM2B_CREATION_DATA_PTR
    ticket: TPMT_TK_CREATION_PTR

class tpm2_hierarchy_pdata_out(NamedTuple):
    handle: ESYS_TR
    public: TPM2B_PUBLIC_PTR
    hash: TPM2B_DIGEST_PTR
    creation: tpm2_hierarchy_pdata_out_creation

class tpm2_hierarchy_pdata(NamedTuple):
    pdata_in: tpm2_hierarchy_pdata_in
    pdata_out: tpm2_hierarchy_pdata_out

class tpm_createprimary_parent(NamedTuple):
    auth_str: str
    session: tpm2_session

class tpm_createprimary_ctx(NamedTuple):
    parent: tpm_createprimary_parent

    objdata: tpm2_hierarchy_pdata
    context_file: str = None
    unique_file: str = None
    key_auth_str: str = None
    creation_data_file: str = None
    creation_ticket_file: str = None
    creation_hash_file: str = None
    outside_info_data: str = None

    alg: str = None
    halg: str = None
    attrs: str = None
    policy: str = None

class Tpm2Tools:

    # tpm2_createprimary context arguments:
    # - p: key_auth_str = str(objauth)
    # - c: context_file = ctx
    # - g: halg = "sha256"
    # - G: alg = "rsa"
    # if ownerauth and len(ownerauth) > 0:
    #   - P: parent.auth_str = ownerauth
    def createprimary(
        key_auth_str=None,
        context_file=None,
        halg="sha256",
        alg="rsa",
        parent_auth_str=None,
        ):

        ctx = tpm_createprimary_ctx(
            alg = CREATEPRIMARY_DEFAULT_PRIMARY_KEY_ALG,
            objdata = tpm2_hierarchy_pdata(
                pdata_in = tpm2_hierarchy_pdata(
                    sensitive = TPM2B_SENSITIVE_CREATE_EMPTY_INIT,
                    hierarchy = TPM2_RH_OWNER
                )
            )
        )

        with ExitStack() as stack:

            symmetric = TPMT_SYM_DEF(
                algorithm=TPM2_ALG_AES,
                keyBits=TPMU_SYM_KEY_BITS(aes=128),
                mode=TPMU_SYM_MODE(aes=TPM2_ALG_CFB),
            )

            nonceCaller = TPM2B_NONCE(
                size=20,
                buffer=[
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                ],
            )

            symmetric_ptr = stack.enter_context(symmetric.ptr())
            nonceCaller_ptr = stack.enter_context(nonceCaller.ptr())

            # Auth session
            session_auth = stack.enter_context(
                self.esys_ctx.auth_session(
                    ESYS_TR_NONE,
                    ESYS_TR_NONE,
                    ESYS_TR_NONE,
                    ESYS_TR_NONE,
                    ESYS_TR_NONE,
                    nonceCaller_ptr,
                    TPM2_SE_HMAC,
                    symmetric_ptr,
                    TPM2_ALG_SHA1,
                )
            )

            # Enc param session
            session_enc = stack.enter_context(
                self.esys_ctx.auth_session(
                    ESYS_TR_NONE,
                    ESYS_TR_NONE,
                    ESYS_TR_NONE,
                    ESYS_TR_NONE,
                    ESYS_TR_NONE,
                    nonceCaller_ptr,
                    TPM2_SE_HMAC,
                    symmetric_ptr,
                    TPM2_ALG_SHA1,
                )
            )

            # Set both ENC and DEC flags for the enc session
            sessionAttributes = (
                TPMA_SESSION_DECRYPT
                | TPMA_SESSION_ENCRYPT
                | TPMA_SESSION_CONTINUESESSION
            )

            self.esys_ctx.TRSess_SetAttributes(session_enc, sessionAttributes, 0xFF)

            auth = TPM2B_AUTH(
                size=20,
                buffer=[
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                ],
            )

            # TODO Move this into binding
            import ctypes

            attributes = ctypes.c_uint32(
                TPMA_NV_OWNERWRITE
                | TPMA_NV_AUTHWRITE
                | TPMA_NV_WRITE_STCLEAR
                | TPMA_NV_READ_STCLEAR
                | TPMA_NV_AUTHREAD
                | TPMA_NV_OWNERREAD
            ).value

            publicInfo = TPM2B_NV_PUBLIC(
                size=0,
                nvPublic=TPMS_NV_PUBLIC(
                    nvIndex=TPM2_NV_INDEX_FIRST,
                    nameAlg=TPM2_ALG_SHA1,
                    attributes=attributes,
                    authPolicy=TPM2B_DIGEST(size=0, buffer=[]),
                    dataSize=20,
                ),
            )

            auth_ptr = stack.enter_context(auth.ptr())
            publicInfo_ptr = stack.enter_context(publicInfo.ptr())

            nvHandle = stack.enter_context(
                self.esys_ctx.nv(
                    authHandle=ESYS_TR_RH_OWNER,
                    shandle1=session_auth,
                    auth=auth_ptr,
                    publicInfo=publicInfo_ptr,
                )
            )

            nv_test_data = TPM2B_MAX_NV_BUFFER(
                size=20,
                buffer=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            )
            nv_test_data_ptr = stack.enter_context(nv_test_data.ptr())

            # NV_Write cmd does not support TPMA_SESSION_ENCRYPT - the flag
            # should be auto cleared by ESYS
            r = self.esys_ctx.NV_Write(
                nvHandle,
                nvHandle,
                session_enc,
                ESYS_TR_NONE,
                ESYS_TR_NONE,
                nv_test_data_ptr,
                0,
            )

            # Verify that the same session flags are still set after the test
            sessionAttributesVerify_ptr = stack.enter_context(TPMA_SESSION_PTR())
            r = self.esys_ctx.TRSess_GetAttributes(
                session_enc, sessionAttributesVerify_ptr
            )

            if sessionAttributes != sessionAttributesVerify_ptr.value:
                raise Exception(
                    "Session flags not equal after write %x, %x"
                    % (sessionAttributes, sessionAttributesVerify_ptr.value)
                )

            data_ptr_ptr = stack.enter_context(TPM2B_MAX_NV_BUFFER_PTR_PTR())

            # NV_Read cmd does not support TPMA_SESSION_DECRYPT - the flags
            # should be auto cleared by ESYS
            r = self.esys_ctx.NV_Read(
                nvHandle,
                nvHandle,
                session_enc,
                ESYS_TR_NONE,
                ESYS_TR_NONE,
                20,
                0,
                data_ptr_ptr,
            )
            # TODO free data_ptr_ptr ?
            # free(data);

            # Verify that the same session flags are still set after the test
            self.esys_ctx.TRSess_GetAttributes(session_enc, sessionAttributesVerify_ptr)

            if sessionAttributes != sessionAttributesVerify_ptr.value:
                raise Exception(
                    "Session flags not equal after read %x, %x"
                    % (sessionAttributes, sessionAttributesVerify_ptr.value)
                )
