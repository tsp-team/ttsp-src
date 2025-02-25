# Default window properties...
window-title Panda
win-origin -1 -1
win-size 640 480
#win-fixed-size 1
load-display pandagl
aux-display pandagl

#clock-mode limited
#clock-frame-rate 10

# Logging...
notify-level info
#notify-level-egg2pg info
#notift-level-bspfile info
#notify-level-pgraph info
#notify-level-loader info
#notify-level-gobj info
#notify-level-bspmaterial info
#notify-level-display debug
#notify-level-raytrace info
#notify-level-glgsg debug
#notify-level-gsg info
#notify-level-bullet info
#notify-level-linmath info
#notify-level-net spam
notify-timestamp #f
default-directnotify-level info
on-screen-debug-enabled 1

# Filenames...
#cursor-filename resources/toonmono.cur
#icon-filename resources/icon.ico

default-model-extension .egg

#model-cache-dir ./cache
model-cache-model #t
model-cache-textures #t
model-cache-compressed-textures 1

physics-debug #f

model-path .

# Audio...

# Woo-hoo!!!! Miles!!
audio-library-name p3openal_audio
audio-cache-limit 9999999
audio-preload-threshold 99999999
#miles-audio-expand-mp3-threshold 10000000
#miles-audio-panda-threads #t
#audio-library-name p3openal_audio

# Virtual file system...
vfs-mount resourcepack/phase_3 phase_3
vfs-mount resourcepack/phase_3.5 phase_3.5
vfs-mount resourcepack/phase_4 phase_4
vfs-mount resourcepack/phase_5 phase_5
vfs-mount resourcepack/phase_5.5 phase_5.5
vfs-mount resourcepack/phase_6 phase_6
vfs-mount resourcepack/phase_7 phase_7
vfs-mount resourcepack/phase_8 phase_8
vfs-mount resourcepack/phase_9 phase_9
vfs-mount resourcepack/phase_10 phase_10
vfs-mount resourcepack/phase_11 phase_11
vfs-mount resourcepack/phase_12 phase_12
vfs-mount resourcepack/phase_13 phase_13
vfs-mount resourcepack/phase_14 phase_14

# Server...
server-port 7032
server-address 127.0.0.1
connect-method native

# Resync clocks every minute.
# This may need to be shrinked even further.
time-manager-freq 60

# 150-300 ms latency
simulated-latency 0
simulated-latency-min 0.125
simulated-latency-max 0.15

# Performance...
hardware-animated-vertices #t
sync-video #f
smooth-lag 0.1
smooth-prediction-lag 0.0
basic-shaders-only #f
framebuffer-multisample 1
framebuffer-stencil 0
support-stencil 0
framebuffer-srgb 1
framebuffer-alpha 0
framebuffer-float 0
depth-bits 8
color-bits 8 8 8
alpha-bits 0
multisamples 16
garbage-collect-states-rate 0.5

audio-dls-file resources/gm.dls

# Game content...
game-name Cog Invasion
want-weapons #t
want-pies #t
want-chat #t
want-sa-reactions #f
gag-start-key alt
gag-throw-key alt-up
want-firstperson-battle #f
chat-key t
want-WASD #t
want-gta-controls #f
show-minigame-dates #f
want-real-shadows #f
load-stuff #f
want-playground-gags #f
gsg-want-hlsounds #f
explosion-hlsounds #f
want-nametags #f

hdr-min-avg-lum 3.0
hdr-percent-bright-pixels 2.0
hdr-percent-target 60.0
hdr-debug-histogram #f
hdr-tonemap-scale 1.0

want-pssm 1
pssm-debug-cascades 0
pssm-splits 3
pssm-size 2048
pssm-shadow-depth-bias 0.0001
pssm-max-distance 200
pssm-sun-distance 400
pssm-normal-offset-scale 3.0
pssm-normal-offset-uv-space 1
pssm-softness-factor 2.0
pssm-cache-shaders 1
pssm-ambient-light-identifier 0.2 0.2 0.2
pssm-ambient-light-min 0.2 0.2 0.2
pssm-ambient-light-scale 15.0
shadow-depth-bits 32
stencil-bits 0

# Time averaged lighting in BSP levels to reduce popping
light-average 1
light-lerp-speed 5.0

ctmusic-numsongs 1

want-pstats 1
pstats-gpu-timing 0
#pstats-host 127.0.0.1
pstats-view-on-server 1
pstats-eventmanager 1

preload-textures 1
preload-simple-textures 1
texture-compression 0
allow-incomplete-render 1
allow-async-bind 1
restore-initial-pose 0

flatten-collision-nodes 1

egg-load-old-curves 0

show-buffers #f

texture-minfilter mipmap
texture-magfilter linear
text-minfilter linear
text-magfilter linear
gl-coordinate-system default
gl-force-fbo-color 0
garbage-collect-states 0
allow-flatten-color 1
gl-debug 0
gl-finish 0
gl-debug-synchronous 1
gl-debug-abort-level fatal
gl-depth-zero-to-one 0
gl-force-depth-stencil 0
gl-compile-and-execute 1
glsl-preprocess 1
gl-version 3 2

text-flatten 1
text-dynamic-merge 1

interpolate-frames 1

threading-model Cull/Draw # experimental
assert-abort 1

textures-power-2 none

precache-assets 0

mat_rimlight 1
mat_envmaps 1
mat_phong 1

support-ipv6 0

r_ambientboost 1
r_ambientmin 0.3
r_ambientfraction 0.1
r_ambientfactor 5.0

r_bloomscale 1.0
r_bloomtintr 0.3
r_bloomtintg 0.59
r_bloomtintb 0.11
r_bloomtintexponent 2.2

decals_remove_overlapping 0
decals_max 30

geom-cache-size 999999
