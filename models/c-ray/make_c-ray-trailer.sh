#! /bin/bash
# Build a c-ray-trailer and keep it on the shared file system.

# Create the render configuration here
cat <<END >c-ray-trailer
# walls
#s	0 -1000 0		999		1.0 1.0 1.0			10.0	10.0

# bouncing ball
#s	0 0 2			1		1.0 0.5 0.1			60.0	0.7

# lights...
l	-50 100 -50
l	50 100 -250

# camera (there can be only one!)
#	position	FOV		target
c	0 6 -17		20		0 -1 0
END

