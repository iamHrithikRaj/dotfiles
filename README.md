# 🚀 Dotfiles — Professional Neovim Dev Environment

**One command. Any machine. Full dev setup.**

A cross-platform bootstrap that installs Neovim with a professional configuration for **C, C++, C#, Rust, Python, Markdown**, and more — complete with LSP, auto-formatting, linting, autocompletion, and a curated plugin set. Built on [kickstart.nvim](https://github.com/nvim-lua/kickstart.nvim).

```bash
git clone https://github.com/iamHrithikRaj/dotfiles.git
cd dotfiles
python bootstrap.py
```

That's it. The script handles **everything** — from installing Neovim and language toolchains to configuring your shell alias and downloading fonts.

---

## ✨ What You Get

### Languages — Full LSP, Formatting & Linting Out of the Box

| Language | LSP | Formatter | Linter | Treesitter |
|---|---|---|---|---|
| C / C++ | clangd | clang-format | clang-tidy (via clangd) | ✅ |
| C# | Roslyn (via roslyn.nvim) | csharpier | Roslyn | ✅ |
| Rust | rust-analyzer (via rustaceanvim) | rustfmt | clippy | ✅ |
| Python | pyright | ruff / black | ruff | ✅ |
| Markdown | marksman | prettier | markdownlint | ✅ (+mermaid) |
| JSON | jsonls | prettier | — | ✅ |
| XML | lemminx | xmlformatter | — | ✅ |
| YAML | — | prettier | — | ✅ |
| TOML | taplo | taplo | — | ✅ |
| CMake | cmake-ls | — | — | ✅ |
| Lua | lua_ls | stylua | — | ✅ |

### Plugins

| Plugin | What it does |
|---|---|
| [telescope.nvim](https://github.com/nvim-telescope/telescope.nvim) | Fuzzy finder — files, grep, LSP symbols, keymaps, everything |
| [neo-tree.nvim](https://github.com/nvim-neo-tree/neo-tree.nvim) | File explorer sidebar |
| [gitsigns.nvim](https://github.com/lewis6991/gitsigns.nvim) | Git signs in gutter + stage/reset hunks |
| [blink.cmp](https://github.com/saghen/blink.cmp) | Fast autocompletion with LSP + snippets |
| [conform.nvim](https://github.com/stevearc/conform.nvim) | Auto-format on save |
| [nvim-lint](https://github.com/mfussenegger/nvim-lint) | Async linting |
| [roslyn.nvim](https://github.com/seblj/roslyn.nvim) | C# LSP — same Roslyn compiler as Visual Studio |
| [rustaceanvim](https://github.com/mrcjkb/rustaceanvim) | Enhanced Rust — hover actions, clippy, crate graph |
| [markdown-preview.nvim](https://github.com/iamcco/markdown-preview.nvim) | Live browser preview with Mermaid diagram support |
| [which-key.nvim](https://github.com/folke/which-key.nvim) | Discover keybinds as you type |
| [mini.nvim](https://github.com/nvim-mini/mini.nvim) | Statusline, surround, text objects |
| [todo-comments.nvim](https://github.com/folke/todo-comments.nvim) | Highlight TODO/FIXME/NOTE in comments |
| [friendly-snippets](https://github.com/rafamadriz/friendly-snippets) | Premade snippets for all languages |

### What the Bootstrap Script Installs

The script detects your OS and installs everything you need:

| Tool | Windows | Linux | macOS |
|---|---|---|---|
| Neovim | `winget` | `apt`/`dnf`/`pacman` | `brew` |
| Node.js | `winget` | `nodesource` / pkg mgr | `brew` |
| .NET SDK | `winget` | `apt`/`dnf` | `brew` |
| Rust (rustup) | `winget` | `rustup.rs` | `rustup.rs` |
| ripgrep, fd, cmake | `winget` | pkg mgr | `brew` |
| JetBrainsMono Nerd Font | `winget` | auto-download | `brew cask` |
| Python (if missing/broken) | `winget` | — | — |
| csharpier (C# formatter) | `dotnet tool` | `dotnet tool` | `dotnet tool` |
| `vim` → `nvim` alias | PowerShell `$PROFILE` | `.bashrc`/`.zshrc` | `.bashrc`/`.zshrc` |

---

## 📦 Quick Start

### 1. Prerequisites

**Python 3** must be installed first (it's the only manual prerequisite).

| OS | Command |
|---|---|
| Windows | `winget install Python.Python.3.12` |
| Linux | `sudo apt install python3` (usually pre-installed) |
| macOS | `brew install python` (usually pre-installed) |

> ⚠ **Windows users**: Use the **python.org** version, not the Microsoft Store version. The Store version is sandboxed and breaks Mason package installs. The script detects this automatically and fixes it.

### 2. Install

```bash
git clone https://github.com/iamHrithikRaj/dotfiles.git
cd dotfiles
python bootstrap.py
```

> **Windows**: Run as **Administrator** (right-click terminal → Run as administrator)  
> **Linux**: Will prompt for `sudo` password  
> **macOS**: No elevated access needed

### 3. Post-Install

1. **Set your terminal font** to `JetBrainsMono Nerd Font`
   - Windows Terminal: Settings → Appearance → Font face
   - iTerm2: Preferences → Profiles → Text → Font
   - GNOME Terminal: Preferences → Profiles → Custom font
2. **Close and reopen your terminal** (not just a new tab)
3. **Run `nvim`** — plugins and tools install automatically on first launch
4. Run `:checkhealth` inside nvim to verify everything is working

---

## ⌨️ Key Keymaps

| Keymap | Action |
|---|---|
| `<Space>sf` | Search files |
| `<Space>sg` | Search by grep |
| `<Space>f` | Format buffer |
| `\` | Toggle file tree (neo-tree) |
| `<Space>mp` | Markdown preview toggle |
| `<Space>th` | Toggle inlay hints |
| `<Space>bn` / `<Space>bp` | Next / previous buffer |
| `<Space>bd` | Delete buffer |
| `<Space>sh` | Search help |
| `<Space>sk` | Search keymaps |
| `grd` | Go to definition |
| `grr` | Go to references |
| `grn` | Rename symbol |
| `gra` | Code action |
| `<Space>ch` | Switch C/C++ source/header |

> 💡 Press `<Space>` and wait — [which-key](https://github.com/folke/which-key.nvim) will show all available keybinds.

---

## 🔧 Adding / Removing Languages

The bootstrap script uses a **data-driven language registry**. Adding or removing a language means editing ONE dict in `bootstrap.py` — no other code changes needed.

### Example: Adding Go

```python
# In bootstrap.py → LANGUAGES dict:
"go": {
    "label": "Go",
    "treesitter": ["go", "gomod", "gosum"],
    "lsp": {"gopls": {"_config": "{}"}},
    "mason": ["gopls", "goimports"],
    "formatters": {"go": ["goimports"]},
    "linters": {"go": ["golangcilint"]},
    "prerequisites": {
        "windows": "winget install GoLang.Go",
        "linux_apt": "sudo apt install -y golang",
        "macos": "brew install go",
    },
},
```

Then re-run `python bootstrap.py`.

### Example: Removing XML

Delete or comment out the `"xml"` entry in `LANGUAGES`. Done.

---

## 🛠 Bootstrap Options

```bash
python bootstrap.py              # Full install — tools + config
python bootstrap.py --dry-run    # Preview what would happen (no changes made)
python bootstrap.py --skip-tools # Only install/update nvim config, skip tool installs
```

### Re-running the Script

The script is **idempotent** — safe to run multiple times:
- Already-installed tools are skipped
- Existing nvim config is backed up with a timestamp (`nvim.bak.20260209_053848`)
- Config files are overlaid on top of the existing kickstart base

---

## 📁 Repo Structure

```
dotfiles/
├── bootstrap.py                    # Cross-platform bootstrap script
├── README.md
└── nvim/                           # Neovim config (copied to ~/.config/nvim)
    ├── init.lua                    # Main config — options, keymaps, plugins
    ├── lazy-lock.json              # Pinned plugin versions
    └── lua/
        ├── custom/plugins/
        │   ├── roslyn.lua          # C# LSP (Roslyn compiler)
        │   ├── rust.lua            # Rust (rustaceanvim)
        │   └── markdown.lua        # Markdown preview + Mermaid
        └── kickstart/plugins/
            ├── autopairs.lua       # Auto-close brackets/quotes
            ├── gitsigns.lua        # Git keymaps
            ├── indent_line.lua     # Indentation guides
            ├── lint.lua            # Linting config
            └── neo-tree.lua        # File explorer
```

## License

MIT
