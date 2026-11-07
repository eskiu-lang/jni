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

## Documentation

- [Modules](docs/README.md#modules)
- [Platforms](docs/README.md#platforms)
- [Contributing](docs/README.md#contributing)
- [Using jni](docs/guide.md): `JniEnv` by area (calls, fields, arrays, exceptions,
- [API reference](docs/api.md): every public function and type
- [API reference](docs/api.md): every public function and type

## Install

In an Eskiu package (Eskiu 0.14 or newer):

```bash
eskiuc add jni --git https://github.com/eskiu-lang/jni --rev v0.1.0
```

## License

MIT. See [LICENSE](LICENSE).
