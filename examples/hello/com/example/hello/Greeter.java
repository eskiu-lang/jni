package com.example.hello;

public class Greeter {
    static { System.loadLibrary("hello"); }

    public static native String greet(String name);

    public static void main(String[] args) {
        System.out.println(greet(args.length > 0 ? args[0] : "world"));
    }
}
