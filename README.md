# Neovim Dotfiles

Professional Neovim development environment for C, C++, C#, Rust, Python, Markdown, and more.  
Built on [kickstart.nvim](https://github.com/nvim-lua/kickstart.nvim) with language-specific enhancements.

## Quick Start

### Prerequisites

**Python 3** must be installed first (it's the only manual prerequisite):

| OS | Command |
|---|---|
| Windows | `winget install Python.Python.3.12` |
| Linux (apt) | `sudo apt install python3` (usually pre-installed) |
| macOS | `brew install python` (usually pre-installed) |

### Install Everything

```bash
git clone https://github.com/iamHrithikRaj/dotfiles.git
cd dotfiles
python bootstrap.py
```

> **Windows**: Run your terminal as **Administrator** (right-click → Run as administrator). `winget` needs admin to install system-wide packages. The script will warn you if you forget.
>
> **Linux**: The script uses `sudo` for package installs — it will prompt for your password.
>
> **macOS**: No elevated access needed (`brew` runs as your user).

That's it! The bootstrap script handles everything:
- Installs Neovim, Node.js, .NET SDK, Rust, ripgrep, fd, cmake
- Installs JetBrainsMono Nerd Font
- Clones kickstart.nvim and overlays our customized config
- Sets up `vim` → `nvim` alias
- Configures NuGet and installs csharpier

### Post-Install

1. **Set your terminal font** to `JetBrainsMono Nerd Font`
   - Windows Terminal: Settings → Profiles → Defaults → Appearance → Font face
2. **Restart your terminal** (to pick up PATH changes)
3. **Run `nvim`** — plugins install automatically on first launch
4. Inside nvim, run `:Mason` to verify all tools installed
5. Run `:checkhealth` to verify everything is working

## What's Included

### Languages & Tooling

| Language | LSP | Formatter | Linter | Treesitter |
|---|---|---|---|---|
| C / C++ | clangd | clang-format | clang-tidy (via clangd) | ✅ |
| C# | Roslyn (via roslyn.nvim) | csharpier | Roslyn | ✅ |
| Rust | rust-analyzer (via rustaceanvim) | rustfmt | clippy | ✅ |
| Python | pyright | ruff / black | ruff | ✅ |
| Markdown | marksman | prettier | markdownlint | ✅ (+ mermaid) |
| JSON | jsonls | prettier | — | ✅ |
| XML | lemminx | xmlformatter | — | ✅ |
| YAML | — | prettier | — | ✅ |
| TOML | taplo | taplo | — | ✅ |
| CMake | cmake-ls | — | — | ✅ |
| Lua | lua_ls | stylua | — | ✅ |

### Plugins

- **[telescope.nvim](https://github.com/nvim-telescope/telescope.nvim)** — Fuzzy finder for files, grep, LSP symbols
- **[neo-tree.nvim](https://github.com/nvim-neo-tree/neo-tree.nvim)** — File explorer sidebar
- **[gitsigns.nvim](https://github.com/lewis6991/gitsigns.nvim)** — Git status in gutter + hunk actions
- **[blink.cmp](https://github.com/saghen/blink.cmp)** — Autocompletion with LSP + snippets
- **[conform.nvim](https://github.com/stevearc/conform.nvim)** — Auto-formatting on save
- **[nvim-lint](https://github.com/mfussenegger/nvim-lint)** — Asynchronous linting
- **[roslyn.nvim](https://github.com/seblj/roslyn.nvim)** — C# LSP using Microsoft's Roslyn compiler
- **[rustaceanvim](https://github.com/mrcjkb/rustaceanvim)** — Enhanced Rust support
- **[markdown-preview.nvim](https://github.com/iamcco/markdown-preview.nvim)** — Live preview with Mermaid diagrams
- **[which-key.nvim](https://github.com/folke/which-key.nvim)** — Shows pending keybinds
- **[mini.nvim](https://github.com/nvim-mini/mini.nvim)** — Statusline, surround, text objects
- **[todo-comments.nvim](https://github.com/folke/todo-comments.nvim)** — Highlight TODO/FIXME/NOTE comments

### Key Keymaps

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

## Adding a New Language

Edit the `LANGUAGES` dict in `bootstrap.py`. Example — adding Go:

```python
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

Then re-run `python bootstrap.py`. No other code changes needed.

## Bootstrap Options

```bash
python bootstrap.py              # Full install
python bootstrap.py --dry-run    # Preview what would be installed
python bootstrap.py --skip-tools # Only install nvim config, skip tool installs
```

## License

MIT
