# ubdsim

Micropython port of Peter Corke's bdsim - realtime only (no simulation).

# Usage

2 options for typical use:

1. (Recommended) Install and run pre-baked firmware onto your target device from [the releases page](https://github.com/CallumJHays/ubdsim/releases) <# TODO>. Click [here](https://github.com/CallumJHays/ubdsim/wiki/install-guide) for a guide <# TODO>.
2. (Not Recommended) Install using upip. In your micropython interpreter run:

   ```python
   import upip
   upip.install('ubdsim')
   ```

   This is not recommended as the entire library will be loaded into RAM, consuming precious working memory (and potentially being unable to load).

3rd (advanced) option: [Freeze package into your own firmware.](https://docs.micropython.org/en/latest/reference/packages.html#cross-installing-packages-with-freezing) Note that you must include [micropython-ulab](https://github.com/v923z/micropython-ulab) as a `USER_C_MODULE` in your build. Do this if you have custom C modules / are using a version of micropython that is not available on the releases page.

# Development

## Setup

Clone the repo, then; -

```bash
# git clone all submodule dependencies
git submodule update --init --recursive
```

## Compiling Firmware

For unix: `make unix`

For ESP32: `make esp32`

Those are the only two supported so far.

If you need to compile firmware for a device/platform not yet available via the releases page, you may accomplish this easily by adding a new directive to the `Makefile`. When you get this working, [Please share it by making a pull request!](https://github.com/CallumJHays/ubdsim/pulls) so that others may benefit from your labor :)
