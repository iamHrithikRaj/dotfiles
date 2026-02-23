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
from datetime import datetime
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
            "windows": "winget install Microsoft.DotNet.SDK.9 --silent --accept-source-agreements --accept-package-agreements",
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
            "windows": "winget install Rustlang.Rustup --silent --accept-source-agreements --accept-package-agreements",
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
        "VC++ Redist": "winget install Microsoft.VCRedist.2015+.x64 --silent --accept-source-agreements --accept-package-agreements",
        "Neovim": "winget install Neovim.Neovim --silent --accept-source-agreements --accept-package-agreements",
        "Git": "winget install Git.Git --silent --accept-source-agreements --accept-package-agreements",
        "ripgrep": "winget install BurntSushi.ripgrep.MSVC --silent --accept-source-agreements --accept-package-agreements",
        "fd": "winget install sharkdp.fd --silent --accept-source-agreements --accept-package-agreements",
        "CMake": "winget install Kitware.CMake --silent --accept-source-agreements --accept-package-agreements",
        "Node.js": "winget install OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements",
        "Nerd Font": "winget install DEVCOM.JetBrainsMonoNerdFont --silent --accept-source-agreements --accept-package-agreements",
        "Oh My Posh": "winget install JanDeDobbeleer.OhMyPosh --source winget --silent --accept-source-agreements --accept-package-agreements",
    },
    "linux_apt": {
        "Neovim + tools": "sudo apt update && sudo apt install -y neovim git ripgrep fd-find unzip gcc make cmake curl",
        "Node.js": "curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt install -y nodejs",
        "Oh My Posh": "brew install jandedobbeleer/oh-my-posh/oh-my-posh",
    },
    "linux_dnf": {
        "Neovim + tools": "sudo dnf install -y neovim git ripgrep fd-find unzip gcc make cmake curl",
        "Node.js": "sudo dnf install -y nodejs",
        "Oh My Posh": "brew install jandedobbeleer/oh-my-posh/oh-my-posh",
    },
    "linux_pacman": {
        "Neovim + tools": "sudo pacman -S --noconfirm --needed neovim git ripgrep fd unzip gcc make cmake curl",
        "Node.js": "sudo pacman -S --noconfirm --needed nodejs npm",
        "Oh My Posh": "brew install jandedobbeleer/oh-my-posh/oh-my-posh",
    },
    "macos": {
        "Neovim + tools": "brew install neovim git ripgrep fd cmake",
        "Node.js": "brew install node",
        "Nerd Font": "brew install --cask font-jetbrains-mono-nerd-font",
        "Oh My Posh": "brew install jandedobbeleer/oh-my-posh/oh-my-posh",
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
    """Run a shell command with a description. Returns True on success.

    Always continues execution — failures are logged and collected for a
    summary at the end, but never stop the bootstrap process.
    """
    print(f"  → {desc}")
    if dry_run:
        print(f"    [DRY RUN] {cmd}")
        return True
    try:
        # Use shell=True for cross-platform compatibility (handles pipes, &&, etc.)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            # Combine stdout and stderr for full error context
            output = (result.stderr.strip() + "\n" + result.stdout.strip()).strip()
            # Don't fail hard — some tools may already be installed/configured
            already_ok_patterns = [
                "already installed",
                "no applicable",
                "already exists",
                "no update available",
                "is already configured",
            ]
            if any(p in output.lower() for p in already_ok_patterns):
                print(f"    ✓ Already installed/configured")
                return True
            # Log the full error so the developer can diagnose
            print(f"    ⚠  FAILED (exit code {result.returncode})")
            print(f"    ┌─ Command: {cmd}")
            if output:
                # Indent each line of output for readability
                for line in output.splitlines()[:15]:  # Cap at 15 lines
                    print(f"    │ {line}")
            print(f"    └─ (continuing with remaining steps...)")
            FAILURES.append({"step": desc, "cmd": cmd, "output": output[:500], "code": result.returncode})
            return False
        print(f"    ✓ Done")
        return True
    except Exception as e:
        print(f"    ✗ Error: {e}")
        FAILURES.append({"step": desc, "cmd": cmd, "output": str(e), "code": -1})
        return False


# Global list to collect all failures for the end-of-run summary
FAILURES: list[dict] = []


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

    # On Windows, check if Python is the Microsoft Store version (sandboxed).
    # The Store version breaks Mason's pip installs because it can't write to
    # its own package directories. If detected, install the python.org version.
    if plat == "windows":
        ensure_real_python(dry_run)

    # Install Nerd Font on Linux (not available via apt/dnf/pacman)
    if plat.startswith("linux"):
        install_nerd_font_linux(dry_run)

    # Refresh PATH so newly installed tools (Node.js, Python, etc.) are
    # available to subsequent steps in this same terminal session.
    # Without this, Mason will fail to install npm/pip packages on first run.
    if not dry_run:
        refresh_path(plat)


def ensure_real_python(dry_run: bool):
    """Detect Microsoft Store Python and install the full python.org version if needed.

    The Store version lives in WindowsApps and runs in a sandbox — pip install
    fails for Mason packages (ruff, cmake-language-server, clang-format, etc.).
    """
    python_path = shutil.which("python")

    if python_path is None:
        # No Python at all — install it
        print("  → Python not found — installing python.org version")
        run(
            "winget install Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements",
            "Installing Python (python.org)",
            dry_run,
        )
        return

    # Check if the Python in PATH is the Microsoft Store version
    python_path_lower = python_path.lower()
    if "windowsapps" in python_path_lower or "pythonsoftwarefoundation" in python_path_lower:
        print(f"  → ⚠  Detected Microsoft Store Python at: {python_path}")
        print(f"       The Store version is sandboxed and breaks Mason's pip installs.")
        print(f"       Installing the full python.org version alongside it...")
        run(
            "winget install Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements",
            "Installing Python (python.org — replaces Store version in PATH)",
            dry_run,
        )
        if not dry_run:
            print("    ℹ  After restarting your terminal, the python.org version will take priority.")
            print("    ℹ  You can disable the Store version in:")
            print("       Settings → Apps → Advanced app settings → App execution aliases")
    else:
        print(f"  → Python: OK ({python_path})")


def refresh_path(plat: str):
    """Reload PATH from the registry/environment so newly installed tools are found."""
    if plat == "windows":
        # On Windows, winget installs update the registry PATH but not the
        # current process. Re-read Machine + User PATH from the registry.
        result = subprocess.run(
            'powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable(\'Path\',\'Machine\') + \';\' + [System.Environment]::GetEnvironmentVariable(\'Path\',\'User\')"',
            shell=True, capture_output=True, text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            os.environ["PATH"] = result.stdout.strip()
            print("  → PATH refreshed (new tools now available in this session)")
    else:
        # On Linux/macOS, tools installed via apt/brew/pacman are already in
        # standard PATH locations. Source common profile files for extras.
        for rc in ["~/.cargo/env", "~/.bashrc", "~/.zshrc"]:
            expanded = os.path.expanduser(rc)
            if os.path.isfile(expanded):
                # Can't source bash files from Python, but cargo/env just adds to PATH
                if "cargo" in rc:
                    cargo_bin = os.path.expanduser("~/.cargo/bin")
                    if cargo_bin not in os.environ.get("PATH", ""):
                        os.environ["PATH"] = cargo_bin + os.pathsep + os.environ.get("PATH", "")


def install_nerd_font_linux(dry_run: bool):
    """Download and install JetBrainsMono Nerd Font on Linux."""
    font_dir = Path.home() / ".local" / "share" / "fonts"
    if (font_dir / "JetBrainsMonoNerdFont-Regular.ttf").exists():
        print("  → Installing JetBrainsMono Nerd Font")
        print("    ✓ Already installed/configured")
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
    # This is idempotent — if the source already exists, dotnet returns an error
    # which we handle gracefully by checking first.
    if "csharp" in LANGUAGES:
        if is_installed("dotnet") or dry_run:
            # Check if nuget.org source already exists before adding
            check = subprocess.run(
                "dotnet nuget list source",
                shell=True, capture_output=True, text=True,
            )
            if "nuget.org" in check.stdout.lower():
                print("  → Configuring NuGet source")
                print("    ✓ Already installed/configured")
            else:
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
                print(f"  → Installing {binary} ({lang['label']})")
                print(f"    ✓ Already installed/configured")
            else:
                run(cmd, f"Installing {binary} ({lang['label']})", dry_run)


def install_nvim_config(dry_run: bool):
    """Clone kickstart.nvim and overlay our customized config.

    Behavior:
    - Fresh install:  Clones kickstart.nvim → overlays our files on top
    - Re-run (update): Backs up existing config (timestamped) → overlays new files
    - The backup is timestamped so multiple re-runs never overwrite previous backups
    """
    print("\n╔══════════════════════════════════════════╗")
    print("║  Installing Neovim Config                ║")
    print("╚══════════════════════════════════════════╝")

    config_path = get_nvim_config_path()
    repo_nvim_dir = Path(__file__).parent / "nvim"

    if config_path.exists():
        # Timestamped backup so re-runs don't overwrite previous backups
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_path = Path(str(config_path) + f".bak.{timestamp}")
        print(f"  → Existing config found at {config_path}")
        print(f"    Backing up to {bak_path.name}")
        if not dry_run:
            shutil.copytree(config_path, bak_path)

    # Clone kickstart.nvim as the base (only on fresh install)
    if not (config_path / ".git").exists():
        run(
            f'git clone https://github.com/nvim-lua/kickstart.nvim.git "{config_path}"',
            "Cloning kickstart.nvim (fresh install)",
            dry_run,
        )
    else:
        print("  → kickstart.nvim base already present — updating config files")

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


def get_shell_profile(plat: str):
    """Return the path to the user's shell profile file."""
    if plat == "windows":
        return (
            Path(os.environ.get("USERPROFILE", ""))
            / "Documents"
            / "PowerShell"
            / "Microsoft.PowerShell_profile.ps1"
        )
    shell = os.environ.get("SHELL", "/bin/bash")
    if "zsh" in shell:
        return Path.home() / ".zshrc"
    return Path.home() / ".bashrc"


def ensure_shell_profile(plat: str, dry_run: bool):
    """Ensure the shell profile file exists (create it if missing)."""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Ensuring shell profile exists           ║")
    print("╚══════════════════════════════════════════╝")

    profile = get_shell_profile(plat)

    if profile.exists():
        print(f"  → {profile} already exists")
        return

    print(f"  → Creating {profile}")
    if not dry_run:
        profile.parent.mkdir(parents=True, exist_ok=True)
        profile.touch()
    print("    ✓ Done")


def setup_vim_alias(plat: str, dry_run: bool):
    """Set up 'vim' command to open nvim."""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Setting up vim → nvim alias             ║")
    print("╚══════════════════════════════════════════╝")

    if plat == "windows":
        profile_path = get_shell_profile(plat)
        alias_line = "Set-Alias -Name vim -Value nvim"

        if profile_path.exists() and alias_line in profile_path.read_text():
            print("  → Alias already configured in PowerShell profile")
            return

        print(f"  → Adding alias to {profile_path}")
        if not dry_run:
            with open(profile_path, "a") as f:
                f.write(f"\n# Neovim alias — use 'vim' to open nvim\n{alias_line}\n")
        print("    ✓ Done")

    else:
        rc_file = get_shell_profile(plat)
        alias_line = "alias vim='nvim'"

        if rc_file.exists() and alias_line in rc_file.read_text():
            print(f"  → Alias already configured in {rc_file.name}")
            return

        print(f"  → Adding alias to {rc_file}")
        if not dry_run:
            with open(rc_file, "a") as f:
                f.write(f"\n# Neovim alias — use 'vim' to open nvim\n{alias_line}\n")
        print("    ✓ Done")


def setup_powerfetch(plat: str, dry_run: bool):
    """Install powerfetch script and add a shell function to invoke it.

    Credits: powerfetch by jantari — https://github.com/jantari/powerfetch
    """
    print("\n╔══════════════════════════════════════════╗")
    print("║  Setting up powerfetch                   ║")
    print("╚══════════════════════════════════════════╝")

    repo_script = Path(__file__).parent / "powerfetch" / "powerfetch.ps1"

    if plat == "windows":
        install_dir = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "powerfetch"
        dest_script = install_dir / "powerfetch.ps1"

        # Copy the script
        print(f"  → Installing powerfetch to {install_dir}")
        if not dry_run:
            install_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo_script, dest_script)
        print("    ✓ Script installed")

        # Add function to PowerShell profile
        profile_path = get_shell_profile(plat)
        func_marker = "function powerfetch"

        if profile_path.exists() and func_marker in profile_path.read_text():
            print("  → powerfetch function already in PowerShell profile")
            return

        func_block = (
            '\n# powerfetch — system info display (https://github.com/jantari/powerfetch)\n'
            'function powerfetch {\n'
            f'  & "{dest_script}" @args\n'
            '}\n'
        )
        print(f"  → Adding powerfetch function to {profile_path}")
        if not dry_run:
            with open(profile_path, "a") as f:
                f.write(func_block)
        print("    ✓ Done")

    else:
        # On Linux/macOS, install to ~/.local/bin
        install_dir = Path.home() / ".local" / "bin"
        dest_script = install_dir / "powerfetch.ps1"

        print(f"  → Installing powerfetch to {install_dir}")
        if not dry_run:
            install_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo_script, dest_script)
        print("    ✓ Script installed")

        rc_file = get_shell_profile(plat)
        func_marker = "function powerfetch"
        alias_line = f"function powerfetch {{ pwsh -NoProfile -File '{dest_script}' \"$@\"; }}"

        if rc_file.exists() and func_marker in rc_file.read_text():
            print(f"  → powerfetch function already in {rc_file.name}")
            return

        print(f"  → Adding powerfetch function to {rc_file}")
        if not dry_run:
            with open(rc_file, "a") as f:
                f.write(
                    f"\n# powerfetch — system info display (https://github.com/jantari/powerfetch)\n"
                    f"{alias_line}\n"
                )
        print("    ✓ Done")


def setup_oh_my_posh(plat: str, dry_run: bool):
    """Add Oh My Posh init line to the shell profile."""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Setting up Oh My Posh prompt            ║")
    print("╚══════════════════════════════════════════╝")

    profile = get_shell_profile(plat)

    if plat == "windows":
        init_line = "oh-my-posh init pwsh | Invoke-Expression"
    else:
        shell = os.environ.get("SHELL", "/bin/bash")
        shell_name = "zsh" if "zsh" in shell else "bash"
        init_line = f'eval "$(oh-my-posh init {shell_name})"'

    if profile.exists() and init_line in profile.read_text():
        print("  → Oh My Posh already configured in profile")
        return

    print(f"  → Adding Oh My Posh init to {profile}")
    if not dry_run:
        with open(profile, "a") as f:
            f.write(f"\n# Oh My Posh prompt\n{init_line}\n")
    print("    ✓ Done")


# ═══════════════════════════════════════════════════════════════════════════════
# POST-INSTALL SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════


def print_summary(plat: str):
    """Print post-install instructions and any failures."""

    # Print failure summary first if there were any
    if FAILURES:
        print("\n╔══════════════════════════════════════════╗")
        print(f"║  ⚠  {len(FAILURES)} step(s) failed                     ║")
        print("╚══════════════════════════════════════════╝")
        for i, f in enumerate(FAILURES, 1):
            print(f"\n  [{i}] {f['step']}  (exit code {f['code']})")
            print(f"      Command: {f['cmd']}")
            if f["output"]:
                for line in f["output"].splitlines()[:5]:
                    print(f"      │ {line}")
        print()
        print("  These failures are non-fatal — the rest of the setup completed.")
        print("  You can re-run the script to retry, or install these manually.")

    if FAILURES:
        print("\n╔══════════════════════════════════════════╗")
        print("║  ⚠  Setup Completed With Warnings        ║")
        print("╚══════════════════════════════════════════╝")
    else:
        print("\n╔══════════════════════════════════════════╗")
        print("║  ✅  Setup Complete!                      ║")
        print("╚══════════════════════════════════════════╝")
    print()
    print("  Installed languages:")
    for lang in LANGUAGES.values():
        print(f"    • {lang['label']}")
    print()
    print("  Shell profile configured:")
    print(f"    • vim → nvim alias")
    print(f"    • Oh My Posh prompt init")
    print(f"    • powerfetch function")
    print()
    print("  Next steps:")
    print("    1. Set your terminal font to 'JetBrainsMono Nerd Font'")
    if plat == "windows":
        print("       Windows Terminal → Settings → Appearance → Font face")
    elif plat == "macos":
        print("       iTerm2: Preferences → Profiles → Text → Font")
        print("       Terminal.app: Preferences → Profiles → Font → Change")
        print("       Alacritty: Edit ~/.config/alacritty/alacritty.toml → font.normal.family")
    else:
        print("       GNOME Terminal: Preferences → Profiles → Custom font")
        print("       Konsole: Settings → Edit Current Profile → Appearance → Font")
        print("       Alacritty: Edit ~/.config/alacritty/alacritty.toml → font.normal.family")
    print("    2. Close and reopen your terminal (not just a new tab)")
    print("    3. Run 'nvim' — plugins install automatically on first launch")
    print("    4. Inside nvim, run ':Mason' to verify all tools installed")
    print("    5. Run ':checkhealth' to verify everything is working")
    print()


def check_privileges(plat: str, skip_tools: bool):
    """Warn if running without required privileges for tool installation."""
    if skip_tools:
        return  # No tool installs — no privileges needed

    if plat == "windows":
        # winget requires admin to install system-wide packages
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            is_admin = False
        if not is_admin:
            print("\n  ⚠  WARNING: Not running as Administrator!")
            print("     winget needs admin to install tools (Neovim, Node.js, etc.)")
            print("     Right-click your terminal → 'Run as administrator' and try again.")
            print("     Or use --skip-tools to only install the Neovim config.\n")
            response = input("  Continue anyway? [y/N] ").strip().lower()
            if response != "y":
                sys.exit(0)
    # Linux: sudo is embedded in the commands — it will prompt for password
    # macOS: brew runs without sudo


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

    # Check for admin/sudo before attempting tool installs
    if not args.dry_run:
        check_privileges(plat, args.skip_tools)

    if not args.skip_tools:
        install_core_tools(plat, args.dry_run)
        install_language_prerequisites(plat, args.dry_run)
        install_system_tools(args.dry_run)

    install_nvim_config(args.dry_run)
    ensure_shell_profile(plat, args.dry_run)
    setup_vim_alias(plat, args.dry_run)
    setup_powerfetch(plat, args.dry_run)
    setup_oh_my_posh(plat, args.dry_run)
    print_summary(plat)

    # Exit with error code if any steps failed (useful for CI/scripting)
    if FAILURES:
        sys.exit(1)


if __name__ == "__main__":
    main()
