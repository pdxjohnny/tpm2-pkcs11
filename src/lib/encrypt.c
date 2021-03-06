/* SPDX-License-Identifier: BSD-2 */
/*
 * Copyright (c) 2018, Intel Corporation
 * All rights reserved.
 */
#include "checks.h"
#include "encrypt.h"
#include "session.h"
#include "session_ctx.h"
#include "token.h"
#include "tpm.h"

typedef CK_RV (*tpm_op)(tpm_encrypt_data *tpm_enc_data, CK_BYTE_PTR in, CK_ULONG inlen, CK_BYTE_PTR out, CK_ULONG_PTR outlen);

encrypt_op_data *encrypt_op_data_new(void) {

    return (encrypt_op_data *)calloc(1, sizeof(encrypt_op_data));
}

void encrypt_op_data_free(encrypt_op_data **opdata) {

    if (opdata) {
        tpm_encrypt_data_free((*opdata)->tpm_enc_data);
        free(*opdata);
        *opdata = NULL;
    }
}

static CK_RV common_init_op (session_ctx *ctx, encrypt_op_data *supplied_opdata, operation op, CK_MECHANISM *mechanism, CK_OBJECT_HANDLE key) {

    check_pointer(mechanism);

    token *tok = session_ctx_get_token(ctx);
    assert(tok);

    if (!supplied_opdata) {
        bool is_active = session_ctx_opdata_is_active(ctx);
        if (is_active) {
            return CKR_OPERATION_ACTIVE;
        }
    }

    tobject *tobj;
    CK_RV rv = token_load_object(tok, key, &tobj);
    if (rv != CKR_OK) {
        return rv;
    }

    rv = object_mech_is_supported(tobj, mechanism);
    if (rv != CKR_OK) {
        tobject_user_decrement(tobj);
        return rv;
    }

    encrypt_op_data *opdata;
    if (!supplied_opdata) {
        opdata = encrypt_op_data_new();
        if (!opdata) {
            tobject_user_decrement(tobj);
            return CKR_HOST_MEMORY;
        }
    } else {
        opdata = supplied_opdata;
    }

    opdata->tobj = tobj;

    rv = tpm_encrypt_data_init(tok->tctx, tobj->handle, tobj->unsealed_auth, mechanism, &opdata->tpm_enc_data);
    if (rv != CKR_OK) {
        tobject_user_decrement(tobj);
        encrypt_op_data_free(&opdata);
        return rv;
    }

    if (!supplied_opdata) {
        session_ctx_opdata_set(ctx, op, opdata, (opdata_free_fn)encrypt_op_data_free);
    }

    return CKR_OK;
}

static CK_RV common_update_op (session_ctx *ctx, encrypt_op_data *supplied_opdata, operation op,
        CK_BYTE_PTR part, CK_ULONG part_len,
        CK_BYTE_PTR encrypted_part, CK_ULONG_PTR encrypted_part_len) {

    check_pointer(part);
    check_pointer(encrypted_part_len);

    CK_RV rv = CKR_GENERAL_ERROR;

    twist input = twistbin_new(part, part_len);
    if (!input) {
        return CKR_HOST_MEMORY;
    }

    twist output = NULL;

    encrypt_op_data *opdata = NULL;
    if (!supplied_opdata) {
        rv = session_ctx_opdata_get(ctx, op, &opdata);
        if (rv != CKR_OK) {
            goto out;
        }
    } else {
        opdata = supplied_opdata;
    }

    tpm_op fop;
    switch(op) {
    case operation_encrypt:
        fop = tpm_encrypt;
        break;
    case operation_decrypt:
        fop = tpm_decrypt;
        break;
    default:
        return CKR_GENERAL_ERROR;
    }

    rv = fop(opdata->tpm_enc_data, part, part_len,
            encrypted_part, encrypted_part_len);
    if (rv != CKR_OK) {
        goto out;
    }

    rv = CKR_OK;

out:
    twist_free(input);
    twist_free(output);

    return rv;
}

static CK_RV common_final_op(session_ctx *ctx, encrypt_op_data *supplied_opdata, operation op,
        CK_BYTE_PTR last_part, CK_ULONG_PTR last_part_len) {

    /*
     * We have no use for these.
     */
    UNUSED(last_part);
    UNUSED(last_part_len);

    CK_RV rv = CKR_GENERAL_ERROR;

    /* nothing to do if opdata is supplied externally */
    if (supplied_opdata) {
        /* do not goto out, no opdata to clear */
        return CKR_OK;
    }

    encrypt_op_data *opdata = NULL;
    rv = session_ctx_opdata_get(ctx, op, &opdata);
    if (rv != CKR_OK) {
        return rv;
    }

    assert(opdata->tobj);
    rv = tobject_user_decrement(opdata->tobj);
    if (rv != CKR_OK) {
        return rv;
    }

    session_ctx_opdata_clear(ctx);

    return CKR_OK;
}

CK_RV encrypt_init_op (session_ctx *ctx, encrypt_op_data *supplied_opdata, CK_MECHANISM *mechanism, CK_OBJECT_HANDLE key) {

    return common_init_op(ctx, supplied_opdata, operation_encrypt, mechanism, key);
}

CK_RV decrypt_init_op (session_ctx *ctx, encrypt_op_data *supplied_opdata, CK_MECHANISM *mechanism, CK_OBJECT_HANDLE key) {

    return common_init_op(ctx, supplied_opdata, operation_decrypt, mechanism, key);
}

CK_RV encrypt_update_op (session_ctx *ctx, encrypt_op_data *supplied_opdata, CK_BYTE_PTR part, CK_ULONG part_len, CK_BYTE_PTR encrypted_part, CK_ULONG_PTR encrypted_part_len) {

    return common_update_op(ctx, supplied_opdata, operation_encrypt, part, part_len, encrypted_part, encrypted_part_len);
}

CK_RV decrypt_update_op (session_ctx *ctx, encrypt_op_data *supplied_opdata, CK_BYTE_PTR part, CK_ULONG part_len, CK_BYTE_PTR encrypted_part, CK_ULONG_PTR encrypted_part_len) {

    return common_update_op(ctx, supplied_opdata, operation_decrypt, part, part_len, encrypted_part, encrypted_part_len);
}

CK_RV encrypt_final_op (session_ctx *ctx, encrypt_op_data *supplied_opdata, CK_BYTE_PTR last_encrypted_part, CK_ULONG_PTR last_encrypted_part_len) {

    return common_final_op(ctx, supplied_opdata, operation_encrypt, last_encrypted_part, last_encrypted_part_len);
}

CK_RV decrypt_final_op (session_ctx *ctx, encrypt_op_data *supplied_opdata, CK_BYTE_PTR last_part, CK_ULONG_PTR last_part_len) {

    return common_final_op(ctx, supplied_opdata, operation_decrypt, last_part, last_part_len);
}

CK_RV decrypt_oneshot_op (session_ctx *ctx, encrypt_op_data *supplied_opdata, CK_BYTE_PTR encrypted_data, CK_ULONG encrypted_data_len, CK_BYTE_PTR data, CK_ULONG_PTR data_len) {

    CK_RV rv = decrypt_update_op(ctx, supplied_opdata, encrypted_data, encrypted_data_len,
            data, data_len);
    if (rv != CKR_OK || !data) {
        return rv;
    }

    return decrypt_final_op(ctx, supplied_opdata, NULL, NULL);
}

CK_RV encrypt_oneshot_op (session_ctx *ctx, encrypt_op_data *supplied_opdata, CK_BYTE_PTR data, CK_ULONG data_len, CK_BYTE_PTR encrypted_data, CK_ULONG_PTR encrypted_data_len) {

    CK_RV rv = encrypt_update_op (ctx, supplied_opdata, data, data_len, encrypted_data, encrypted_data_len);
    if (rv != CKR_OK || !encrypted_data) {
        return rv;
    }

    return encrypt_final_op(ctx, supplied_opdata, NULL, NULL);
}
