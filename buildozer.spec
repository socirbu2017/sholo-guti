[app]
# (str) Title of your application
title = Sholo Guti

# (str) Package name
package.name = shologuti

# (str) Package domain (needed for android/ios packaging)
package.domain = org.example

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# Specify the Python version and compatible Kivy version
requirements = python3,kivy==2.2.1

# (str) Supported orientation (landscape, sensorLandscape, portrait or sensorPortrait)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (string) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Permissions
android.permissions = INTERNET

# (int) Target Android API, must be at least = android.minapi
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# (int) Android NDK version to use
android.ndk = r28c

# (int) Android NDK API to use
android.ndk_api = 21

# (bool) Use legacy toolchain, set to False to use NDK build system
android.accept_sdk_license = True

# (str) Android logcat filters to use
# android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a,armeabi-v7a

# (bool) Enable AndroidX support
android.enable_androidx = True

# (str) Android bootstrap (sdl2 or webview)
p4a.bootstrap = sdl2

# (str) java_modules for Android
# android.add_src = 

# (list) Gradle dependencies
# android.gradle_dependencies = 

# (bool) Workaround for Android x86 issue when used with NDK r23 or x86 (skip it)
android.skip_update_check = False

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning on buildozer exit
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = .buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
# bin_dir = ./bin

# Ensure pip compatibility
android.pip_use_legacy_tool = False
