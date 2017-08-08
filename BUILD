package(default_visibility = ["//visibility:public"])

py_library(
    name = "context",
    srcs = ["context.py"],
    deps = [
        "@containerregistry",
    ]
)

py_library(
    name = "builder",
    srcs = ["builder.py"],
    deps = [
        "@containerregistry",
    ]
)

py_library(
    name = "cache",
    srcs = ["cache.py"],
    deps = [
        "@containerregistry",
    ]
)

py_binary(
    name = "main",
    srcs = ["main.py"],
    deps = [
        ":context",
        ":builder",
        ":cache",
        "@containerregistry",
    ]
)
