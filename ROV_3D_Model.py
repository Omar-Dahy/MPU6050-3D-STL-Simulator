import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import serial
import json
from stl import mesh
import cairo

# Setup serial communication for IMU data
ser = serial.Serial('COM3', 38400, timeout=1)  # Adjust 'COM3' if needed

# IMU variables
ax = ay = az = 0.0
yaw_mode = False

# Load STL model
stl_path = "C:/Users/omerd/Downloads/Ice_Fishing_ROV_PVC_connector.STL"
your_mesh = mesh.Mesh.from_file(stl_path)

# Create a Cairo surface for drawing 2D walls and floor
width, height = 640, 480
surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
context = cairo.Context(surface)

# Function to draw the room (walls and floor) with Cairo
def draw_room_with_cairo():
    # Clear the surface
    context.set_source_rgb(0.0, 0.0, 0.0)  # Set the background to black
    context.paint()

    # Draw the floor (gray color)
    context.set_source_rgb(0.5, 0.5, 0.5)  # Gray color for the floor
    context.rectangle(50, 350, 540, 100)  # Position and size of the floor rectangle
    context.fill()

    # Draw the back wall (light brown color)
    context.set_source_rgb(0.8, 0.5, 0.2)  # Light brown color for the wall
    context.rectangle(50, 50, 540, 300)  # Position and size of the back wall
    context.fill()

# Function to initialize OpenGL
def init():
    glShadeModel(GL_SMOOTH)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClearDepth(1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    # Lighting setup
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLight(GL_LIGHT0, GL_POSITION,  (1.0, 1.0, 1.0, 0.0))
    glLight(GL_LIGHT0, GL_DIFFUSE,  (1.0, 1.0, 1.0, 1.0))
    glLight(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))

# Function to resize the window
def resize(width, height):
    if height == 0:
        height = 1
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1.0 * width / height, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

# Function to draw the 3D model
def draw():
    global your_mesh, ax, ay, az, yaw_mode
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Move the camera further away
    glTranslatef(0, 0.0, -50.0)

    # Draw the 2D room (walls and floor) using Cairo
    draw_room_with_cairo()

    # Scale the model
    scaling_factor = 0.4
    glScalef(scaling_factor, scaling_factor, scaling_factor)

    # Rotate based on IMU data
    glRotatef(ay, 1.0, 0.0, 0.0)  # Pitch, rotate around x-axis
    glRotatef(-1 * ax, 0.0, 0.0, 1.0)  # Roll, rotate around z-axis
    if yaw_mode:
        glRotatef(az, 0.0, 1.0, 0.0)  # Yaw, rotate around y-axis

    # Set color to red for the STL model
    glColor3f(1.0, 0.0, 0.0)  # Red color

    # Draw the STL model
    glBegin(GL_TRIANGLES)
    for facet in your_mesh.vectors:
        for vertex in facet:
            glVertex3fv(vertex)
    glEnd()

# Function to read IMU data
def read_data():
    global ax, ay, az
    ax = ay = az = 0.0
    try:
        ser.write(b".")  # Request IMU data
        line = ser.readline().decode('utf-8').strip()  # Read the response
        if line.startswith("{") and line.endswith("}"):  # Validate JSON format
            imu_data = json.loads(line)  # Parse JSON
            ax = imu_data.get("roll", 0.0)   # Extract roll (x-axis)
            ay = imu_data.get("pitch", 0.0)  # Extract pitch (y-axis)
            az = imu_data.get("yaw", 0.0)    # Extract yaw (z-axis)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Data error: {e}")

# Main function to run the program
def main():
    global yaw_mode

    video_flags = OPENGL | DOUBLEBUF
    pygame.init()
    screen = pygame.display.set_mode((640, 480), video_flags)
    pygame.display.set_caption("STL Viewer with IMU Data")
    resize(640, 480)
    init()  # Initialize OpenGL
    frames = 0
    ticks = pygame.time.get_ticks()

    while True:
        event = pygame.event.poll()
        if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            pygame.quit()
            break
        if event.type == KEYDOWN and event.key == K_z:
            yaw_mode = not yaw_mode
            ser.write(b"z")  # Toggle yaw mode

        # Read IMU data
        read_data()

        # Draw the 3D model
        draw()

        pygame.display.flip()
        frames += 1

    print(f"fps: {frames * 1000 / (pygame.time.get_ticks() - ticks)}")
    ser.close()

if __name__ == '__main__':
    main()
