-- Rustaceanvim — Enhanced Rust development experience
-- Successor to rust-tools.nvim. Manages rust-analyzer automatically.
-- DO NOT add rust_analyzer to the LSP servers table in init.lua —
-- rustaceanvim handles all rust-analyzer lifecycle and configuration.
--
-- REQUIREMENTS:
--   - Rust toolchain installed via rustup (https://rustup.rs)
--   - rust-analyzer is included with rustup since Rust 1.64+
--
-- FEATURES:
--   - Automatic rust-analyzer management
--   - Enhanced hover actions (run/debug runnables)
--   - Crate graph visualization
--   - Expand macros, open Cargo.toml, join lines, etc.

return {
  'mrcjkb/rustaceanvim',
  version = '^5',
  lazy = false, -- Plugin is already lazy — loads only for Rust files
  init = function()
    -- Configure rustaceanvim via global variable (required by the plugin)
    vim.g.rustaceanvim = {
      -- LSP (rust-analyzer) settings
      server = {
        default_settings = {
          ['rust-analyzer'] = {
            -- Enable all features for cargo (needed in workspaces with feature flags)
            cargo = {
              allFeatures = true,
              loadOutDirsFromCheck = true,
            },
            -- Use clippy for on-save diagnostics (stricter than default check)
            checkOnSave = {
              command = 'clippy',
            },
            -- Proc macro support (e.g., derive macros, serde, tokio)
            procMacro = {
              enable = true,
            },
            -- Inlay hints configuration
            inlayHints = {
              lifetimeElisionHints = {
                enable = 'always', -- Show lifetime elision hints
              },
            },
          },
        },
      },
    }
  end,
}
