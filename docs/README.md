# jni documentation

Guides and reference for jni. The [README](../README.md) has the overview.

<!-- pages -->
- [Using jni](guide.md)
- [API reference](api.md): every public function and type
<!-- /pages -->

## Modules

| Module | What it has |
|---|---|
| `<jni>` | `JniEnv`, `JavaVm`, `jni_env`, `jni_vm`, `jvalue_*` |
| `<jni/raw>` | every JNIEnv function as `jni_Name(env, ...)`, the JavaVM ones as `jvm_Name(vm, ...)`, the `JNI_*` constants, `JValue`, `JniNativeMethod` |

Objects, classes, method and field ids are `*void`, as JNI's opaque references are. A
native method's parameters follow the Java signature: `int` for `int`, `int64` for `long`,
`float`, `double`, `uint8` for `boolean`, and `*void` for every object.

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
