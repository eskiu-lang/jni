import java.nio.ByteBuffer;
import java.util.ArrayList;

// Drives tests/jvm/native.esk on a real JVM: each native method exercises part of the
// <jni> layer and the result is checked here. Exit status 0 when everything matches.
public class JniTest {
    static class Point {
        int i;
        long l;
        float f;
        double d;
        boolean b;
        String s;
    }

    static native int add(int a, int b);
    static native String echo(String s);
    static native int sum(int[] a);
    static native double[] scale(double[] a, double k);
    static native String describe(Object o);
    static native void fill(Point p);
    static native boolean throwIt(String msg);
    static native String missing();
    static native int callStatic();
    static native Object makeList();
    static native String takeException();
    static native int version();
    static native boolean attach();
    static native int refs(Object o);
    static native int direct(ByteBuffer b);
    static native String[] strings(int n);
    static native int registered(int x);   // bound by RegisterNatives in JNI_OnLoad

    static int twice(int x) { return 2 * x; }
    static void boom() { throw new IllegalStateException("boom"); }

    static int failures = 0;
    static void check(boolean ok, String what) {
        if (!ok) { System.out.println("FAIL: " + what); failures++; }
    }

    public static void main(String[] args) {
        System.loadLibrary("jnitest");
        check(add(40, 2) == 42, "add");
        String text = "aé€😀z";
        check(echo(text).equals(text + "!"), "echo utf-8 round trip");
        check(echo("").equals("!"), "echo empty");
        check(sum(new int[] {1, 2, 3, 4}) == 10, "sum");
        double[] sc = scale(new double[] {1.5, -2.0}, 2.0);
        check(sc.length == 2 && sc[0] == 3.0 && sc[1] == -4.0, "scale");
        check(describe(Integer.valueOf(7)).equals("7"), "describe");
        Point p = new Point();
        fill(p);
        check(p.i == 7 && p.l == 0x123456789AL && p.f == 2.5f && p.d == -0.25 && p.b && "set".equals(p.s), "fields");
        try {
            throwIt("bad input");
            check(false, "throwIt did not throw");
        } catch (IllegalArgumentException e) {
            check(e.getMessage().equals("bad input"), "throwIt message");
        }
        check(missing().contains("no/Such"), "missing class error");
        check(callStatic() == 42, "callStatic");
        Object l = makeList();
        check(l instanceof ArrayList && ((ArrayList<?>) l).size() == 1 && "x".equals(((ArrayList<?>) l).get(0)), "makeList");
        check(takeException().contains("boom"), "takeException");
        check(version() >= 0x00010006, "version");
        check(attach(), "attach");
        check(refs("r") == 1, "refs");
        ByteBuffer bb = ByteBuffer.allocateDirect(16);
        check(direct(bb) == 16 && bb.get(0) == 1 && bb.get(15) == 16, "direct buffer");
        String[] st = strings(3);
        check(st.length == 3 && st[0].equals("s0") && st[2].equals("s2"), "object array");
        check(registered(20) == 21, "RegisterNatives");
        if (failures == 0) System.out.println("ok");
        System.exit(failures == 0 ? 0 : 1);
    }
}
