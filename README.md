# AIKON-demo
A web interface to showcase demos of the AIKON project.

AIKON-demo provides a frontend on which to upload datasets, run computer vision tasks and visualize results. It interacts with [AIKON-API](github.com/Aikon-platform/aikon-api). For a more complete platform integrating computer vision, corpora management and collaborative work, see the [AIKON platform](https://github.com/Aikon-platform/aikon).

## General requirements

> - **Sudo** privileges
> - **Python** >= 3.10
> - **UV** ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
> - **Node** ([install guide](https://nodejs.org/en/download))
> - **Docker** ([install guide](https://docs.docker.com/engine/install/))
> - **Git**:
>     - `sudo apt install git`
>     - Having configured [SSH access to GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
> - **CUDA** if you want to run the API with a GPU. See [API guide](ap/README)

## Development

1. Install the `api` and `front` apps. The `insall.py` script will walk you through installation options. `.env` creation, Python dependencies installations and so forth. 
    ```bash
    python install.py
    ```
2. Run the app. `run.py` will run and manageall `front` and `api` processes.
    ```bash
    # management commands are: python run.py up|down|logs|build
    # ctrl+c to stop the app (press twice to stop containers as well)
    python run.py
    ```

