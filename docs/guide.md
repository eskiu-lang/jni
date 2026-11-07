# Using jni

`JniEnv` by area, threads through `JavaVm`, and how `<jni/raw>` reaches the JNI tables. Every function and type is also in the [API reference](api.md).

## JniEnv

| Area | Methods |
|---|---|
| VM | `version`, `vm` |
| Strings | `string(s, &out)` (UTF-8 into a `String`), `new_string(utf8)`, `string_length` |
| Classes | `find_class(name)` (a `Result`), `object_class`, `is_instance_of`, `is_same` |
| Members | `method`, `static_method`, `field`, `static_field` (each a `Result`), `register_natives` |
| Calls | `call_void`, `call_int`, `call_long`, `call_float`, `call_double`, `call_bool`, `call_object`, and `call_static_*` of each; `new_object` |
| Fields | `get_int`/`set_int`, and the same for `long`, `float`, `double`, `bool`, `object`; `get_static_int`, `set_static_int`, `get_static_object` |
| Arrays | `array_length`; `new_byte_array`, `new_int_array`, `new_long_array`, `new_float_array`, `new_double_array`, `new_object_array`; `get_bytes`/`set_bytes` (and `ints`, `longs`, `floats`, `doubles`) by region; `byte_elements`/`release_bytes` (and the others) in place; `object_at`, `set_object_at` |
| Buffers | `buffer_address`, `buffer_capacity` of a direct `ByteBuffer` |
| Exceptions | `has_exception`, `clear_exception`, `describe_exception`, `throw_new(class, message)`, `take_exception(&message)` |
| References | `new_global`, `delete_global`, `delete_local`, `push_frame`, `pop_frame` |

Calls take their arguments as a `JValue` array (`jvalue_int`, `jvalue_long`,
`jvalue_float`, `jvalue_double`, `jvalue_bool`, `jvalue_object`), or `null` for none:

```eskiu
Result<*void, string> twice = e.static_method(cls, "twice", "(I)I");
JValue[1] args = {jvalue_int(21)};
int x = e.call_static_int(cls, twice.value, &args[0]);
```

## JavaVm

`JniEnv.vm()` is the VM to keep for later; `JNI_OnLoad(*void vm, *void reserved)` receives
it too (`jni_vm(vm)`). `env(JNI_VERSION_1_6)` is the env of an attached thread,
`attach()` and `attach_daemon()` attach the calling thread and return its env, and
`detach()` detaches it.

```eskiu
int JNI_OnLoad(*void vm, *void reserved) {
    JniEnv e = jni_vm(vm).env(JNI_VERSION_1_6).value;
    *void cls = e.find_class("com/example/Engine").value;
    JniNativeMethod[1] m = {JniNativeMethod{"step", "(I)I", (*void)engine_step}};
    if (!e.register_natives(cls, &m[0], 1).ok) return JNI_ERR;
    return JNI_VERSION_1_6;
}
```

## The raw tables

A `JNIEnv*` points at a table of function pointers, and every one of them takes that same
`JNIEnv*` as its first argument. Eskiu calls a function value as `code(env, args...)`, so
each `jni_Name` builds one whose code is the table entry and whose env is the `JNIEnv*`.
`tools/gen.py` reads the table from `jni.h` (the Android NDK's, by default) and writes
`src/raw.esk`: 169 JNIEnv functions and the 5 of the JavaVM, every one but the variadic and
`va_list` forms, whose `A` counterparts take a `JValue` array. The slot order is fixed by
the JNI specification, so the same table works on ART and on every desktop JVM. Two later
additions of desktop JDKs, `GetModule` (JDK 9) and `IsVirtualThread` (JDK 21), are at the
end; call them only where the JVM has them. `uint8`, `int8`, `uint16` and `int16` arguments
are passed widened to 32 bits, as C callers do.
