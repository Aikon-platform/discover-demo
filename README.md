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

1. To install the API and Front application following the instructions in [api/README](https://github.com/Aikon-platform/discover-api/blob/main/README.md) and [front/README](front/README.md)
    ```bash
    bash setup.sh
    ```
2. Change the `.env.dev` variables to fit your requirements.
3. To start everything in one killable process, run (after installing each part like advised in the subfolders):
    ```bash
    bash run.sh
    ```
