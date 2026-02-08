#!/usr/bin/env python3
"""
Neovim Development Environment Bootstrap Script
================================================

One script to set up a complete Neovim development environment on any machine.
Supports Windows, Linux, and macOS.

PREREQUISITE: Python 3 must be installed before running this script.
  - Windows:    winget install Python.Python.3.12
                OR download from https://www.python.org/downloads/
  - Linux:      sudo apt install python3   (usually pre-installed)
  - macOS:      brew install python         (usually pre-installed)

USAGE:
  python bootstrap.py              # Install everything
  python bootstrap.py --dry-run    # Preview what would be installed
  python bootstrap.py --skip-tools # Only install nvim config, skip tool installs

EXTENSIBILITY:
  To add a new language, add an entry to the LANGUAGES dict below.
  To remove a language, delete or comment out its entry.
  No other code changes are needed — the script reads everything from the registry.

Author: iamHrithikRaj
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# LANGUAGE REGISTRY — The single source of truth for all language support.
#
# To add a language:   Add a new entry to this dict.
# To remove a language: Delete or comment out its entry.
# No other code changes needed — everything is driven from this registry.
#
# Fields:
#   label         — Human-readable name (for log messages)
#   treesitter    — Treesitter parser names to install
#   lsp           — LSP server configs (lspconfig name → settings dict)
#   mason         — Mason package names to auto-install
#   formatters    — Conform formatter mappings (filetype → formatter list)
#   linters       — nvim-lint linter mappings (filetype → linter list)
#   plugin_file   — (optional) Custom plugin file to copy to lua/custom/plugins/
#   system_tools  — (optional) List of (install_command, binary_name) tuples
#   prerequisites — (optional) Platform-specific install commands
#                   Keys: "windows", "linux_apt", "linux_dnf", "linux_pacman", "macos"
# ═══════════════════════════════════════════════════════════════════════════════

LANGUAGES = {
    # ── C / C++ ───────────────────────────────────────────────────────────────
    "c_cpp": {
        "label": "C / C++",
        "treesitter": ["c", "cpp", "cmake", "make"],
        "lsp": {
            "clangd": {
                "cmd": [
                    "'clangd'",
                    "'--background-index'",
                    "'--clang-tidy'",
                    "'--header-insertion=iwyu'",
                    "'--completion-style=detailed'",
                    "'--function-arg-placeholders'",
                    "'--fallback-style=llvm'",
                ],
                "extra": "capabilities = { offsetEncoding = { 'utf-16' } },",
            },
        },
        "mason": ["clangd", "clang-format", "cmake-language-server"],
        "formatters": {"c": ["clang-format"], "cpp": ["clang-format"]},
        "linters": {},
    },

    # ── C# ────────────────────────────────────────────────────────────────────
    "csharp": {
        "label": "C#",
        "treesitter": ["c_sharp"],
        "lsp": {},  # Handled by roslyn.nvim plugin (not lspconfig)
        "mason": [],
        "formatters": {"cs": ["csharpier"]},
        "linters": {},
        "plugin_file": "roslyn.lua",
        "system_tools": [("dotnet tool install -g csharpier", "csharpier")],
        "prerequisites": {
            "windows": "winget install Microsoft.DotNet.SDK.9 --accept-source-agreements --accept-package-agreements",
            "linux_apt": "sudo apt install -y dotnet-sdk-9.0",
            "linux_dnf": "sudo dnf install -y dotnet-sdk-9.0",
            "macos": "brew install dotnet-sdk",
        },
    },

    # ── Rust ──────────────────────────────────────────────────────────────────
    "rust": {
        "label": "Rust",
        "treesitter": ["rust", "toml"],
        "lsp": {
            # rust-analyzer is managed by rustaceanvim, NOT lspconfig
            "taplo": {"_config": "{}"},
        },
        "mason": ["taplo"],
        "formatters": {"rust": ["rustfmt"], "toml": ["taplo"]},
        "linters": {},
        "plugin_file": "rust.lua",
        "prerequisites": {
            "windows": "winget install Rustlang.Rustup --accept-source-agreements --accept-package-agreements",
            "linux_apt": "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
            "linux_dnf": "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
            "linux_pacman": "sudo pacman -S --noconfirm rustup && rustup default stable",
            "macos": "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
        },
    },

    # ── Python ────────────────────────────────────────────────────────────────
    "python": {
        "label": "Python",
        "treesitter": ["python"],
        "lsp": {
            "pyright": {
                "_config": """{
          settings = {
            python = {
              analysis = {
                typeCheckingMode = 'basic',
                autoSearchPaths = true,
                useLibraryCodeForTypes = true,
              },
            },
          },
        }""",
            },
        },
        "mason": ["pyright", "black", "ruff"],
        "formatters": {"python": ["ruff_format", "black", "stop_after_first = true"]},
        "linters": {"python": ["ruff"]},
    },

    # ── Markdown ──────────────────────────────────────────────────────────────
    "markdown": {
        "label": "Markdown",
        "treesitter": ["markdown", "markdown_inline", "mermaid"],
        "lsp": {"marksman": {"_config": "{}"}},
        "mason": ["marksman", "prettier", "markdownlint"],
        "formatters": {"markdown": ["prettier"]},
        "linters": {"markdown": ["markdownlint"]},
        "plugin_file": "markdown.lua",
    },

    # ── JSON ──────────────────────────────────────────────────────────────────
    "json": {
        "label": "JSON",
        "treesitter": ["json"],
        "lsp": {
            "jsonls": {
                "_config": """{
          settings = {
            json = {
              validate = { enable = true },
            },
          },
        }""",
            },
        },
        "mason": ["json-lsp"],
        "formatters": {"json": ["prettier"]},
        "linters": {},
    },

    # ── XML ───────────────────────────────────────────────────────────────────
    "xml": {
        "label": "XML",
        "treesitter": ["xml"],
        "lsp": {"lemminx": {"_config": "{}"}},
        "mason": ["lemminx"],
        "formatters": {"xml": ["xmlformatter"]},
        "linters": {},
    },

    # ── YAML ──────────────────────────────────────────────────────────────────
    "yaml": {
        "label": "YAML",
        "treesitter": ["yaml"],
        "lsp": {},  # yamlls could be added here if needed
        "mason": [],
        "formatters": {"yaml": ["prettier"]},
        "linters": {},
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# CORE TOOLS — Always installed regardless of language selection.
# These are the base dependencies for Neovim + kickstart.nvim to work.
# ═══════════════════════════════════════════════════════════════════════════════

CORE_TOOLS = {
    "windows": {
        "Neovim": "winget install Neovim.Neovim --accept-source-agreements --accept-package-agreements",
        "Git": "winget install Git.Git --accept-source-agreements --accept-package-agreements",
        "ripgrep": "winget install BurntSushi.ripgrep.MSVC --accept-source-agreements --accept-package-agreements",
        "fd": "winget install sharkdp.fd --accept-source-agreements --accept-package-agreements",
        "CMake": "winget install Kitware.CMake --accept-source-agreements --accept-package-agreements",
        "Node.js": "winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements",
        "Nerd Font": "winget install DEVCOM.JetBrainsMonoNerdFont --accept-source-agreements --accept-package-agreements",
    },
    "linux_apt": {
        "Neovim + tools": "sudo apt update && sudo apt install -y neovim git ripgrep fd-find unzip gcc make cmake curl",
        "Node.js": "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt install -y nodejs",
    },
    "linux_dnf": {
        "Neovim + tools": "sudo dnf install -y neovim git ripgrep fd-find unzip gcc make cmake curl",
        "Node.js": "sudo dnf install -y nodejs",
    },
    "linux_pacman": {
        "Neovim + tools": "sudo pacman -S --noconfirm --needed neovim git ripgrep fd unzip gcc make cmake curl",
        "Node.js": "sudo pacman -S --noconfirm --needed nodejs npm",
    },
    "macos": {
        "Neovim + tools": "brew install neovim git ripgrep fd cmake",
        "Node.js": "brew install node",
        "Nerd Font": "brew install --cask font-jetbrains-mono-nerd-font",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# PLATFORM DETECTION
# ═══════════════════════════════════════════════════════════════════════════════


def detect_platform() -> str:
    """Detect OS and return platform key for CORE_TOOLS / prerequisites."""
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "macos"
    elif system == "Linux":
        # Detect Linux package manager
        if shutil.which("apt"):
            return "linux_apt"
        elif shutil.which("dnf"):
            return "linux_dnf"
        elif shutil.which("pacman"):
            return "linux_pacman"
        else:
            print("⚠  Could not detect Linux package manager (apt/dnf/pacman)")
            print("   You may need to install dependencies manually.")
            return "linux_apt"  # fallback
    else:
        print(f"⚠  Unknown OS: {system}")
        return "windows"


def get_nvim_config_path() -> Path:
    """Return the platform-specific Neovim config directory."""
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", "")) / "nvim"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(xdg) / "nvim"


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND RUNNER
# ═══════════════════════════════════════════════════════════════════════════════


def run(cmd: str, desc: str, dry_run: bool = False) -> bool:
    """Run a shell command with a description. Returns True on success."""
    print(f"  → {desc}")
    if dry_run:
        print(f"    [DRY RUN] {cmd}")
        return True
    try:
        # Use shell=True for cross-platform compatibility (handles pipes, &&, etc.)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            # Don't fail hard — some tools may already be installed
            stderr = result.stderr.strip()
            if "already installed" in stderr.lower() or "no applicable" in stderr.lower():
                print(f"    ✓ Already installed")
                return True
            print(f"    ⚠  Warning: {stderr[:200]}")
            return False
        print(f"    ✓ Done")
        return True
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False


def is_installed(binary: str) -> bool:
    """Check if a binary is available in PATH."""
    return shutil.which(binary) is not None


# ═══════════════════════════════════════════════════════════════════════════════
# INSTALL STEPS
# ═══════════════════════════════════════════════════════════════════════════════


def install_core_tools(plat: str, dry_run: bool):
    """Install core tools (Neovim, git, ripgrep, fd, cmake, node, font)."""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Installing Core Tools                   ║")
    print("╚══════════════════════════════════════════╝")

    tools = CORE_TOOLS.get(plat, {})
    for name, cmd in tools.items():
        run(cmd, f"Installing {name}", dry_run)

    # Install Nerd Font on Linux (not available via apt/dnf/pacman)
    if plat.startswith("linux"):
        install_nerd_font_linux(dry_run)


def install_nerd_font_linux(dry_run: bool):
    """Download and install JetBrainsMono Nerd Font on Linux."""
    font_dir = Path.home() / ".local" / "share" / "fonts"
    if (font_dir / "JetBrainsMonoNerdFont-Regular.ttf").exists():
        print("  → Nerd Font: Already installed")
        return

    print("  → Installing JetBrainsMono Nerd Font...")
    if dry_run:
        print("    [DRY RUN] Would download and install font")
        return

    font_dir.mkdir(parents=True, exist_ok=True)
    cmds = [
        "curl -fLo /tmp/JetBrainsMono.zip https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip",
        f"unzip -o /tmp/JetBrainsMono.zip -d {font_dir}",
        "fc-cache -fv",
        "rm -f /tmp/JetBrainsMono.zip",
    ]
    for cmd in cmds:
        run(cmd, cmd.split()[0], dry_run)


def install_language_prerequisites(plat: str, dry_run: bool):
    """Install language-specific prerequisites (Rust toolchain, .NET SDK, etc.)."""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Installing Language Prerequisites       ║")
    print("╚══════════════════════════════════════════╝")

    for lang_id, lang in LANGUAGES.items():
        prereqs = lang.get("prerequisites", {})
        cmd = prereqs.get(plat)
        if cmd:
            run(cmd, f"{lang['label']} prerequisites", dry_run)

    # Configure NuGet source if .NET SDK is present (needed for csharpier)
    if "csharp" in LANGUAGES:
        if is_installed("dotnet") or dry_run:
            run(
                "dotnet nuget add source https://api.nuget.org/v3/index.json -n nuget.org",
                "Configuring NuGet source",
                dry_run,
            )


def install_system_tools(dry_run: bool):
    """Install global system tools defined in language registry (e.g., csharpier)."""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Installing Global Tools                 ║")
    print("╚══════════════════════════════════════════╝")

    for lang_id, lang in LANGUAGES.items():
        for cmd, binary in lang.get("system_tools", []):
            if is_installed(binary) and not dry_run:
                print(f"  → {binary}: Already installed")
            else:
                run(cmd, f"Installing {binary} ({lang['label']})", dry_run)


def install_nvim_config(dry_run: bool):
    """Clone kickstart.nvim and overlay our customized config."""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Installing Neovim Config                ║")
    print("╚══════════════════════════════════════════╝")

    config_path = get_nvim_config_path()
    repo_nvim_dir = Path(__file__).parent / "nvim"

    if config_path.exists():
        print(f"  → Neovim config already exists at {config_path}")
        print(f"    Backing up to {config_path}.bak")
        if not dry_run:
            bak_path = Path(str(config_path) + ".bak")
            if bak_path.exists():
                shutil.rmtree(bak_path)
            shutil.copytree(config_path, bak_path)

    # Clone kickstart.nvim as the base
    if not (config_path / ".git").exists():
        run(
            f'git clone https://github.com/nvim-lua/kickstart.nvim.git "{config_path}"',
            "Cloning kickstart.nvim",
            dry_run,
        )
    else:
        print("  → kickstart.nvim already cloned")

    # Overlay our customized files on top of kickstart
    print("  → Overlaying customized config files...")
    if not dry_run:
        # Ensure target directories exist
        (config_path / "lua" / "custom" / "plugins").mkdir(parents=True, exist_ok=True)
        (config_path / "lua" / "kickstart" / "plugins").mkdir(parents=True, exist_ok=True)

        # Copy all files from our nvim/ directory
        for src_file in repo_nvim_dir.rglob("*"):
            if src_file.is_file():
                rel = src_file.relative_to(repo_nvim_dir)
                dst_file = config_path / rel
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)
                print(f"    ✓ {rel}")

    print(f"  ✓ Config installed to {config_path}")


def setup_vim_alias(plat: str, dry_run: bool):
    """Set up 'vim' command to open nvim."""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Setting up vim → nvim alias             ║")
    print("╚══════════════════════════════════════════╝")

    if plat == "windows":
        # Add alias to PowerShell profile
        profile_path = Path(os.environ.get("USERPROFILE", "")) / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
        alias_line = "Set-Alias -Name vim -Value nvim"

        if profile_path.exists() and alias_line in profile_path.read_text():
            print("  → Alias already configured in PowerShell profile")
            return

        print(f"  → Adding alias to {profile_path}")
        if not dry_run:
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            with open(profile_path, "a") as f:
                f.write(f"\n# Neovim alias — use 'vim' to open nvim\n{alias_line}\n")
        print("    ✓ Done (restart terminal to take effect)")

    else:
        # Add alias to shell rc file
        shell = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell:
            rc_file = Path.home() / ".zshrc"
        else:
            rc_file = Path.home() / ".bashrc"

        alias_line = "alias vim='nvim'"

        if rc_file.exists() and alias_line in rc_file.read_text():
            print(f"  → Alias already configured in {rc_file.name}")
            return

        print(f"  → Adding alias to {rc_file}")
        if not dry_run:
            with open(rc_file, "a") as f:
                f.write(f"\n# Neovim alias — use 'vim' to open nvim\n{alias_line}\n")
        print("    ✓ Done (restart terminal or run: source " + str(rc_file) + ")")


# ═══════════════════════════════════════════════════════════════════════════════
# POST-INSTALL SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════


def print_summary(plat: str):
    """Print post-install instructions."""
    print("\n" + "=" * 60)
    print("  ✅  SETUP COMPLETE!")
    print("=" * 60)
    print()
    print("  Installed languages:")
    for lang in LANGUAGES.values():
        print(f"    • {lang['label']}")
    print()
    print("  Next steps:")
    print("    1. Set your terminal font to 'JetBrainsMono Nerd Font'")
    if plat == "windows":
        print("       Windows Terminal → Settings → Appearance → Font face")
    print("    2. Restart your terminal (to pick up PATH changes)")
    print("    3. Run 'nvim' — plugins install automatically on first launch")
    print("    4. Inside nvim, run ':Mason' to verify all tools installed")
    print("    5. Run ':checkhealth' to verify everything is working")
    print()
    print("  Keymaps cheat sheet:")
    print("    <Space>sf  — Search files       <Space>sg  — Search by grep")
    print("    <Space>f   — Format buffer       \\         — Toggle file tree")
    print("    <Space>mp  — Markdown preview    <Space>th — Toggle inlay hints")
    print("    <Space>bn  — Next buffer         <Space>bp — Previous buffer")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap a professional Neovim development environment"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be installed without making changes",
    )
    parser.add_argument(
        "--skip-tools",
        action="store_true",
        help="Only install Neovim config, skip tool installations",
    )
    args = parser.parse_args()

    print("╔══════════════════════════════════════════╗")
    print("║  Neovim Dev Environment Bootstrap        ║")
    print("║  github.com/iamHrithikRaj/dotfiles       ║")
    print("╚══════════════════════════════════════════╝")

    plat = detect_platform()
    print(f"\n  Platform: {plat}")
    print(f"  Config:   {get_nvim_config_path()}")
    print(f"  Languages: {', '.join(l['label'] for l in LANGUAGES.values())}")

    if args.dry_run:
        print("\n  🔍 DRY RUN MODE — no changes will be made\n")

    if not args.skip_tools:
        install_core_tools(plat, args.dry_run)
        install_language_prerequisites(plat, args.dry_run)
        install_system_tools(args.dry_run)

    install_nvim_config(args.dry_run)
    setup_vim_alias(plat, args.dry_run)
    print_summary(plat)


if __name__ == "__main__":
    main()
