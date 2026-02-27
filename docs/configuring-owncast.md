<!--
SPDX-FileCopyrightText: 2020 - 2024 MDAD project contributors
SPDX-FileCopyrightText: 2020 - 2024 Slavi Pantaleev
SPDX-FileCopyrightText: 2020 Aaron Raimist
SPDX-FileCopyrightText: 2020 Chris van Dijk
SPDX-FileCopyrightText: 2020 Dominik Zajac
SPDX-FileCopyrightText: 2020 Mickaël Cornière
SPDX-FileCopyrightText: 2022 François Darveau
SPDX-FileCopyrightText: 2022 Julian Foad
SPDX-FileCopyrightText: 2022 Warren Bailey
SPDX-FileCopyrightText: 2023 Antonis Christofides
SPDX-FileCopyrightText: 2023 Felix Stupp
SPDX-FileCopyrightText: 2023 Julian-Samuel Gebühr
SPDX-FileCopyrightText: 2023 Pierre 'McFly' Marty
SPDX-FileCopyrightText: 2024 - 2025 Suguru Hirahara
SPDX-FileCopyrightText: 2024 MASH project contributors
SPDX-FileCopyrightText: 2024 Sergio Durigan Junior

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Setting up Owncast

This is an [Ansible](https://www.ansible.com/) role which installs [Owncast](https://owncast.online) to run as a [Docker](https://www.docker.com/) container wrapped in a systemd service.

Owncast is a free and open source live video and web chat server for use with existing popular broadcasting software.

See the project's [documentation](https://owncast.online/docs/) to learn what Owncast does and why it might be useful to you.

## Prerequisites

### Open a port

You may need to open the following port on your server:

- `1935` over **TCP**, controlled by `owncast_container_http_host_bind_port` — used for TCP based [RTMP](https://en.wikipedia.org/wiki/Real-Time_Messaging_Protocol)

Docker automatically opens the port in the server's firewall, so you likely don't need to do anything. If you use another firewall in front of the server, you may need to adjust it.

By default, the port will be exposed by the container on **all network interfaces**.

## Adjusting the playbook configuration

To enable Owncast with this role, add the following configuration to your `vars.yml` file.

**Note**: the path should be something like `inventory/host_vars/mash.example.com/vars.yml` if you use the [MASH Ansible playbook](https://github.com/mother-of-all-self-hosting/mash-playbook).

```yaml
########################################################################
#                                                                      #
# owncast                                                              #
#                                                                      #
########################################################################

owncast_enabled: true

########################################################################
#                                                                      #
# /owncast                                                             #
#                                                                      #
########################################################################
```

### Set the hostname

To enable Owncast you need to set the hostname as well. To do so, add the following configuration to your `vars.yml` file. Make sure to replace `example.com` with your own value.

```yaml
owncast_hostname: "example.com"
```

After adjusting the hostname, make sure to adjust your DNS records to point the domain to your server.

**Note**: hosting Owncast under a subpath (by configuring the `owncast_path_prefix` variable) does not seem to be possible due to Owncast's technical limitations.

### Extending the configuration

There are some additional things you may wish to configure about the service.

Take a look at:

- [`defaults/main.yml`](../defaults/main.yml) for some variables that you can customize via your `vars.yml` file. You can override settings (even those that don't have dedicated playbook variables) using the `owncast_environment_variables_additional_variables` variable

## Installing

After configuring the playbook, run the installation command of your playbook as below:

```sh
ansible-playbook -i inventory/hosts setup.yml --tags=setup-all,start
```

If you use the MASH playbook, the shortcut commands with the [`just` program](https://github.com/mother-of-all-self-hosting/mash-playbook/blob/main/docs/just.md) are also available: `just install-all` or `just setup-all`

## Usage

After running the command for installation, the Owncast instance becomes available at the URL specified with `owncast_hostname`. With the configuration above, the service is hosted at `https://example.com`.

To get started, open the URL `https://owncast.example.com/admin` with a web browser.

>[!NOTE]
> Change the default stream key set to `abc123` as soon as possible.

## Troubleshooting

### Check the service's logs

You can find the logs in [systemd-journald](https://www.freedesktop.org/software/systemd/man/systemd-journald.service.html) by logging in to the server with SSH and running `journalctl -fu owncast` (or how you/your playbook named the service, e.g. `mash-owncast`).
