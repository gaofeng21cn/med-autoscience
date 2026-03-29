# MedAutoScience macOS First Release

## Positioning

This is the first macOS-focused prerelease of `medautosci`. It is a command-line release, not a desktop App.

## Install

```bash
curl -fsSL https://github.com/gaofeng/med-autoscience/releases/download/v0.1.0a1/install-macos.sh | bash
```

If `medautosci` is not found afterwards:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zprofile
source ~/.zprofile
```

## Preconditions

- macOS on `arm64` or `x86_64`
- `bash`, `curl`, `tar`
- Network access for `uv`, managed Python 3.12, and release assets
- Existing `DeepScientist` / `Codex` / workspace setup when you want to run the full research flow

## Upgrade

Use the install command from the target release you want to move to.

## Uninstall

```bash
~/.local/bin/uv tool uninstall med-autoscience
```

## Limits

- This release only solves CLI installation
- It does not provide an App, GUI, or one-click workspace bootstrap
- Some workflows still require external tools such as `pandoc`
