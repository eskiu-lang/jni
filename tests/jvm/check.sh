#!/usr/bin/env bash
# Builds tests/jvm/native.esk into a shared library and runs JniTest.java on the system
# JDK against it. ESKIUC picks the compiler; JAVA_HOME (or javac/java on PATH) the JDK.
set -euo pipefail
cd "$(dirname "$0")/../.."
ESKIUC="${ESKIUC:-eskiuc}"
out="${OUT:-build/jvm}"
mkdir -p "$out"
case "$(uname -s)" in
    Darwin) lib="libjnitest.dylib" ;;
    MINGW*|MSYS*|CYGWIN*) lib="jnitest.dll" ;;
    *) lib="libjnitest.so" ;;
esac
"$ESKIUC" tests/jvm/native.esk -O2 -o "$out/$lib"
JAVAC=javac
JAVA=java
if [ -n "${JAVA_HOME:-}" ]; then
    JAVAC="$JAVA_HOME/bin/javac"
    JAVA="$JAVA_HOME/bin/java"
fi
"$JAVAC" -d "$out" tests/jvm/JniTest.java
"$JAVA" -Xcheck:jni -Djava.library.path="$out" -cp "$out" JniTest
