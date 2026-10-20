#!/usr/bin/env python3
"""Generates src/raw.esk from a jni.h (the Android NDK's, by default).

    python3 tools/gen.py [path/to/jni.h] > src/raw.esk

Every function of the JNIEnv table (JNINativeInterface) that is neither variadic nor
takes a va_list becomes `jni_<Name>(*void env, ...)`, and every function of the JavaVM
table (JNIInvokeInterface) `jvm_<Name>(*void vm, ...)`. Each is a call through an Eskiu
fn value whose env slot is the JNIEnv (or JavaVM) pointer: JNI passes that pointer as the
first argument of every function, which is exactly where a closure call puts its env.

The table order is fixed by the JNI specification, so the slots read from the NDK header
hold on every JVM. Two functions desktop JDKs added after the last one Android has,
GetModule (JDK 9) and IsVirtualThread (JDK 21), are appended by hand: call them only on
a JVM that has them.
"""
import glob
import os
import re
import sys

PRIM = {
    "void": "void", "jint": "int", "jlong": "int64", "jboolean": "uint8", "jbyte": "int8",
    "jchar": "uint16", "jshort": "int16", "jfloat": "float", "jdouble": "double",
    "jsize": "int", "jobjectRefType": "int",
}
# Narrow integers travel as int in the fn type: the caller then widens them as every C
# ABI expects (Apple arm64 has the caller extend), and the wrapper keeps the JNI type.
NARROW = {"uint8", "int8", "uint16", "int16"}
OBJ = {"jobject", "jclass", "jstring", "jthrowable", "jarray", "jobjectArray",
       "jbooleanArray", "jbyteArray", "jcharArray", "jshortArray", "jintArray",
       "jlongArray", "jfloatArray", "jdoubleArray", "jweak", "jmethodID", "jfieldID"}


def esk_type(c):
    c = c.replace("const ", "").strip()
    stars = c.count("*")
    base = c.replace("*", "").strip()
    if base == "char" and stars == 1:
        return "string"
    if base == "jvalue" and stars == 1:
        return "*JValue"
    if base == "JNINativeMethod" and stars == 1:
        return "*JniNativeMethod"
    if base in ("JNIEnv", "JavaVM", "void") and stars >= 1:
        return "*" * (stars - 1) + "*void"
    if base in OBJ:
        return "*" * stars + "*void"
    if base in PRIM:
        return "*" * stars + PRIM[base]
    raise SystemExit("unmapped C type: " + c)


def table(src, name):
    m = re.search(r"struct %s \{(.*?)\n\};" % name, src, re.S)
    body = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S)
    out = []
    for decl in body.split(";"):
        decl = " ".join(decl.split())
        if not decl:
            continue
        r = re.match(r"void\s*\*\s*(reserved\d)$", decl)
        if r:
            out.append((r.group(1), None, None))
            continue
        f = re.match(r"(.+?)\s*\(\s*\*\s*(\w+)\s*\)\s*\((.*)\)$", decl)
        if not f:
            raise SystemExit("cannot parse: " + decl)
        ret, fname, args = f.groups()
        args = [a.strip() for a in args.split(",")]
        out.append((fname, ret.strip(), args))
    return out


def emit(entries, prefix, self_name, extra=()):
    lines = []
    sigs = {}
    funcs = []
    slots = []
    for i, (fname, ret, args) in enumerate(list(entries) + list(extra)):
        if ret is None:
            continue
        slots.append("const int %s_SLOT_%s = %d;" % (prefix.upper(), fname, i))
        if "..." in args or any("va_list" in a for a in args):
            continue
        params = [esk_type(a) for a in args[1:]]
        rt = esk_type(ret)
        fn_params = ["int" if p in NARROW else p for p in params]
        sig = "fn(%s)->%s" % (", ".join(fn_params), rt)
        if sig not in sigs:
            sigs[sig] = "_JniF%d" % len(sigs)
        names = ["a%d" % k for k in range(len(params))]
        decl = ", ".join(["*void %s" % self_name] + ["%s %s" % (t, n) for t, n in zip(params, names)])
        call = ", ".join(("(int)%s" % n) if t in NARROW else n for t, n in zip(params, names))
        body = [
            "%s %s_%s(%s) {" % (rt, prefix, fname, decl),
            "    _JniRaw r = _jni_slot(%s, %d);" % (self_name, i),
            "    %s f = ((*%s)&r).f;" % (sig, sigs[sig]),
            ("    f(%s);" % call) if rt == "void" else ("    return f(%s);" % call),
            "}",
        ]
        funcs.append("\n".join(body))
    return slots, sigs, funcs


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob(os.path.expanduser(
        "~/Library/Android/sdk/ndk/*/toolchains/llvm/prebuilt/*/sysroot/usr/include/jni.h")))[-1]
    src = open(path).read()
    env = table(src, "JNINativeInterface")
    vm = table(src, "JNIInvokeInterface")
    extra_env = [("GetModule", "jobject", ["JNIEnv*", "jclass"]),
                 ("IsVirtualThread", "jboolean", ["JNIEnv*", "jobject"])]
    s1, sig1, f1 = emit(env, "jni", "env", extra_env)
    s2, sig2, f2 = emit(vm, "jvm", "vm")
    sigs = dict(sig1)
    for k in sig2:
        if k not in sigs:
            sigs[k] = "_JniF%d" % len(sigs)
    # emit() numbered the JavaVM signatures on their own; renumber them into one table.
    f2 = [re.sub(r"\(\*_JniF\d+\)&r\)\.f;", lambda m, s=None: m.group(0), f) for f in f2]
    fixed = []
    for f in f2:
        sig = re.search(r"    (fn\(.*?\)->\S+) f = ", f).group(1)
        fixed.append(re.sub(r"\(\*_JniF\d+\)", "(*%s)" % sigs[sig], f))
    print("// GENERATED by tools/gen.py from %s; do not edit." % os.path.basename(path))
    print("//")
    print("// The JNI function tables as Eskiu functions. Each jni_<Name>(env, ...) calls slot")
    print("// JNI_SLOT_<Name> of the JNIEnv table through a fn value whose env slot is the JNIEnv")
    print("// itself; jvm_<Name>(vm, ...) does the same with the JavaVM table. Variadic and")
    print("// va_list functions are left out: use the A forms, which take a *JValue array.")
    print()
    print("#if defined(__wasm__) || defined(TARGET_OS_IPHONE)")
    print('#error "jni: there is no Java VM on this platform (Android and desktop JVMs only)"')
    print("#endif")
    print()
    print("const int JNI_FALSE = 0;\nconst int JNI_TRUE = 1;")
    print("const int JNI_VERSION_1_1 = 0x00010001;\nconst int JNI_VERSION_1_2 = 0x00010002;")
    print("const int JNI_VERSION_1_4 = 0x00010004;\nconst int JNI_VERSION_1_6 = 0x00010006;")
    print("const int JNI_VERSION_1_8 = 0x00010008;   // desktop JDK 8 and later")
    print("const int JNI_OK = 0;\nconst int JNI_ERR = -1;\nconst int JNI_EDETACHED = -2;")
    print("const int JNI_EVERSION = -3;\nconst int JNI_ENOMEM = -4;\nconst int JNI_EEXIST = -5;")
    print("const int JNI_EINVAL = -6;\nconst int JNI_COMMIT = 1;\nconst int JNI_ABORT = 2;")
    print("const int JNI_INVALID_REF_TYPE = 0;\nconst int JNI_LOCAL_REF_TYPE = 1;")
    print("const int JNI_GLOBAL_REF_TYPE = 2;\nconst int JNI_WEAK_GLOBAL_REF_TYPE = 3;")
    print()
    print("// jvalue: one argument of a Call...A / NewObjectA call, 8 bytes like the C union.")
    print("struct JValue {\n    int64 bits;\n}")
    print()
    print("// JNINativeMethod, for jni_RegisterNatives.")
    print("struct JniNativeMethod {\n    string name;\n    string signature;\n    *void fnPtr;\n}")
    print()
    print("struct _JniRaw {\n    *void code;\n    *void env;\n}")
    print()
    print("// Slot i of the function table that a JNIEnv* or JavaVM* points to, as a fn value")
    print("// whose env is that pointer.")
    print("_JniRaw _jni_slot(*void self, int i) {")
    print("    ***void t = (***void)self;")
    print("    return _JniRaw{(*t)[i], self};")
    print("}")
    print()
    for k, v in sigs.items():
        print("struct %s { %s f; }" % (v, k))
    print()
    for s in s1 + s2:
        print(s)
    print()
    print("\n\n".join(f1 + fixed))


main()
