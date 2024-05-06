import os
import sys
from itertools import combinations_with_replacement
from tqdm import tqdm_notebook as tqdm
import numpy as np

import requests
import urllib.request
import json
import shutil

from pathlib import Path
from PIL import Image

from ..const import IMG_PATH, LIB_PATH
from .const import MAX_SIZE
from ...shared.utils.fileutils import create_dir
from ...shared.utils.logging import console




def save_img(
    img: Image,
    img_filename,
    doc_dir,
    max_dim=MAX_SIZE,
    img_format="JPEG",
):
    try:
        if img.mode != "RGB":
            img = img.convert("RGB")

        if img.width > max_dim or img.height > max_dim:
            img.thumbnail(
                (max_dim, max_dim), Image.ANTIALIAS
            )  # Image.Resampling.LANCZOS
        img_path = os.path.join(doc_dir, img_filename + ".jpg")
        img.save(img_path, format=img_format)
        return img 
    
    except Exception as e:
        console(f"Failed to save {img_filename} as JPEG", e=e)
        return False




def get_json(url):
    with urllib.request.urlopen(url) as url:
        return json.loads(url.read().decode())




def download_img(img_url, doc_id, img_name):
    doc_dir = f"{IMG_PATH}/{doc_id}"
    if not os.path.exists(doc_dir):
        os.makedirs(doc_dir)
    try:
        with requests.get(img_url, stream=True) as response:
            response.raw.decode_content = True
            img = Image.open(response.raw)
            save_img(img, img_name, doc_dir)

    except requests.exceptions.RequestException as e:
        shutil.copyfile(
            f"{LIB_PATH}/media/placeholder.jpg",
            f"{doc_dir}/{img_name}",
        )
        # log_failed_img(img_name, img_url)
        console(f"[download_img] {img_url} is not a valid img file", e=e)
    except Exception as e:
        shutil.copyfile(
            f"{LIB_PATH}/media/placeholder.jpg",
            f"{doc_dir}/{img_name}",
        )
        # log_failed_img(img_name, img_url)
        console(f"[download_img] {img_url} image was not downloaded", e=e)



def is_downloaded(doc_id, image_id):
    path = Path(f"{IMG_PATH}/{doc_id}/{image_id}.jpg")
    return path.exists()

########################################## VECTO HELPER FUNCTIONS ######################################

def line_to_xy(x):
    c_x, c_y, w, h = x
    x0, y0 = c_x - w / 2, c_y - h / 2
    x1, y1 = c_x + w / 2, c_y + h / 2
    
    return x0, y0, x1, y1

def circle_to_xy(x):
    c_x, c_y, w, h = x
    r = (w+h)/4 
    return c_x, c_y, r

def arc_to_xy(x):
    cx, cy, w, h, w_mid, h_mid = x
    x0, y0 = cx - w / 2, cy - h / 2
    x1, y1 = cx + w / 2, cy + h / 2
    x_mid, y_mid = cx + w_mid / 2, cy + h_mid / 2
    return x0, y0, x1, y1, x_mid, y_mid

def get_outputs_per_class(pred_dict):
    mask = pred_dict["labels"] == 0
    lines, line_scores = pred_dict["parameters"][mask][:, :4], pred_dict["scores"][mask]
    mask = pred_dict["labels"] == 1
    circles, circle_scores = (
        pred_dict["parameters"][mask][:, 4:8],
        pred_dict["scores"][mask],
    )
    mask = pred_dict["labels"] == 2
    arcs, arc_scores = pred_dict["parameters"][mask][:, 8:14], pred_dict["scores"][mask]
    lines, line_scores = lines.cpu().numpy(), line_scores.cpu().numpy()
    circles, circle_scores = circles.cpu().numpy(), circle_scores.cpu().numpy()
    arcs, arc_scores = arcs.cpu().numpy(), arc_scores.cpu().numpy()
    lines = np.array([line_to_xy(x) for x in lines])
    circles = np.array([circle_to_xy(x) for x in circles])
    arcs = np.array([arc_to_xy(x) for x in arcs])
    return lines, line_scores, circles, circle_scores, arcs, arc_scores


def is_large_arc(rad_angle):
    if rad_angle[0] <= np.pi:
        return not (rad_angle[0] < rad_angle[1] < (np.pi + rad_angle[0]))
    return (rad_angle[0] - np.pi) < rad_angle[1] < rad_angle[0]
def find_circle_center(p1, p2, p3):
    """Circle center from 3 points"""
    # print(p1, p2, p3)
    temp = p2[0] * p2[0] + p2[1] * p2[1]
    bc = (p1[0] * p1[0] + p1[1] * p1[1] - temp) / 2
    cd = (temp - p3[0] * p3[0] - p3[1] * p3[1]) / 2
    det = (p1[0] - p2[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p2[1])
    if abs(det) < 1.0e-10:
        return (None, None)

    cx = (bc * (p2[1] - p3[1]) - cd * (p1[1] - p2[1])) / det
    cy = ((p1[0] - p2[0]) * cd - (p2[0] - p3[0]) * bc) / det
    return np.array([cx, cy])

def find_circle_center_arr(p1, p2, p3):
    """Circle center from 3 points"""
    temp = p2[:, 0] ** 2 + p2[:, 1] ** 2
    bc = (p1[:, 0] ** 2 + p1[:, 1] ** 2 - temp) / 2
    cd = (temp - p3[:, 0] ** 2 - p3[:, 1] ** 2) / 2
    det = (p1[:, 0] - p2[:, 0]) * (p2[:, 1] - p3[:, 1]) - (p2[:, 0] - p3[:, 0]) * (
        p1[:, 1] - p2[:, 1]
    )

    # Handle the case where the determinant is close to zero
    mask = np.abs(det) < 1.0e-10
    det[mask] = 1.0  # Prevent division by zero
    bc[mask] = 0.0  # These arcs will have center at (0, 0)
    cd[mask] = 0.0

    cx = (bc * (p2[:, 1] - p3[:, 1]) - cd * (p1[:, 1] - p2[:, 1])) / det
    cy = ((p1[:, 0] - p2[:, 0]) * cd - (p2[:, 0] - p3[:, 0]) * bc) / det
    return np.stack([cx, cy], axis=-1)



def get_angles_from_arc_points(p0, p_mid, p1):
    arc_center = find_circle_center(p0, p_mid, p1)
    arc_center = (arc_center[0], arc_center[1])
    start_angle = np.arctan2(p0[1] - arc_center[1], p0[0] - arc_center[0])
    end_angle = np.arctan2(p1[1] - arc_center[1], p1[0] - arc_center[0])
    mid_angle = np.arctan2(p_mid[1] - arc_center[1], p_mid[0] - arc_center[0])
    return start_angle, mid_angle, end_angle, arc_center


def get_arc_plot_params(arc):
    start_angle, mid_angle, end_angle, arc_center = get_angles_from_arc_points(
        arc[:2],
        arc[4:],
        arc[2:4],
    )
    # print(start_angle, mid_angle, end_angle)
    diameter = 2 * np.linalg.norm(arc[:2] - arc_center)
    to_deg = lambda x: (x * 180 / np.pi) % 360
    start_angle, mid_angle, end_angle = (
        to_deg(start_angle),
        to_deg(mid_angle),
        to_deg(end_angle),
    )
    # print("angles", start_angle, mid_angle, end_angle)
    return start_angle, mid_angle, end_angle, arc_center, diameter

############################# SOME HELPERS FOR REMOVING DUPLICATAES #####################

#removing immediate duplicates, very small lines, arcs on top of lines and circles 
#(might need to add merging fragmented lines and arcs)

def remove_duplicate_circles(circle_coords_list, image_size, circle_scores=None):
    circle_coords = np.array(circle_coords_list).reshape(-1, 3) # (n_circles, 3)
    distances = np.linalg.norm(circle_coords[None, :, :] - circle_coords[:, None, :], axis=-1)
    threshold = (image_size[0] + image_size[1]) / 80
    mask = distances < threshold
    indices_to_remove = np.array([np.sum(row[i+1:]) for i, row in enumerate(mask)])
    indices_to_keep = np.where(indices_to_remove == 0)[0]
    if circle_scores is not None:
        circle_scores = np.array(circle_scores)
        return circle_coords_list[indices_to_keep], circle_scores[indices_to_keep]
    return circle_coords[indices_to_keep]

def remove_duplicate_lines(line_coords_list, image_size, line_scores=None):
    line_coords = np.array(line_coords_list).reshape(-1, 4) # (n_lines, 4)
    permuted_lines = np.hstack((line_coords[:, 2:4],line_coords[:, 0:2]))
    distances = np.minimum(np.linalg.norm(line_coords[None, :, :] - line_coords[:, None, :], axis=-1), np.linalg.norm(line_coords[None, :, :] - permuted_lines[:, None, :], axis=-1))
    threshold = (image_size[0] + image_size[1]) / 80
    mask = distances < threshold
    indices_to_remove = np.array([np.sum(row[i+1:]) for i, row in enumerate(mask)])
    indices_to_keep = np.where(indices_to_remove == 0)[0]
    if line_scores is not None:
        line_scores = np.array(line_scores)
        return line_coords_list[indices_to_keep], line_scores[indices_to_keep]
    return line_coords_list[indices_to_keep]

def remove_small_lines(line_coords_list, image_size, line_scores=None):
    line_coords = np.array(line_coords_list).reshape(-1, 4) # (n_lines, 4)
    lengths = np.linalg.norm(line_coords[:, :2] - line_coords[:, 2:], axis=-1)
    threshold = (image_size[0] + image_size[1]) / 50
    # print(lengths)
    mask = lengths > threshold
    indices_to_keep = np.where(mask)[0]
    if line_scores is not None:
        line_scores = np.array(line_scores)
        return line_coords_list[indices_to_keep], line_scores[indices_to_keep]
    return line_coords_list[indices_to_keep]

def remove_duplicate_arcs(line_coords_list, image_size, line_scores=None):
    line_coords = np.array(line_coords_list).reshape(-1, 6) # (n_lines, 6)
    permuted_lines = np.hstack((line_coords[:, 2:4],line_coords[:, 0:2], line_coords[:, 4:6]))
    distances = np.minimum(np.linalg.norm(line_coords[None, :, :] - line_coords[:, None, :], axis=-1), np.linalg.norm(line_coords[None, :, :] - permuted_lines[:, None, :], axis=-1))
    threshold = (image_size[0] + image_size[1]) / 50
    mask = distances < threshold
    indices_to_remove = np.array([np.sum(row[i+1:]) for i, row in enumerate(mask)])
    indices_to_keep = np.where(indices_to_remove == 0)[0]
    if line_scores is not None:
        line_scores = np.array(line_scores)
        return line_coords_list[indices_to_keep], line_scores[indices_to_keep]
    return line_coords_list[indices_to_keep]

def remove_arcs_on_top_of_circles(arc_coords_list, circle_coords_list, image_size, arc_scores=None): 
    arc_coords = np.array(arc_coords_list).reshape(-1, 6) # (n_arcs, 6)
    circle_coords = np.array(circle_coords_list).reshape(-1, 3) # (n_circles, 3)
    arc_centers = find_circle_center_arr(
        arc_coords[:, :2],
        arc_coords[:, 4:],
        arc_coords[:, 2:4],
    )
    radii = np.linalg.norm(arc_coords[:, :2] - arc_centers, axis = 1)
    arc_circle_coords = np.hstack((arc_centers, radii[:, None]))
    distances = np.linalg.norm(circle_coords[None, :, :] - arc_circle_coords[:, None, :], axis=-1)
    threshold = (image_size[0] + image_size[1]) / 80
    # print(distances)
    # print(threshold)
    mask = distances < threshold
    indices_to_remove = np.array([np.sum(row) for i, row in enumerate(mask)])
    indices_to_keep = np.where(indices_to_remove == 0)[0]
    if arc_scores is not None:
        arc_scores = np.array(arc_scores)
        return arc_coords_list[indices_to_keep], arc_scores[indices_to_keep]
    return arc_coords_list[indices_to_keep]

def remove_arcs_on_top_of_lines(arc_coords_list, line_coords_list, image_size, arc_scores=None): 
    arc_coords = np.array(arc_coords_list).reshape(-1, 6) # (n_arcs, 6)
    line_coords = np.array(line_coords_list).reshape(-1, 4) # (n_lines, 4)
    line_coords_w_center = np.hstack((line_coords[:, :2], line_coords[:, 2:], (line_coords[:, :2] + line_coords[:, 2:])/2))
    line_coords_w_center_permuted = np.hstack((line_coords[:, 2:], line_coords[:, :2], (line_coords[:, :2] + line_coords[:, 2:])/2))
    distances = np.minimum(np.linalg.norm(line_coords_w_center[None, :, :] - arc_coords[:, None, :], axis=-1), np.linalg.norm(line_coords_w_center_permuted[None, :, :] - arc_coords[:, None, :], axis=-1))
    threshold = (image_size[0] + image_size[1]) / 50
    mask = distances < threshold
    indices_to_remove = np.array([np.sum(row) for i, row in enumerate(mask)])
    indices_to_keep = np.where(indices_to_remove == 0)[0]
    if arc_scores is not None:
        arc_scores = np.array(arc_scores)
        return arc_coords_list[indices_to_keep], arc_scores[indices_to_keep]
    return arc_coords_list[indices_to_keep]


# arc visualization, very clunky in python but this should work
from matplotlib.patches import Arc
def plot_arc(ax, arc, c='r', linewidth=2):
    arc = arc.reshape(-1)
    theta1, theta_mid, theta2, c_xy, diameter = get_arc_plot_params(arc)
    if theta_mid < theta1 and theta_mid > theta2:
        theta1, theta2 = theta2, theta1
    to_rad = lambda x: (x * np.pi / 180) % (2 * np.pi)
    if not is_large_arc([to_rad(theta1), to_rad(theta_mid)]):
        arc_patch_1 = Arc(
            c_xy,
            diameter,
            diameter,
            angle=0.0,
            theta1=theta1,
            theta2=theta_mid,
            fill=None,
            color=c,
            linewidth=linewidth,
        )
    else:
        arc_patch_1 = Arc(
            c_xy,
            diameter,
            diameter,
            angle=0.0,
            theta1=theta_mid,
            theta2=theta1,
            fill=None,
            color=c,
            # color="black",
            linewidth=linewidth,
        )
    ax.add_patch(arc_patch_1)

    if not is_large_arc([to_rad(theta_mid), to_rad(theta2)]):
        arc_patch_2 = Arc(
            c_xy,
            diameter,
            diameter,
            angle=0.0,
            theta1=theta_mid,
            theta2=theta2,
            fill=None,
            color=c,
            linewidth=linewidth,
        )

    else:
        arc_patch_2 = Arc(
            c_xy,
            diameter,
            diameter,
            angle=0.0,
            theta1=theta2,
            theta2=theta_mid,
            fill=None,
            color=c,
            # color="black",
            linewidth=linewidth,
        )
    ax.add_patch(arc_patch_2)


