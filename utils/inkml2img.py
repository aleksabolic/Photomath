from PIL import Image, ImageDraw
import xml.etree.ElementTree as ET
from inkml import *

def scale_coordinates(coordinates, new_size):
    epsilon = 1e-5
    original_min_x, original_min_y = min(coordinates, key=lambda x: x[0])[0], min(coordinates, key=lambda x: x[1])[1]
    original_max_x, original_max_y = max(coordinates, key=lambda x: x[0])[0], max(coordinates, key=lambda x: x[1])[1]

    new_min_x, new_min_y = 0, 0
    new_max_x, new_max_y = new_size

    scaled_coordinates = []

    for x, y in coordinates:
        scaled_x = (x - original_min_x) * (new_max_x - new_min_x) / (original_max_x - original_min_x + epsilon) + new_min_x
        scaled_y = (y - original_min_y) * (new_max_y - new_min_y) / (original_max_y - original_min_y + epsilon) + new_min_y
        scaled_coordinates.append((scaled_x, scaled_y))

    return scaled_coordinates


def scale_coordinates_box(coordinates, x1, x2, y1, y2):
    epsilon = 1e-5

    original_min_x, original_min_y = min(coordinates, key=lambda x: x[0])[0], min(coordinates, key=lambda x: x[1])[1]
    original_max_x, original_max_y = max(coordinates, key=lambda x: x[0])[0], max(coordinates, key=lambda x: x[1])[1]

    new_min_x, new_min_y = x1, y1
    new_max_x, new_max_y = x2, y2

    X_scaling_factor = (new_max_x - new_min_x) / (original_max_x - original_min_x + epsilon)
    Y_scaling_factor = (new_max_y - new_min_y) / (original_max_y - original_min_y + epsilon)

    scaled_coordinates = []

    for x, y in coordinates:
        scaled_x = (x - original_min_x) * X_scaling_factor + new_min_x
        scaled_y = (y - original_min_y) * Y_scaling_factor + new_min_y
        scaled_coordinates.append((scaled_x, scaled_y))

    return scaled_coordinates



def inkml2img(path, image_w = 1032, image_h = 268, padding_x = 0, padding_y = 0 ,thickness = 3, formula = False):
    """
    Converts an inkml file to an PIL image
    :param path: path to the inkml file
    :param image_w: width of the output image
    :param image_h: height of the output image
    :param padding: padding of the image
    :param thickness: thickness of the lines
    :param formula: whether to return the formula as well
    :return: the PIL image and the formula
    """

    tree = ET.parse(path)
    root = tree.getroot()

    width, height = image_w-2*padding_x, image_h-2*padding_y
    image = Image.new('L', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    namespace = {'inkml': 'http://www.w3.org/2003/InkML'}

    coordinates = []
    stops = []

    for j, trace in enumerate(root.findall(".//inkml:trace", namespaces=namespace)):
        points = trace.text.strip().split(',')
        for p in points:
            coordinates.append((float(p.split()[0]), float(p.split()[1])))

        stops.append(len(coordinates)-1)

    coordinates = scale_coordinates(coordinates, (width, height))

    #draw the lines
    index = 0
    for i in range(len(coordinates) - 1):
        if i == stops[index]:
            index+=1
            continue
        draw.line([(coordinates[i][0], coordinates[i][1]), (coordinates[i+1][0], coordinates[i+1][1])], fill='black', width=thickness)

    
    pad_img = Image.new('L', (image_w, image_h), 'white')
    pad_img.paste(image, (padding_x, padding_y))

    if formula:
        truth_annotation = root.find(".//inkml:annotation[@type='truth']", namespaces = namespace).text
        return pad_img, truth_annotation

    return pad_img

def create_seg_img(strokes, image_w = 1032, image_h = 268, padding_x = 0, padding_y = 0 ,thickness = 3):
    """
    Make PIL image from given strokes (list of strokes)
    :param strokes: list of strings representing strokes (for example: ['1 2, 3 4, 5 6', '7 8, 9 10, 11 12'])
    """

    width, height = image_w-2*padding_x, image_h-2*padding_y
    image = Image.new('L', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    coordinates = []
    stops = []

    for stroke in strokes:
        points = stroke.strip().split(',')
        for p in points:
            coordinates.append((float(p.split()[0]), float(p.split()[1])))
        stops.append(len(coordinates)-1)

    coordinates = scale_coordinates(coordinates, (width, height))

    #draw the lines
    index = 0
    for i in range(len(coordinates)-1):
        if i == stops[index]:
            index+=1
            continue
        draw.line([(coordinates[i][0], coordinates[i][1]), (coordinates[i+1][0], coordinates[i+1][1])], fill='black', width=thickness)

    
    pad_img = Image.new('L', (image_w, image_h), 'white')
    pad_img.paste(image, (padding_x, padding_y))

    return pad_img

