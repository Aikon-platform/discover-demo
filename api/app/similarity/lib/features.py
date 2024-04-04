import os
import sys

import torch
from torchvision.models.feature_extraction import create_feature_extractor
from torchvision import models
from collections import OrderedDict
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler

from ..const import FEATS_PATH
from .utils import get_model_path
from .vit import VisionTransformer
from ...shared.utils.logging import console


def extract_features(data_loader, device, feat_layer, feat_set, feat_net, doc_id):
    """
    feat_net ['resnet34', 'moco_v2_800ep_pretrain', 'dino_deitsmall16_pretrain', 'dino_vitbase8_pretrain']
    """
    torch.cuda.empty_cache()
    with torch.no_grad():
        feat_path = f"{FEATS_PATH}/{doc_id}.pt"
        if os.path.exists(feat_path):
            console(f"Load already computed features {doc_id}")
            return torch.load(feat_path, map_location=device)

        model_path = get_model_path(feat_net)
        if feat_net == "resnet34" and feat_set == "imagenet":
            model = models.resnet34(weights=models.ResNet34_Weights.IMAGENET1K_V1).to(
                device
            )
            model = create_feature_extractor(
                model, return_nodes={"layer3.5.bn2": "conv4", "avgpool": "avgpool"}
            )

        elif feat_net == "moco_v2_800ep_pretrain" and feat_set == "imagenet":
            model = models.resnet50().to(device)
            pre_dict = torch.load(model_path)["state_dict"]
            new_state_dict = OrderedDict()
            for k, v in pre_dict.items():
                name = k[17:]
                new_state_dict[name] = v

            model.load_state_dict(new_state_dict, strict=False)
            model = create_feature_extractor(
                model, return_nodes={"layer3.5.bn3": "conv4", "avgpool": "avgpool"}
            )
        elif feat_net == "dino_deitsmall16_pretrain":
            pre_dict = torch.load(model_path)
            model = VisionTransformer(
                patch_size=16, embed_dim=384, num_heads=6, qkv_bias=True
            ).to(device)
            model.load_state_dict(pre_dict)
        elif feat_net == "dino_vitbase8_pretrain":
            pre_dict = torch.load(model_path)
            model = VisionTransformer(
                patch_size=8, embed_dim=768, num_heads=12, qkv_bias=True
            ).to(device)
            model.load_state_dict(pre_dict)
        else:
            sys.stderr.write("Invalid network or dataset for feature extraction.")
            exit()

        model.eval()
        features = []
        if "dino" in feat_net:
            for i, imgs in enumerate(data_loader):
                features.append(model(imgs).detach().cpu())
        elif feat_layer == "conv4":
            for i, imgs in enumerate(data_loader):
                features.append(
                    model(imgs)["conv4"].detach().cpu().flatten(start_dim=1)
                )
        else:
            for i, imgs in enumerate(data_loader):
                features.append(model(imgs)["avgpool"].detach().cpu().squeeze())

    features = torch.cat(features)
    torch.save(features, feat_path)

    return features


def scale_feats(features, n_components):
    scaler = MinMaxScaler()
    features = scaler.fit_transform(features)

    if n_components >= 1:
        pca = PCA(n_components=int(n_components), whiten=True, random_state=0)
    elif n_components > 0:
        pca = PCA(n_components=n_components, whiten=True, random_state=0)
    else:
        pca = PCA(n_components=None, whiten=True, random_state=0)
    return pca.fit_transform(features)
