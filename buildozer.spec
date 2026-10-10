[app]

title = LightNet Tarkwa
package.name = lightnettarkwa
package.domain = org.lightnet
source.dir = .
source.include_exts = py
version = 1.0

requirements = python3,kivy,requests

orientation = portrait
fullscreen = 0

android.permissions = INTERNET

android.minapi = 24
android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1
