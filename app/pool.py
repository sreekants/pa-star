#!/usr/bin/python
from PIL import Image
import os, math, sys
import numpy

TILE_SIZE  = 4
transparent = (255, 255, 255, 0)
red         = (255, 0, 0, 255)
green       = (0, 255, 0, 255)
black       = (0, 0, 0, 255)

def getcolor(x, y, input, width, height):
    #print( f'x={x} y={y} ({x*9}, {(y)*9}) ({(x+1)*9}, {(y+1)*9})')


    color       = transparent

    for i in range(x*TILE_SIZE, (x+1)*TILE_SIZE): 
        if i >= width:
            break

        for j in range(y*TILE_SIZE, (y+1)*TILE_SIZE):
            if j>=height:
                break

            pixel = input[i, j]
            # print( f'{x}, {y} = {input[x, y]}')

            if pixel == red:    # Goal point
                return red 
            
            if pixel == green:  # Start point
                return green

            if pixel == black:
                color = black

    return color

def getgradient(x, y, input, width, height):
    #print( f'x={x} y={y} ({x*9}, {(y)*9}) ({(x+1)*9}, {(y+1)*9})')

    count   = 0
    block   = 0

    for i in range(x*TILE_SIZE, (x+1)*TILE_SIZE): 
        if i >= width:
            break

        for j in range(y*TILE_SIZE, (y+1)*TILE_SIZE):
            if j>=height:
                break

            count   = count+1
            pixel   = input[i, j]

            if pixel == black:
                block   = block+1

    if count == 0:
        return 0.0
    
    return float(block)/float(count)

def get_density( input, width, height ):
    walls      = 0
    for x in range(0,width):
        for y in range(0,height):
            if input[x, y] == black:
                walls   = walls+1

    spaces      = width*height - walls
    density     = float(walls)/float(width*height)
    
    return density

def get_dispersion( input, width, height, cwidth, cheight ):
    # Iterate over all pixels
    samples = []

    for x in range(0,cwidth):
        for y in range(0,cheight):
            gradient    = getgradient(x, y, input, width, height)
            samples.append(gradient)

    return (numpy.mean(samples, axis=0), numpy.std(samples, axis=0))

def process_image(input_image_path:str, output_image_path:str):
    # Load the image
    rgba_image  = Image.open(input_image_path)
    input       = rgba_image.load()

    # Width and height of the image
    width, height    = rgba_image.size
    cwidth, cheight  = (math.ceil(float(width)/float(TILE_SIZE)), math.ceil(float(height)/float(TILE_SIZE)))


    # Create the convolution image
    conv_image  = Image.new( 'RGBA', 
                            (cwidth, cheight), 
                            (255, 255, 255, 0))

    output      = conv_image.load()

    # print( getcolor(0, 0, input, width, height) )
    # sys.exit(0)

    density = get_density( input, width, height )
    opacity = get_dispersion( input, width, height, cwidth, cheight )
    # print( f"density = {density:.2}")
    # print( f"opacity = mu:{opacity[0]:.2} sigma:{opacity[1]:.2}")

    # Iterate over all pixels
    for x in range(0,cwidth):
        for y in range(0,cheight):
            output[x, y]    = getcolor(x, y, input, width, height)


    # Save the modified image
    if os.path.isfile(output_image_path) == False:
        conv_image.save(output_image_path, 'PNG')
        
    return density, opacity


if __name__ == "__main__":
    input_image_path    = sys.argv[1] 
    output_image_path   = input_image_path.replace( '.png', '.conv.png' )
    process_image(input_image_path, output_image_path)