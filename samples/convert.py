from PIL import Image
import os

def getrgba(input_image_path):
    # Open the input image and convert to grayscale to ensure consistency
    grayscale_image = Image.open(input_image_path).convert('L')
    
    # Convert the grayscale image to RGBA
    rgba_image = grayscale_image.convert('RGBA')
    
    grayscale_image.close()

    return rgba_image

def convert_grayscale_to_rgba_with_transparency(input_image_path, output_image_path, start, goal):  
    # Load the gray scale as an RGBA image
    rgba_image = getrgba(input_image_path)
    
  
    # Access the pixel data
    pixels = rgba_image.load()
    
    # Width and height of the image
    width, height = rgba_image.size
    
    # Iterate over all pixels
    for x in range(width):
        for y in range(height):
            r, g, b, a = pixels[x, y]
            # If the pixel is white in the grayscale image, make it transparent in the RGBA image
            if x == start[0] and y == start[1]:
                pixels[x, y] = (0, 255, 0, 255)
                continue

            if x == goal[0] and y == goal[1]:
                pixels[x, y] = (255, 0, 0, 255)
                continue

            if r == 255 and g == 255 and b == 255:
                pixels[x, y] = (255, 255, 255, 0)
    
    # Save the modified image
    rgba_image.save(output_image_path, 'PNG')

'''    
    # Example usage
    input_image_path = 'maps\\900.png'
    output_image_path = 'maps\\900.png'

    # convert_grayscale_to_rgba(input_image_path, output_image_path)
    convert_grayscale_to_rgba_with_transparency(input_image_path, output_image_path, (0,200), (200,0) )
'''

def find_files(path, ext):
    png_files = []
    # os.walk generates the file names in a directory tree by walking either top-down or bottom-up.
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(ext):
                png_files.append(os.path.join(root, file))
    return png_files

def process_path(path):
    png_files = find_files(path, ".png")
    for file in png_files:
        convert_grayscale_to_rgba_with_transparency(file, file, (0,200), (200,0) )
    return

if __name__ == "__main__":
    process_path('.')