-- Markdown Preview — live preview in your browser with Mermaid diagram support
-- Opens a local dev server and renders Markdown in real-time as you type.
--
-- USAGE:
--   <leader>mp  — Toggle markdown preview in browser
--   :MarkdownPreview / :MarkdownPreviewStop
--
-- FEATURES:
--   - Live refresh as you edit
--   - Mermaid diagram rendering (flowcharts, sequence diagrams, etc.)
--   - KaTeX math support
--   - Synchronized scrolling between editor and preview

return {
  'iamcco/markdown-preview.nvim',
  ft = { 'markdown' },
  build = 'cd app && npm install',
  keys = {
    { '<leader>mp', '<cmd>MarkdownPreviewToggle<CR>', desc = '[M]arkdown [P]review toggle' },
  },
  init = function()
    -- Enable Mermaid diagram rendering in preview
    vim.g.mkdp_filetypes = { 'markdown' }
    -- Auto-close preview when switching away from markdown buffer
    vim.g.mkdp_auto_close = 1
  end,
}
