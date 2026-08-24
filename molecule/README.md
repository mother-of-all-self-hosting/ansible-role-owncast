<!--
SPDX-FileCopyrightText: 2018-2025 Slavi Pantaleev
SPDX-FileCopyrightText: 2019-2022 Aaron Raimist
SPDX-FileCopyrightText: 2019-2023 MDAD project contributors
SPDX-FileCopyrightText: 2023 QEDeD
SPDX-FileCopyrightText: 2024 Fabio Bonelli
SPDX-FileCopyrightText: 2024 Nikita Chernyi
SPDX-FileCopyrightText: 2024-2026 Suguru Hirahara
SPDX-FileCopyrightText: 2026 spatterlight

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Molecule Testing

This role supports [Molecule](https://docs.ansible.com/projects/molecule/), an Ansible testing framework designed for developing and testing Ansible collections, playbooks, and roles.

## Prerequisites

To utilize Molecule you need to prepare several requirements:

- **x86** computer running one of these operating systems that make use of [systemd](https://systemd.io/):
  - **Archlinux**
  - **CentOS**, **Rocky Linux**, **AlmaLinux**, or possibly other RHEL alternatives (although your mileage may vary)
  - **Debian** (10/Buster or newer)
  - **Ubuntu** (18.04 or newer, although [20.04 may be problematic](https://github.com/mother-of-all-self-hosting/mash-playbook/blob/main/docs/ansible.md#supported-ansible-versions) if you run the Ansible playbook on it)
- `root` access on the computer which Molecule runs against
- [Ansible](http://ansible.com/) program
- [Python](https://www.python.org/)
  - Most distributions install Python by default, but some don't (e.g. Ubuntu 18.04) and require manual installation (something like `apt-get install python3`)
- [Docker](https://www.docker.com)
  - Access to Docker UNIX socket (`/var/run/docker.sock`) is required by default

## Installation

To set up the environment for using Molecule, run the command below on the terminal:

```bash
python3 -m venv ./molecule/venv
source ./molecule/venv/bin/activate
pip3 install -r ./molecule/requirements.txt
```

## Scenarios

Currently these testing scenarios are available:

### `default`

Tests a standard Owncast installation.

### `default-selfbuild`

Tests a standard Owncast installation with self-building the container image.

## What the scenarios verify

Owncast serves its web interface, and answers its public API, from the moment it starts — there is no setup wizard to walk through, and no configuration it insists on before it will run. A plain `docker run` of the upstream image therefore passes any check that stops at "something answered over HTTP", which is why the scenarios go further:

- the version Owncast reports over its API is the one `owncast_version` asks for, so that a bump to a tag that does not exist, or that cannot serve, fails here (self-built images are exempt — upstream's `Dockerfile` stamps the version from a `VERSION` build argument that this role does not pass, and defaults it to `dev`)
- the administration API refuses unauthenticated requests and wrong passwords, and serves the server configuration to a correct one — which it can only do out of the database in the data directory the role provisioned
- Owncast listens on the same ports that the role publishes
- the container runs the way the role asks for: as an unprivileged user, with a read-only root filesystem, with all capabilities dropped, on its own container network, and from the image the scenario selected
- the RTMP ingest server accepts a broadcast that names the stream key the administration API reports, and refuses one that does not

The RTMP probe ([`files/rtmp-probe.py`](files/rtmp-probe.py)) speaks enough of the protocol to complete a handshake, open a connection and offer a stream key, which is the point at which Owncast commits to accepting or refusing the broadcast. It deliberately stops there rather than pushing video, so that no broadcasting software (`ffmpeg`, OBS) is needed to run the tests.

## Running

By default it is configured to run the scenarios on Ubuntu 26.04.

```bash
molecule test --scenario-name default
```

You can utilize other distributions by setting one to the `MOLECULE_DISTRO` environment variable:

```bash
# Ubuntu 24.04
MOLECULE_DISTRO=ubuntu2404 molecule test --scenario-name default

# Debian 13
MOLECULE_DISTRO=debian13 molecule test --scenario-name default

# Debian 12
MOLECULE_DISTRO=debian12 molecule test --scenario-name default
```
