# DTI-demo
A web interface as demo for DTI clustering

Please refer to [api/README](https://github.com/Aikon-platform/discover-api/blob/main/README.md) and [front/README](front/README.md) for installing and running each individual part.

## General requirements

> - **Sudo** privileges
> - **Python** >= 3.10
> - **Git**:
>     - `sudo apt install git`
>     - Having configured [SSH access to GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

## Development

To install the API and Front application following the instructions in [api/README](https://github.com/Aikon-platform/discover-api/blob/main/README.md) and [front/README](front/README.md)

```bash
bash setup.sh
```

Copy the `.env.dev.template` files to `.env.dev`, o start everything in one killable process, run (after installing each part like advised in the subfolders):

```bash
bash run.sh
```
