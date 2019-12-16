# Notes on Python Binding Integration

```log
Starting program: /usr/local/bin/tpm2_createprimary -p mypobjpin -c /tmp/tmp3ti3c9ri/context.out -g sha256
Missing separate debuginfos, use: dnf debuginfo-install glibc-2.30-5.fc31.x86_64
[Thread debugging using libthread_db enabled]
Using host libthread_db library "/lib64/libthread_db.so.1".
[New Thread 0x7ffff73ff700 (LWP 13768)]
[New Thread 0x7ffff6bfe700 (LWP 13769)]
trace:esys:src/tss2-esys/api/Esys_StartAuthSession.c:190:Esys_StartAuthSession_Async() context=0x55555559c
555ba31a,authHash=000b
trace:esys:src/tss2-esys/api/Esys_StartAuthSession.c:317:Esys_StartAuthSession_Finish() context=0x55555559
trace:esys:src/tss2-esys/esys_iutil.c:1370:iesys_check_response() No auths to verify
trace:esys:src/tss2-esys/api/Esys_CreatePrimary.c:189:Esys_CreatePrimary_Async() context=0x55555559cd20, p
Info=0x555555567584, creationPCR=0x5555555675c8
debug:esys:src/tss2-esys/esys_iutil.c:579:iesys_update_session_flags() Checking if command supports enc/de
debug:esys:src/tss2-esys/esys_iutil.c:597:iesys_update_session_flags() Session Attrs 0x1 orig 0x1
trace:esys:src/tss2-esys/api/Esys_CreatePrimary.c:299:Esys_CreatePrimary_Finish() context=0x55555559cd20,
7668, creationHash=0x555555567660, creationTicket=0x555555567670
trace:esys:src/tss2-esys/esys_iutil.c:127:cmp_TPM2B_AUTH() call
trace:esys:src/tss2-esys/esys_iutil.c:85:cmp_TPM2B_DIGEST() call
trace:esys:src/tss2-esys/esys_iutil.c:29:cmp_UINT16() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
debug:esys:src/tss2-esys/esys_iutil.c:611:iesys_restore_session_flags() Restoring session attribs
debug:esys:src/tss2-esys/esys_iutil.c:618:iesys_restore_session_flags() Orig Session 0 Attrs 0x1, altered
trace:esys:src/tss2-esys/esys_iutil.c:106:cmp_TPM2B_NAME() call
trace:esys:src/tss2-esys/esys_iutil.c:29:cmp_UINT16() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
trace:esys:src/tss2-esys/esys_iutil.c:46:cmp_BYTE() call
name-alg:
  value: sha256
  raw: 0xb
attributes:
  value: fixedtpm|fixedparent|sensitivedataorigin|userwithauth|restricted|decrypt
  raw: 0x30072
type:
  value: rsa
  raw: 0x1
exponent: 0x0
bits: 2048
scheme:
  value: null
  raw: 0x10
scheme-halg:
  value: (null)
  raw: 0x0
sym-alg:
  value: aes
  raw: 0x6
sym-mode:
  value: cfb
  raw: 0x43
sym-keybits: 128
rsa: baa705760000b1d1ea3e798a20bdea3d28d89c0f9c1b79519b40deae8a58b40b16903ddc20a07854f9b00326b7d12c044fe1c
1729d49f87d267f75de5195cedefdd2358b13e9de32133879c162daaf3b89097ee418c903dcba1efbd5a917bc4108ed9f347ad8460
d4c3b814f05563ec07ae576b215e47b055037941773b4f473c84113b9ac6aab0d4ed96264b443c19278c34d983a3632a694c78957c
trace:esys:src/tss2-esys/api/Esys_ContextSave.c:124:Esys_ContextSave_Async() context=0x55555559cd20, saveH
trace:esys:src/tss2-esys/api/Esys_ContextSave.c:194:Esys_ContextSave_Finish() context=0x55555559cd20, cont
trace:esys:src/tss2-esys/esys_mu.c:928:iesys_MU_IESYS_CONTEXT_DATA_Marshal() called: src=0x7fffffffb060 bu
trace:esys:src/tss2-esys/esys_mu.c:848:iesys_MU_IESYS_METADATA_Marshal() called: src=0x7fffffffc4ac buffer
trace:esys:src/tss2-esys/esys_mu.c:752:iesys_MU_IESYS_RESOURCE_Marshal() called: src=0x7fffffffc4b0 buffer
trace:esys:src/tss2-esys/esys_mu.c:585:iesys_MU_IESYSC_RESOURCE_TYPE_Marshal() called: src=1 buffer=0x5555
trace:esys:src/tss2-esys/esys_mu.c:668:iesys_MU_IESYS_RSRC_UNION_Marshal() called: src=0x7fffffffc500 buff
trace:esys:src/tss2-esys/api/Esys_FlushContext.c:121:Esys_FlushContext_Async() context=0x55555559cd20, flu
trace:esys:src/tss2-esys/api/Esys_FlushContext.c:187:Esys_FlushContext_Finish() context=0x55555559cd20
[Thread 0x7ffff73ff700 (LWP 13768) exited]
[Thread 0x7ffff79a6d80 (LWP 13764) exited]
[Inferior 1 (process 13764) exited normally]
```
