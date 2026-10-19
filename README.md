# AIKON-demo
A web interface to showcase demos of the AIKON project.

AIKON-demo provides a frontend on which to upload datasets, run computer vision tasks and visualize results. It interacts with [AIKON-API](github.com/Aikon-platform/aikon-api). For a more complete platform integrating computer vision, corpora management and collaborative work, see the [AIKON platform](https://github.com/Aikon-platform/aikon).

---

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

---

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

---

## Diffrent modes to use the app

When running `install.py` you will be prompted to chose a `MODE` (`dev`, `local` or `prod`). This mode determines how your app will run:
- `dev`: a partially dockerized build for cozy development. Frontend and API web apps run on the host machine, everything else is dockerized (Postgres database and Redis server). View the app in your Web browser on `http://localhost:$DJANGO_PORT`.
- `local`: a fully dockerized instance of the app running entierly on `localhost` for easy demo usage. View the app in your Web browser on `http://localhost:$NGINX_PORT`
- `prod`: a fully dockerized instance of the app, ready for production. It will run on `$PROD_URL`.


---

## Citation

If you find this work useful, please consider citing:

```bibtex
@article{albouy2026aikon,
    title={{AIKON : A Modular Computer Vision Platform for Historical Corpora}},
    author={
        Albouy, Ségolène and
        Norindr, Somkeo and
        Kervegan, Paul and
        Aouinti, Fouad and
        Delanaux, Rémy and
        Champenois, Robin and
        Grometto, Clara and
        Lazaris, Stavros and
        Guilbaud, Alexandre and
        Husson, Matthieu and
        Aubry, Mathieu
    },
    url={https://doi.org/10.1007/s10032-026-00581-x},
    year={2026},
    month={June},
    journal={International Journal on Document Analysis and Recognition (IJDAR)},
    keyword={Digital Humanities, Computer Vision, Historical Documents, Visual Analysis},
}
```
