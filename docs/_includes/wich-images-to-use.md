## Docker Images Reference

### Odoo Images

Pre-built Odoo images for all Community versions from 8.0 to 19.0 are hosted on
[Docker Hub](https://registry.hub.docker.com/r/jobiols/odoo-jeo/tags).

The Dockerfiles to build these images (or create your own) are at
[github.com/jobiols/docker-odoo-jeo](https://github.com/jobiols/docker-odoo-jeo).

You are encouraged to fork the repo and customize images for your needs.

### Version Compatibility Table

| Odoo version | Odoo image tag | Postgres | WDB image |
|---|---|---|---|
| 8.0 | `jobiols/odoo-jeo:8.0` | `postgres:9.6-alpine` | `kozea/wdb` |
| 9.0 | `jobiols/odoo-jeo:9.0` | `postgres:9.6-alpine` | `kozea/wdb` |
| 10.0 | `jobiols/odoo-jeo:10.0` | `postgres:9.6-alpine` | `kozea/wdb` |
| 11.0 | `jobiols/odoo-jeo:11.0` | `postgres:10.1-alpine` | `kozea/wdb` |
| 12.0 | `jobiols/odoo-jeo:12.0` | `postgres:10.1-alpine` | `kozea/wdb` |
| 13.0 | `jobiols/odoo-jeo:13.0` | `postgres:10.1-alpine` | `kozea/wdb` |
| 14.0 | `jobiols/odoo-jeo:14.0` | `postgres:13-alpine` | `kozea/wdb` |
| 15.0 | `jobiols/odoo-jeo:15.0` | `postgres:13-alpine` | `kozea/wdb` |
| 16.0 | `jobiols/odoo-jeo:16.0` | `postgres:13-alpine` | `jobiols/wdb:3.3.1` |
| 17.0 | `jobiols/odoo-jeo:17.0` | `postgres:17.5-alpine` | `jobiols/wdb:3.3.2` |
| 18.0 | `jobiols/odoo-jeo:18.0` | `postgres:17.5-alpine` | `jobiols/wdb:3.3.2` |
| 19.0 | `jobiols/odoo-jeo:19.0` | `postgres:17.5-alpine` | `jobiols/wdb:3.3.2` |

> **Note:** For Odoo 19+, the entrypoint changes from `odoo.py` to `odoo-bin`.

### Other Images

| Image | Purpose | Notes |
|---|---|---|
| `aeroo` | Aeroo reports engine | Only used for Odoo ≤ 9. Can be omitted for newer versions. |
| `dbtools` | Database backup/restore tools | `jobiols/dbtools:1.3.1` — used internally by backup operations. |

### Postgres version notes

- For Postgres ≥ 18, the data volume path inside the container changes to
  `/var/lib/postgresql/18/docker`. Odoo-env handles this automatically.
- The postgres container is named `pg-<clientname>` and connected to the `odoo-net`
  Docker network as `db`.

### How images are declared

In the manifest `docker-images` list, each entry is a pair:

```
'short-name image:tag'
```

The `short-name` tells odoo-env which role the image plays. Recognized names:
`odoo`, `postgres`, `aeroo`, `nginx`.

Example:
```python
'docker-images': [
    'odoo jobiols/odoo-jeo:18.0',
    'postgres postgres:17.5-alpine',
]
```

In debug mode, odoo-env automatically pulls the **debug** variant of the Odoo image
(if available) and extracts sources to the host. In production mode, it pulls the
standard image.
