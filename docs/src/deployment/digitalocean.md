How to Deploy Fluxomni to DigitalOcean
=======================================

This guide shows the recommended setup for Fluxomni on one [DigitalOcean] droplet.

## 0. Prerequisites

You need a [DigitalOcean] account with a [payment method][1].

## 1. Create Droplet

Open the [droplet creation page][2].

### 1.1. Choose an Image

Select **Ubuntu 24.04 LTS**.

### 1.2. Choose a Plan

Budget the whole droplet with the [sizing guide](../getting-started/sizing.md). One measured media container used 1 CPU and 2 GiB, and that figure excludes the OS, Docker, frontend, and control plane. Transcoding, playlist playback, and recording need their own test.

![Server resources](../images/do_1.2.jpg)

### 1.3. Add Volume (Optional)

> __NOTE__: Skip this step if you do not plan to record streams to files.

Recording live streams may need more disk space than the default disk provides. You can attach an external block storage volume to the droplet.

![Add volume](../images/do_1.3.1.jpg)
![Setup volume](../images/do_1.3.2.jpg)

The installer does not detect or mount this volume. Format it, mount it, and point `FLUXOMNI_CONTROL_PLANE_DATA_DIR` and `FLUXOMNI_MEDIA_NODE_DATA_DIR` at directories on that mount before you store recordings there. See [Configuration](../getting-started/configuration.md).

### 1.4. Choose a Datacenter Region

Choose a region near both your stream source and destinations to reduce latency.

![Region](../images/do_1.4.jpg)

### 1.5. Add User Data

To automatically install Fluxomni on the new droplet, paste the following script into the `User data` field. The script runs once when the droplet is created. It also configures a firewall with the required ports.

```bash
#!/bin/bash
curl -fsSL https://install.fluxomni.io | WITH_UFW=1 bash -s
```

From the installer release after v26.4.0, a new Linux host with a normal Docker Engine also turns preparation limits on. Docker Desktop and WSL stay off. The installer prints the budgets. Set `FLUXOMNI_PREPARATION_CGROUP_ENABLED=0` before `bash` to skip them.

![Provision](../images/do_1.5.jpg)

### 1.6. Select Authentication Method

[DigitalOcean] requires an authentication method to access the droplet. You can use an [SSH] key (recommended) or set a root password. These credentials are for server management. You do not need them to use the Fluxomni web app.

![SSH access](../images/do_1.6.jpg)

### 1.7. Finalize and Create

Choose a hostname for your droplet to easily identify it later. You can leave the other settings at their defaults.

![Droplet name](../images/do_1.7.jpg)

Click **Create Droplet** to begin provisioning.

## 2. Access Fluxomni

After you create the droplet, wait 5-15 minutes for server setup and installation.

You can find the IP address of your droplet in the DigitalOcean control panel.

![Droplet IP](../images/do_2.jpg)

Open the droplet's IP address in your browser.

![Address bar](../images/browser.jpg)

Current releases serve the operator UI from the `frontend` container.
Use `/routes` for route management and `/fleet` to inspect attached media nodes.

> __NOTE__: Fluxomni uses `http://` by default. For production, we strongly recommend a domain name and a reverse proxy, such as Nginx or Caddy, to provide secure access over `https://`.

Next, complete [First Stream](../getting-started/first-stream.md) to create a protected operator account and verify one live route.

[DigitalOcean]: https://digitalocean.com
[SSH]: https://en.wikipedia.org/wiki/SSH_(Secure_Shell)

[1]: https://cloud.digitalocean.com/account/billing
[2]: https://cloud.digitalocean.com/droplets/new
