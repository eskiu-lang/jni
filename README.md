<p align="center">
  <img src="https://raw.githubusercontent.com/eskiu-lang/eskiu/main/assets/logo.png" alt="Eskiu, a kitten with a ball of yarn" width="140">
</p>

<h2 align="center">jni</h2>
<p align="center">Native methods for Android and the JVM, written in Eskiu.</p>
<p align="center"><sub>Part of the <a href="https://github.com/eskiu-lang">Eskiu</a> project</sub></p>
<p align="center">
  <a href="https://eskiu-lang.org">eskiu-lang.org</a> &nbsp;&middot;&nbsp;
  <a href="#modules">Modules</a> &nbsp;&middot;&nbsp;
  <a href="examples/hello/">Example</a> &nbsp;&middot;&nbsp;
  <a href="https://github.com/eskiu-lang/eskiu">The language</a>
</p>

<p align="center">
  <a href="https://github.com/eskiu-lang/jni/actions/workflows/ci.yml"><img src="https://github.com/eskiu-lang/jni/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/version-0.1.0-6448d4" alt="Version 0.1.0">
  <img src="https://img.shields.io/badge/JNI-1.6%2B-orange" alt="JNI 1.6+">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License: MIT"></a>
</p>

---

`jni` lets an Eskiu library be the native side of a Java or Kotlin class: an Android
`.so` in `jniLibs`, or a desktop library loaded with `System.loadLibrary`. There is no C
glue. A native method is an Eskiu function with the JNI name, and it calls back into the VM
through `JniEnv`.

- **Strings as UTF-8.** Java strings come in and go out as real UTF-8, converted through
  UTF-16, so emoji and other supplementary characters survive (JNI's own "modified UTF-8"
  would not round-trip them). Invalid input becomes U+FFFD.
- **Arrays, objects and fields.** Primitive arrays by region or by elements, object arrays,
  direct `ByteBuffer`s, fields of every primitive type, constructors and method calls,
  static and instance.
- **Lookups as `Result`.** A class, method or field that is not there comes back as an
  error message, and the `NoClassDefFoundError` or `NoSuchMethodError` the VM raised is
  cleared, so it does not leak out of the native method.
- **Exceptions.** Check, clear, describe, throw a new one, or take the pending one with its
  `toString()`.
- **Threads.** `JavaVm` attaches and detaches other threads and finds their env.
- **The whole table underneath.** `<jni/raw>` has every function of the JNIEnv and JavaVM
  tables, generated from `jni.h`.

```eskiu
import <string>;
import <jni>;

// package com.example.hello; class Greeter { static native String greet(String name); }
*void Java_com_example_hello_Greeter_greet(*void env, *void cls, *void name) {
    JniEnv e = jni_env(env);
    String who;
    defer String_free(&who);
    e.string(name, &who);
    String out;
    defer String_free(&out);
    String_appendf(&out, "Hello, %s, from Eskiu", who.data);
    return e.new_string(out.data);
}
```

```bash
eskiuc greeter.esk --target aarch64-linux-android24 -o app/src/main/jniLibs/arm64-v8a/libhello.so
eskiuc greeter.esk -o libhello.dylib      # a desktop JVM: .dylib, .so or .dll
```

## Modules

| Module | What it has |
|---|---|
| `<jni>` | `JniEnv`, `JavaVm`, `jni_env`, `jni_vm`, `jvalue_*` |
| `<jni/raw>` | every JNIEnv function as `jni_Name(env, ...)`, the JavaVM ones as `jvm_Name(vm, ...)`, the `JNI_*` constants, `JValue`, `JniNativeMethod` |

Objects, classes, method and field ids are `*void`, as JNI's opaque references are. A
native method's parameters follow the Java signature: `int` for `int`, `int64` for `long`,
`float`, `double`, `uint8` for `boolean`, and `*void` for every object.

## Guides

- [Using jni](docs/guide.md): `JniEnv` by area (calls, fields, arrays, exceptions,
  references), threads and `JNI_OnLoad` through `JavaVm`, and the raw tables
- [API reference](docs/api.md): every public function and type

## Platforms

| Platform | Status | Checked |
|---|---|---|
| Android arm64-v8a | runs | Android emulator (ART, API 35) |
| Android x86_64, armeabi-v7a, x86 | compiles | CI |
| Linux x86-64 (JDK 17) | runs | CI |
| macOS arm64 (JDK 17) | runs | CI |
| Windows x86-64 (JDK 17, MinGW) | runs | CI |
| iOS, WebAssembly | not available | there is no Java VM: importing `<jni>` stops with an `#error` |

## Contributing

Bug reports are welcome; please include the program, the `eskiuc --version` output and the
JVM or Android version. The tests run with:

```bash
eskiuc test                  # the wrappers against a fake JNIEnv: slots, argument passing, UTF-8
tests/jvm/check.sh           # tests/jvm/native.esk on the system JDK, under -Xcheck:jni
python3 tools/gen.py > src/raw.esk
```

`tests/jvm/JniTest.java` calls one native method per area of `JniEnv` (strings with
supplementary characters, arrays, fields, calls, constructors, exceptions, references,
direct buffers, `JNI_OnLoad` with `RegisterNatives`) and checks each result. CI runs it on
Linux, macOS and Windows; the same program, dexed with `d8`, also passes on ART.

## License

MIT. See [LICENSE](LICENSE).
