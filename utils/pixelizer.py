import torch 
from torchvision import transforms
import cv2
from PIL import Image
import torch.nn.functional as F
import numpy as np

def get_probs(model, roi_list, device):

    if roi_list == []:
        return np.array([])

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Lambda(lambda x: x * 2 -1)
    ])

    roi_tensors = [transform(roi) for roi in roi_list]
    roi_tensors = torch.stack(roi_tensors).to(device)

    with torch.no_grad():
        model.eval()
        probs = model(roi_tensors)
        probs = F.softmax(probs, dim=1)
        probs = probs.detach().cpu().numpy()

    return probs


def pixelize_image(model, img, device):
    """
    img: pytorch tensor of shape (3, height, width)
    model: model for symbol classification
    device: device to run model on

    return: torch tensor of shape (1 + num_classes, height, width), where the first channel is the original image, 
    and the rest of the channels are the probabilities of each pixel being a certain symbol
    """

    im = cv2.cvtColor(np.array(img.permute(1,2,0)), cv2.COLOR_RGB2GRAY)

    ret, thresh = cv2.threshold(im, 127, 255, 0)
    contours, _ = cv2.findContours(thresh,1, 3)

    symbol_roi = []

    for idx, cnt in enumerate(contours):
    
        x, y, w, h = cv2.boundingRect(cnt)

        #remove outer most rectangle
        if x == 0 and y == 0 and w == im.shape[1] and h == im.shape[0]:
            continue

        roi = im[y:y + h, x:x + w]
        
        symbol_roi.append((x,y,w,h))


    good_symbols = []
    #find nested boxes
    for i, roi in enumerate(symbol_roi):
        x,y,w,h = roi
        is_outer = True

        # check if in another box
        for j, roi2 in enumerate(symbol_roi):
            if i == j:
                continue

            x2,y2,w2,h2 = roi2  

            if x >= x2 and y >= y2 and x + w <= x2 + w2 and y + h <= y2 + h2:
                is_outer = False
                break
        
        if is_outer:
            good_symbols.append(roi)

    # find probs of good symbols
    pil_rois = [Image.fromarray(im[y:y + h, x:x + w]).resize((45,45)) for x,y,w,h in good_symbols]
    probs = get_probs(model, pil_rois, device)

    output = np.zeros((1+probs.shape[-1], im.shape[0], im.shape[1]))

    if probs.shape[-1] == 0:
        # see what is the output size of the model
        dummy_input = [Image.fromarray(im[0:1, 0:1]).resize((45,45))]
        probs = get_probs(model, dummy_input, device)
        output = np.zeros((1 + probs.shape[-1], im.shape[0], im.shape[1]))
        return torch.from_numpy(output)
    
    # add original image
    output[0, :, :] = np.array(img[0,:,:])
    # add prob for each pixel
    for idx, symbols in enumerate(good_symbols):
        x,y,w,h = symbols
        output[1:, y:y+h, x:x+w] = np.tile(probs[idx][:, np.newaxis, np.newaxis], (1, h, w))

    return torch.from_numpy(output)

